
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

    def train(self, arff_file_name, target_variable_name):
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

        n = len(self.variables) - 1
        self.target_likelihood = {k: n*log(v) for k, v in tgt_count.items()}

    def classify(self, attributes_values):
        classes_likelihood = {k: v for k, v in self.target_likelihood.items()}

        for i, val in enumerate(attributes_values):
            if i == self.target_index:
                continue
            ob_class = attributes_values[self.target_index]
            classes_likelihood[ob_class] += self.likelihoods[ob_class, i, val]

        return classes_likelihood


N = NaiveBayesClassifier('examples/classifiers/emotions-train.arff')
t = N.train('./examples/classifiers/emotions-train.arff', N.variables[0])
test_data = arff.load(open('examples/classifiers/emotions-test.arff'))['data']
