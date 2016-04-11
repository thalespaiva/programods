
import itertools as it

from programods.distribution import Variable
from programods.distribution import Potential


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
        if not first_line.pop(0).startswith('markov'):
            return None

        n_vars = int(get_tokens_from_next_line().pop(0))
        vars_cards = map(int, get_tokens_from_next_line())
        name_zip_card = zip(map(str, range(n_vars)), vars_cards)

        variables = tuple(Variable(n, range(c)) for n, c in name_zip_card)
        variables_dict = {var.name: var for var in variables}

        n_cliques = int(get_tokens_from_next_line().pop(0))
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

            potential = Potential([variables[name] for name in clique])
            potential.set_values(dict(zip(domains_prod, values)))

            potentials[clique] = potential

        uai_file.close()

        return variables, potentials

    def parse_evidence_file(evidence_file_path):
        evid_file = open(evidence_file_path)
        token_extractor = UAI_Parser.get_per_line_token_extractor(evid_file)

        n_of_evidences = int(token_extractor().pop(00))
        evidences = []
        for i in range(n_of_evidences):
            evidence_info = token_extractor()
            evidence_info.pop(0)  # to discard useless len(vars)

            evid_vars_names = evidence_info[0::2]
            evid_vars_values = map(int, evidence_info[1::2])

            evidence = tuple(zip(evid_vars_names, evid_vars_values))
            evidences.append(dict(evidence))

        evid_file.close()

        return evidences


class MarkovGraph:

    def __init__(self, adjacencies=None):
        if adjacencies is None:
            self.adjacencies = {}
        else:
            self.adjacencies = adjacencies

    @property
    def variables(self):
        return list(self.adjacencies.keys())

    def __getitem__(self, key):
        return self.adjacencies[key]

    def __setitem__(self, key, value):
        self.adjacencies[key] = value

    def __iter__(self):
        for variable in self.adjacencies:
            yield variable

    def __delitem__(self, key):
        del self.adjacencies[key]

    def get(self, key, failed_return_value):
        return self.adjacencies.get(key, failed_return_value)

    def gen_graph(markov_net, variables=None):
        if variables is None:
            variables_set = set(markov_net.variables.values())
        else:
            variables_set = set(variables)

        graph = MarkovGraph()
        for potential in markov_net.potentials.values():
            if variables_set.issuperset(potential.scope_set):
                for var in potential.scope:
                    neighbors = graph.get(var, set()) | potential.scope_set
                    graph[var] = neighbors - {var}

        return graph

    def get_reduced_copy(self, variables=None):
        if variables is None:
            variables = list(self.variables)
        else:
            variables = list(variables)

        reduced = MarkovGraph()
        for variable in variables:
            reduced.adjacencies[variable] = set()
            for neighbor in self[variable]:
                if neighbor in variables:
                    # Ugly, but effective
                    reduced.adjacencies[variable].add(neighbor)

        return reduced

    def draw(self, file_path, variables=None):
        if variables is None:
            variables = list(self.variables)
        else:
            variables = list(variables)

        import graphviz as gv

        network = gv.Graph(format='png')
        for variable in self:
            if variable in variables:
                network.node(variable.name)

        for variable in variables:
            for neighbor in self[variable]:
                if neighbor in variables and variable.name < neighbor.name:
                    # Ugly, but effective
                    network.edge(variable.name, neighbor.name)

        network.render(file_path, view=True)

    def get_min_fill_variable(self):
        min_fill = None
        min_fill_var = None

        def get_n_fill_edges_on_elimination(variable):
            neighbors = self[variable]
            n_edges = 0
            for neighbor in neighbors:
                n_edges += len(self[neighbor] & neighbors)
                return (len(neighbors) * (len(neighbors) - 1) - n_edges) // 2

        for variable in self:
            fill = get_n_fill_edges_on_elimination(variable)
            if min_fill is None or fill < min_fill:
                min_fill = fill
                min_fill_var = variable

        return min_fill_var

    def get_min_degree_variable(self):
        min_degree = None
        min_degree_var = None

        for variable in self:
            degree = len(self[variable])
            if min_degree is None or degree < min_degree:
                min_degree = degree
                min_degree_var = variable

                return min_degree_var

    def get_elimination_ordering_by_min_fill(self, elim_variables=None):
        if elim_variables is None:
            variables = list(self.variables.values())
        else:
            variables = list(elim_variables)

        graph = self.get_reduced_copy(variables)
        ordering = []
        for _ in range(len(variables)):
            min_fill_variable = graph.get_min_fill_variable()

            for neighbor in graph[min_fill_variable]:
                adjacent = graph[neighbor] | graph[min_fill_variable]
                graph[neighbor] = adjacent - {neighbor, min_fill_variable}

            del graph.adjacencies[min_fill_variable]
            variables.remove(min_fill_variable)
            ordering.append(min_fill_variable)

        return ordering

    def get_elimination_ordering_by_min_degree(self, elim_variables=None):
        if elim_variables is None:
            variables = list(self.variables.values())
        else:
            variables = list(elim_variables)

        graph = self.get_reduced_copy(variables)
        ordering = []
        for _ in range(len(variables)):
            min_degree_variable = graph.get_min_degree_variable()

            for neighbor in graph[min_degree_variable]:
                adjacent = graph[neighbor] | graph[min_degree_variable]
                graph[neighbor] = adjacent - {neighbor, min_degree_variable}

            del graph[min_degree_variable]
            variables.remove(min_degree_variable)
            ordering.append(min_degree_variable)

        return ordering


class MarkovNet:

    def __init__(self, variables, potentials):
        self.variables = variables
        self.potentials = potentials

        self.graph = MarkovGraph.gen_graph(self)

    def init_from_uai_file(uai_file_path):
        variables, potentials = UAI_Parser.parse(uai_file_path)

        return MarkovNet(variables, potentials)

    def get_variables_domains_product(self, evidence={}):
        domains = []
        for var in self.variables.values():
            if var.name in evidence.keys():
                domains.append([evidence[var.name]])
            else:
                domains.append(var.domain)
        return it.product(*domains)

    def get_partition_function(self, evidence={}):
        variables = self.variables.values()
        non_evid_vars = ([v for v in variables if v.name not in evidence])
        potentials = tuple(self.potentials.values())

        reduced = Potential.eliminate_variables(potentials, non_evid_vars)
        return reduced.evaluate(evidence)

    def get_partition_function_by_min_fill(self, evidence={}):
        variables = self.variables.values()
        elim_vars = ([v for v in variables if v.name not in evidence])

        ord_elim = self.graph.get_elimination_ordering_by_min_fill(elim_vars)
        potentials = tuple(self.potentials.values())

        reduced = Potential.eliminate_variables(potentials, ord_elim)
        return reduced.evaluate(evidence)

    def get_partition_function_by_min_degree(self, evidence={}):
        variables = self.variables.values()
        elim_vars = ([v for v in variables if v.name not in evidence])

        ord_elim = self.graph.get_elimination_ordering_by_min_degree(elim_vars)
        potentials = tuple(self.potentials.values())

        reduced = Potential.eliminate_variables(potentials, ord_elim)
        return reduced.evaluate(evidence)

    def get_partition_function_by_enumeration(self, evidence={}):
        total = 0

        var_names = [v.name for v in self.variables.values()]
        for valuation in self.get_variables_domains_product(evidence):
            var_valuation = dict(zip(var_names, valuation))
            prod = 1
            for potential in self.potentials.values():
                prod *= potential.evaluate(var_valuation)
            total += prod

        return total

    def get_variables_by_names(self, names):
        return [self.variables[name] for name in names]

    def draw(self, file_path, variables=None):
        graph = MarkovGraph.gen_graph(self, variables)
        graph.draw(file_path)


if __name__ == "__main__":
    import sys
    import math

    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print('Usage: %s <markov_net_description.uai> [evidence.uai.evid]'
              % sys.argv[0])
        sys.exit(1)

    markov_net = MarkovNet.init_from_uai_file(sys.argv[1])

    if len(sys.argv) == 3:
        evidences = UAI_Parser.parse_evidence_file(sys.argv[2])
        for i, evidence in enumerate(evidences):
            z = markov_net.get_partition_function(evidence)
            print("partition function log10 for evid %2d: %.6f" %
                  (i + 1, math.log10(z)))
    else:
        z = markov_net.get_partition_function()
        print("partition function: %.6f" % math.log10(z))
