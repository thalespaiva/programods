
import arff

from math import log

from programods.distribution import Variable


class NaiveBayesClassifier:

    def __init__(self, arff_file_name):
        arff_file = open(arff_file_name)
        arff_attributes = arff.load(arff_file)['attributes']
        arff_file.close()

        self.variables = [a[0] for a in arff_attributes]
        self.indexed_variables = {}
        for i, a in enumerate(arff_attributes):
            self.indexed_variables[a[0]] = (i, Variable(a[0], a[1]))

        self.target_variable = None
        self.target_index = None
        self.likelihoods = None
        self.target_likelihood = None

    def train(self, arff_file_name, target_variable_name, None):
        arff_file = open(arff_file_name)
        training_set = arff.load(arff_file)['data']
        arff_file.close()

        tgt_index, tgt_var = self.indexed_variables[target_variable_name]

        likelihoods = {}  # class_val, attribute_index, attribute_val: N
        tgt_count = {v: 0 for v in tgt_var.domain}

        for obs in training_set:
            for i, value in enumerate(obs):
                key = (obs[tgt_index], i, obs[i])
                if key not in likelihoods:
                    likelihoods[key] = 1
                else:
                    likelihoods[key] += 1
                tgt_count[obs[tgt_index]] += 1

        for keys in likelihoods:
            likelihoods[keys] = log(likelihoods[keys])

        self.target_variable = tgt_var
        self.target_index = tgt_index
        self.likelihoods = likelihoods

        n = 1 - (len(self.variables) - 1 - 1)
        self.target_likelihood = {k: n*log(v) for k, v in tgt_count.items()}

    def classify(self, attributes_values):
        classes_ll = {k: v for k, v in self.target_likelihood.items()}

        for i, val in enumerate(attributes_values):
            if i == self.target_index:
                continue

            for k in classes_ll:
                classes_ll[k] += self.likelihoods.get((k, i, val), 0)

        return max(classes_ll, key=lambda k: classes_ll[k])

    def test(self, arff_file_name):
        arff_file = open(arff_file_name)
        test_set = arff.load(arff_file)['data']
        arff_file.close()

        no_corrects = 0
        for test_unit in test_set:
            expected_class = self.classify(test_unit)
            if expected_class == test_unit[self.target_index]:
                no_corrects += 1

        print("P = ", no_corrects/len(test_set))


N = NaiveBayesClassifier('examples/classifiers/emotions-train.arff')
N.train('./examples/classifiers/emotions-train.arff', N.variables[0])

M = NaiveBayesClassifier('examples/classifiers/medical-train.arff')
M.train('./examples/classifiers/medical-train.arff', M.variables[0])
