
import arff

from math import log

from programods.distribution import Variable
from collections import defaultdict

from itertools import product

EPS = 0.0001


def get_arff_part(arff_file_name, part):
    arff_file = open(arff_file_name)
    arff_info = arff.load(arff_file)
    arff_file.close()

    return arff_info[part]


def increment_or_init(dict_, key):
    try:
        dict_[key] += 1
    except:
        dict_[key] = 1


class Classifier:

    def __init__(self, arff_file_name):
        arff_attributes = get_arff_part(arff_file_name, 'attributes')

        self.indexed_variables = {}
        self.variables = []
        for i, a in enumerate(arff_attributes):
            var = Variable(a[0], a[1])
            self.indexed_variables[a[0]] = (i, var)
            self.variables.append(var)

    def train(self, arff_file_name, target_variable_name):
        raise NotImplementedError("Subclasses should implement this!")

    def classify(self, attributes_values):
        raise NotImplementedError("Subclasses should implement this!")

    def test(self, arff_file_name):
        test_set = get_arff_part(arff_file_name, 'data')
        no_corrects = 0
        for test_unit in test_set:
            expected_class = self.classify(test_unit)
            if expected_class == test_unit[self.target_index]:
                no_corrects += 1

        print("P = ", no_corrects/len(test_set))


class NaiveBayesClassifier(Classifier):

    def __init__(self, arff_file_name):
        super().__init__(arff_file_name)

        self.target_variable = None
        self.target_index = None
        self.likelihoods = None
        self.target_likelihoods = None

    def get_likelihoods(self, training_set, tgt_name):
        tgt_index, tgt_var = self.indexed_variables[tgt_name]

        likelihoods = {}  # class_val, attribute_index, attribute_val: N
        tgt_likelihoods = {v: 0 for v in tgt_var.domain}

        for obs in training_set:
            for i, value in enumerate(obs):
                key = (obs[tgt_index], i, obs[i])
                if key not in likelihoods:
                    likelihoods[key] = 1
                else:
                    likelihoods[key] += 1
                tgt_likelihoods[obs[tgt_index]] += 1

        for keys in likelihoods:
            likelihoods[keys] = log(likelihoods[keys])

        n = 1 - (len(self.variables) - 1 - 1)
        for key in tgt_likelihoods:
            tgt_likelihoods[key] = n*log(tgt_likelihoods[key])

        return tgt_likelihoods, likelihoods

    def train(self, arff_file_name, target_variable_name):
        training_set = get_arff_part(arff_file_name, 'data')

        pair_of_lls = self.get_likelihoods(training_set, target_variable_name)
        self.target_likelihoods, self.likelihoods = pair_of_lls

        pair_of_var_infos = self.indexed_variables[target_variable_name]
        self.target_index, self.target_variable = pair_of_var_infos

    def classify(self, attributes_values):
        classes_ll = {k: v for k, v in self.target_likelihoods.items()}

        for i, val in enumerate(attributes_values):
            if i == self.target_index:
                continue

            for k in classes_ll:
                classes_ll[k] += self.likelihoods.get((k, i, val), 0)

        return max(classes_ll, key=lambda k: classes_ll[k])


class TreeAugmentedNaiveBayesClassifier(Classifier):

    def __init__(self, arff_file_name):
        super().__init__(arff_file_name)

        self.pairs_counters = None
        self.single_counters = None

    def set_counters_by_training(self, training_set, tgt_name):
        tgt_index, tgt_var = self.indexed_variables[tgt_name]

        pairs_counters = defaultdict(int)
        single_counters = defaultdict(int)

        n = len(training_set[0])
        for i in range(n):
            for obs in training_set:
                for j in range(i):
                    pairs_counters[(obs[tgt_index],
                                   (j, obs[j]), (i, obs[i]))] += 1
                single_counters[obs[tgt_index], (i, obs[i])] += 1

        self.pairs_counters = pairs_counters
        self.single_counters = single_counters
        self.target_var = tgt_var
        self.tgt_index = tgt_index
        self.number_of_observations = n

        self.classes_likelihood = {}
        for k in self.target_var.domain:
            key = (k, (tgt_index, k))
            self.classes_likelihood[k] = log(single_counters[key]/n)

    def get_edge_weight(self, i, j):
        i, j = min(i, j), max(i, j)

        i_var, j_var = self.variables[i], self.variables[j]

        weight = 0
        for c in self.target_var.domain:
            for i_val in i_var.domain:
                for j_val in j_var.domain:
                    pairs_key = (c, (i, i_val), (j, j_val))
                    pair_occurrs = self.pairs_counters.get(pairs_key, 0)

                    if pair_occurrs == 0:
                        continue

                    single_occurrs_i = self.single_counters.get(
                        (c, (i, i_val)), 0)
                    single_occurrs_j = self.single_counters.get(
                        (c, (j, j_val)), 0)

                    weight -= pair_occurrs * log(
                        pair_occurrs/(single_occurrs_i * single_occurrs_j))

        return weight

    def train(self, arff_file_name, target_variable_name):
        training_set = get_arff_part(arff_file_name, 'data')

        self.set_counters_by_training(training_set, target_variable_name)
        pair_of_var_infos = self.indexed_variables[target_variable_name]
        self.target_index, self.target_variable = pair_of_var_infos

        edges_weight = self.get_edges_weights()
        self.parents = self.get_parents_list_on_min_spanning_tree(edges_weight)

    def get_edges_weights(self):
        edges_weight = {}
        for i, _ in enumerate(self.variables):
            for j, _ in enumerate(self.variables[:i]):
                edges_weight[j, i] = self.get_edge_weight(i, j)

        return edges_weight

    def get_parents_list_on_min_spanning_tree(self, edges_weight):
        vertices = set(range(len(self.variables)))
        vertices.remove(self.target_index)
        n = len(vertices)

        parents = [None] * (n + 1)
        costs = {(0, next(iter(vertices)))}

        def get_cost(i, j):
            return edges_weight[min(i, j), max(i, j)]

        while costs:  # Prim's Algorithm
            c, v = min(costs, key=lambda q: q[1])
            costs.remove((c, v))
            vertices.remove(v)

            for u in vertices:
                if parents[u] is None:
                    costs.add((get_cost(v, u), u))
                    parents[u] = v

                elif get_cost(parents[u], u) > get_cost(v, u):
                    costs.remove((get_cost(parents[u], u), u))
                    costs.add((get_cost(v, u), u))
                    parents[u] = v

        return parents

    def classify(self, attributes_values):
        classes_ll = {k: i for k, i in self.classes_likelihood.items()}

        for i, val in enumerate(attributes_values):
            if i == self.target_index:
                continue

            for c in classes_ll:
                if self.parents[i] is None:
                    estim = self.single_counters[c, (i, attributes_values[i])]
                    estim /= self.single_counters[c, (self.tgt_index, c)]
                else:
                    p = self.parents[i]
                    pair_key = (c, (min(i, p), attributes_values[min(i, p)]),
                                   (max(i, p), attributes_values[max(i, p)]))
                    estim = self.pairs_counters[pair_key]

                    single_key = (c, (p, attributes_values[p]))
                    estim /= self.single_counters[single_key] + EPS

                classes_ll[c] += log(estim + EPS)

        return max(classes_ll, key=lambda k: classes_ll[k])


P = NaiveBayesClassifier('examples/classifiers/emotions-train.arff')
P.train('./examples/classifiers/emotions-train.arff', P.variables[0].name)
#
# Q = NaiveBayesClassifier('examples/classifiers/medical-train.arff')
# Q.train('./examples/classifiers/medical-train.arff', Q.variables[0])
#
# R = NaiveBayesClassifier('examples/classifiers/yeast-train.arff')
# R.train('./examples/classifiers/yeast-train.arff', R.variables[0])
#
# S = NaiveBayesClassifier('examples/classifiers/yelp-train.arff')
# S.train('./examples/classifiers/yelp-train.arff', S.variables[0])

T = TreeAugmentedNaiveBayesClassifier('examples/classifiers/yeast-train.arff')
T.train('./examples/classifiers/yeast-train.arff', T.variables[0].name)

# U = TreeAugmentedNaiveBayesClassifier('examples/classifiers/yelp-train.arff')
# U.train('./examples/classifiers/yelp-train.arff', U.variables[0].name)

# N = TreeAugmentedNaiveBayesClassifier('./examples/classifiers/small-train.arff')
# N.train('./examples/classifiers/small-train.arff', N.variables[0].name)

# M = TreeAugmentedNaiveBayesClassifier('examples/classifiers/medical-train.arff')
# M.train('./examples/classifiers/medical-train.arff', M.variables[0].name)
