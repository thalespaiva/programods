#!/usr/bin/python3

import itertools as it

from bayesnet import Variable
from bayesnet import Distribution


class UAI_Parser:

    def get_per_line_token_extractor(uai_file):

        def extract_token():
            line = uai_file.readline().strip()
            while not line:
                line = uai_file.readline().strip()
            return line.lower().split()

        return extract_token

    def parse_preamble(get_tokens_from_next_line):
        first_line = get_tokens_from_next_line()
        if not first_line.pop().startswith('markov'):
            return None

        n_vars = int(get_tokens_from_next_line().pop())
        vars_cards = map(int, get_tokens_from_next_line())
        name_zip_card = zip(map(str, range(n_vars)), vars_cards)

        variables = tuple(Variable(n, '_', range(c)) for n, c in name_zip_card)
        variables_dict = {var.name: var for var in variables}

        n_cliques = int(get_tokens_from_next_line().pop())
        cliques = []
        for i in range(n_cliques):
            clique_info = get_tokens_from_next_line()
            cliques.append(tuple(clique_info[1:]))

        return (variables_dict, cliques)

    def parse(uai_file_path):
        uai_file = open(uai_file_path)
        token_extractor = UAI_Parser.get_per_line_token_extractor(uai_file)

        variables, cliques = UAI_Parser.parse_preamble(token_extractor)

        potentials = {}  # { tuple_of_vars_names: { valuation: value } }
        for clique in cliques:
            token_extractor()  # to consume a useless len(values) line

            values = map(float, token_extractor())
            domains_prod = it.product(*[variables[n].domain for n in clique])

            potential = Distribution([variables[name] for name in clique], [])
            potential.set_values(dict(zip(domains_prod, values)))

            potentials[clique] = potential

        uai_file.close()

        return variables, potentials


class MarkovNet:

    def __init__(self, variables, potentials):
        self.variables = variables
        self.potentials = potentials

    def init_from_uai_file(uai_file_path):
        variables, potentials = UAI_Parser.parse(uai_file_path)

        return MarkovNet(variables, potentials)

    def get_partition_function(self):
        total = 0

        variables = self.variables.values()
        domains_product = it.product(*[v.domain for v in variables])
        var_names = [v.name for v in variables]

        for valuation in domains_product:
            var_valuation = dict(zip(var_names, valuation))
            prod = 1
            for potential in self.potentials.values():
                prod *= potential.evaluate(var_valuation)
            print(valuation, prod)
            total += prod

        return total


if __name__ == "__main__":
    pass
