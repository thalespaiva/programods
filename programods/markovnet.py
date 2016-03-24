#!/usr/bin/python3

import itertools as it


class Variable:

    def __init__(self, name, type_, domain):
        self.name = name
        self.type = type_
        self.domain = domain

    def __str__(self):
        out = []

        out.append('[V] Name : %s\n' % self.name)
        out.append('    Type : %s\n' % self.type)
        out.append('    Dom  : %s' % self.domain)

        return "".join(out)

    def __repr__(self):
        return "Variable<" + self.name + ">"


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

            potentials[clique] = dict(zip(domains_prod, values))

        return variables, potentials


if __name__ == "__main__":
    pass
