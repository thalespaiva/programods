
import arff

from math import log

from programods.distribution import Variable


def get_arff_part(arff_file_name, part):
    arff_file = open(arff_file_name)
    arff_info = arff.load(arff_file)
    arff_file.close()

    return arff_info[part]

class NaiveBayesClassifier:

    def __init__(self, arff_file_name):
        arff_attributes = get_arff_part(arff_file_name, 'attributes')

        self.variables = [a[0] for a in arff_attributes]
        self.indexed_variables = {}
        for i, a in enumerate(arff_attributes):
            self.indexed_variables[a[0]] = (i, Variable(a[0], a[1]))

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

    def test(self, arff_file_name):
        test_set = get_arff_part(arff_file_name, 'data')
        no_corrects = 0
        for test_unit in test_set:
            expected_class = self.classify(test_unit)
            if expected_class == test_unit[self.target_index]:
                no_corrects += 1

        print("P = ", no_corrects/len(test_set))


class TreeAugmentedNaiveBayesClassifier:

    def __init__(self, ):
        pass


N = NaiveBayesClassifier('examples/classifiers/emotions-train.arff')
N.train('./examples/classifiers/emotions-train.arff', N.variables[0])

M = NaiveBayesClassifier('examples/classifiers/medical-train.arff')
M.train('./examples/classifiers/medical-train.arff', M.variables[0])
