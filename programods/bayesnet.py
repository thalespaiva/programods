
import random

import itertools as it
import pyparsing as pp

from programods.distribution import Variable
from programods.distribution import Potential
from programods.distribution import LocalProbability


class BIF_Parser:

    NET_KEY = "network"
    VAR_KEY = "variable"
    PROB_KEY = "probability"
    PROP_KEY = "property"
    TYPE_KEY = "type"
    DISC_KEY = "discrete"
    DEFVALS_KEY = "default"
    TABVALS_KEY = "table"

    DATA_VARS = 'variables'
    DATA_NET = 'network'
    DATA_PROBS = 'probabilities'

    def parse(file_path):
        pp.ParserElement.setDefaultWhitespaceChars(", |\t\n")

        word = pp.Word(pp.alphas + '_-', pp.alphanums + '_-')
        integ = pp.Word(pp.nums)
        number = pp.Combine(integ + pp.Optional('.' + pp.Optional(integ)))
        lpar, rpar, lbr, rbr, lsb, rsb, sc = map(pp.Suppress, '(){}[];')

        keywords = [BIF_Parser.NET_KEY, BIF_Parser.VAR_KEY,
                    BIF_Parser.PROB_KEY, BIF_Parser.PROP_KEY,
                    BIF_Parser.TYPE_KEY, BIF_Parser.DISC_KEY,
                    BIF_Parser.DEFVALS_KEY, BIF_Parser.TABVALS_KEY]
        lit_keywords = map(pp.Literal, keywords)
        net, var, prob, prop, vartype, disc, defvals, tabvals = lit_keywords

        prop_decl = pp.Group(prop + pp.Regex(r'[^;]*') + sc)
        var_name = word
        var_value = pp.Word(pp.alphanums + '_-')
        var_values_list = pp.OneOrMore(var_value)

        net_cont = lbr + pp.Group(pp.ZeroOrMore(prop_decl)) + rbr
        net_decl = pp.Group(net + word + net_cont)

        disc_var = pp.Group(vartype.suppress() + disc + lsb + integ + rsb) + \
            lbr + pp.Group(var_values_list) + rbr + sc
        var_cont = lbr + pp.ZeroOrMore(prop_decl) + pp.Group(disc_var) + \
            pp.ZeroOrMore(prop_decl) + rbr
        var_decl = pp.Group(var + var_name + var_cont)

        number_list = pp.OneOrMore(number)
        var_list = pp.OneOrMore(var_name)

        prob_def_entry = number_list + sc
        prob_table = tabvals + pp.Group(number_list) + sc
        prob_entry = lpar + pp.Group(var_values_list) + rpar + \
            pp.Group(number_list) + sc
        prob_cont = lbr + pp.ZeroOrMore(prop_decl |
                                        pp.Group(prob_def_entry) |
                                        pp.Group(prob_entry) |
                                        prob_table) + rbr

        prob_decl = pp.Group(prob + lpar +
                             pp.Group(var_name +
                                      pp.Group(pp.Optional(var_list))) +
                             rpar + pp.Group(prob_cont))

        bif_file = net_decl + pp.ZeroOrMore(var_decl | prob_decl)

        return bif_file.parseFile(file_path).asList()

    def _get_variable_from_data_item(item):
        var_name = item.pop(0)
        var_info = item.pop(0)
        var_type_info = var_info.pop(0)
        var_type_info.pop(0)  # get rid of useless type (obviously discrete)
        # var_domain_size = var_type_info.pop(0)
        var_domain = var_info.pop(0)

        return Variable(var_name, var_domain)

    def _get_prob_from_data_item(item, variables):
        vars_info = item.pop(0)
        main_var = variables[vars_info.pop(0)]
        parent_vars = [variables[v] for v in vars_info.pop(0)]

        probability = LocalProbability(main_var, parent_vars)

        probs_info = item.pop(0)
        if probs_info[0] == BIF_Parser.TABVALS_KEY:
            prob_table = probs_info[1]
            domains_list = [main_var.domain] + [v.domain for v in parent_vars]
            for valuation, prob in zip(it.product(*domains_list), prob_table):
                probability[tuple(valuation)] = float(prob)
        else:
            for cond_valuation, probs in probs_info:
                valuations = [[d] + cond_valuation for d in main_var.domain]
                for valuation, prob in zip(valuations, probs):
                    probability[tuple(valuation)] = float(prob)

        return probability


class BayesNet:

    def __init__(self, name, nodes, local_probs, properties=None):
        self.name = name
        self.nodes = nodes
        self.local_probs = local_probs
        self.properties = properties

    def __getitem__(self, index):
        return self.nodes[index]

    def __iter__(self):
        for node in self.nodes:
            yield node

    def parent_nodes(self, node_name):
        return [prnt.name for prnt in self.local_probs[node_name].parent_vars]

    def child_nodes(self, node_name):
        target_node = self[node_name]
        children = []

        for node in self:
            if target_node in self.local_probs[node].parent_vars:
                children.append(node)

        return children

    def reachable_via_active_trails(self, source_vars, observed_set):
        observed_set = set(observed_set)
        up, down = 'up', 'down'

        obs_ancestors = self.get_ancestors_set(observed_set)

        schedule = [(source_var, up) for source_var in source_vars]
        visited = set()
        reachable = set()

        def schedule_parents(node):
            for n in self.parent_nodes(node):
                schedule.append((n, up))

        def schedule_children(node):
            for n in self.child_nodes(node):
                schedule.append((n, down))

        while schedule:
            visiting = schedule.pop()
            if visiting not in visited:
                node, direct = visiting
                if node not in observed_set:
                    reachable.add(node)
                visited.add(visiting)
                if direct == up and node not in observed_set:
                    schedule_parents(node)
                    schedule_children(node)
                elif direct == down:
                    if node not in observed_set:
                        schedule_children(node)
                    if node in obs_ancestors:
                        schedule_parents(node)

        return reachable

    def is_d_separated(self, this_set, that_set, observed_set=None):
        if observed_set is None:
            observed_set = []

        this_set, that_set = set(this_set), set(that_set)

        reachable = self.reachable_via_active_trails(this_set, observed_set)

        return len(reachable & that_set) == 0

    def draw_reachable_via_active_trails(self, tgt, src_vars, observed_set):
        import graphviz as gv

        reachable = self.reachable_via_active_trails(src_vars, observed_set)

        network = gv.Digraph(format='png')
        for node in self:
            if node in src_vars:
                color = 'blue'
            elif node in reachable:
                color = 'green'
            elif node in observed_set:
                color = 'grey'
            else:
                color = 'red'
            network.node(node, color=color)

        for node in self:
            for parent in self.parent_nodes(node):
                network.edge(parent, node)
        network.render(tgt, view=True)

    def init_from_bif_file(bif_file_path):
        data_list = BIF_Parser.parse(bif_file_path)

        network_name = 'None'
        nodes = {}  # indexed by variables names
        local_probs = {}  # indexed by nodes indexes
        properties = []

        for item in data_list:
            item_type = item.pop(0)
            if item_type == BIF_Parser.NET_KEY:
                network_name = item.pop(0)
                properties.append(item.pop(0))

            elif item_type == BIF_Parser.VAR_KEY:
                variable = BIF_Parser._get_variable_from_data_item(item)
                nodes[variable.name] = variable

            if item_type == BIF_Parser.PROB_KEY:
                prob = BIF_Parser._get_prob_from_data_item(item, nodes)
                local_probs[prob.main_var.name] = prob

        return BayesNet(network_name, nodes, local_probs, properties)

    def draw(self, file_path):
        import graphviz as gv

        network = gv.Digraph(format='png')
        for node in self:
            network.node(node)

        for node in self:
            for parent in self.parent_nodes(node):
                network.edge(parent, node)
        network.render(file_path, view=True)

    def get_conditional_distrib(self, main_vars, parent_vars):
        joint_dist = self.get_joint_distribution(main_vars + parent_vars)
        cond_dist = self.get_joint_distribution(parent_vars)

        return joint_dist/cond_dist

    def get_var_distribution(self, var_name):
        if not self.parent_nodes(var_name):
            return self.local_probs[var_name]

        prob = self.local_probs[var_name]
        for parent in self.parent_nodes(var_name):
            prob *= self.get_var_distribution(parent)
        for var in prob.variables:
            if var.name != var_name:
                prob %= var

        return prob

    def get_ancestors_set(self, nodes_names):  # ancestor including the node
        parent_nodes_set = set()
        for node in nodes_names:
            parent_nodes_set |= set(self.parent_nodes(node))
        parent_nodes_not_in_nodes_set = parent_nodes_set - set(nodes_names)

        if not parent_nodes_not_in_nodes_set:
            return set(nodes_names)

        return set(nodes_names) | parent_nodes_set | \
            self.get_ancestors_set(parent_nodes_not_in_nodes_set)

    def get_joint_distribution(self, variables_names):
        ancestors_set = self.get_ancestors_set(variables_names)

        prob = self.local_probs[ancestors_set.pop()]
        for var_name in ancestors_set:
            prob *= self.local_probs[var_name]
        variables_names_set = set(variables_names)
        for var in prob.variables:
            if var.name not in variables_names_set:
                prob %= var

        prob.normalize()
        return prob

    def get_markov_blanket(self, node):

        if isinstance(node, Variable):
            node = node.name

        parents = set(self.parent_nodes(node))
        children = set(self.child_nodes(node))
        espouses = set()
        for child in children:
            espouses |= set(self.parent_nodes(child))

        return (parents | children | espouses) - {node}

    def get_probability_given_markov_blanket(self, node, mb_valuation):
        potentials = [self.local_probs[c] for c in self.child_nodes(node)]
        potentials.append(self.local_probs[node])

        combined = Potential.combine(potentials)
        return combined.get_reduced(mb_valuation)

    def conjunctive_query(self, valuation_dict=None, **kwargs):
        if valuation_dict is not None:
            valuation = valuation_dict
        elif kwargs is not None:
            valuation = kwargs

        variables = self.nodes.values()
        non_evid_vars = ([v for v in variables if v.name not in valuation])
        potentials = tuple(self.local_probs.values())

        reduced = Potential.eliminate_variables(potentials, non_evid_vars)
        return reduced.evaluate(valuation)

    def conjunctive_query_by_enumeration(self, valuation_dict=None, **kwargs):
        if valuation_dict is not None:
            valuation = valuation_dict
        elif kwargs is not None:
            valuation = kwargs

        joint_distribution = self.get_joint_distribution(valuation.keys())
        return joint_distribution.evaluate(valuation)

    def get_topological_ordering(self):
        ordering = []
        marked = set()
        tmp_marked = set()

        def visit(node):
            if node in tmp_marked:
                raise ValueError("Not a DAG!")
            if node not in marked:
                tmp_marked.add(node)
                for child in self.child_nodes(node):
                    visit(child)
                tmp_marked.remove(node)
                marked.add(node)

                ordering.append(node)

        nodes = set(self.nodes.keys())

        for node in nodes:
            if node not in marked:
                visit(node)

        return list(reversed(ordering))

    def conjunctive_query_by_logical_sampling(self, sample_size,
                                              valuation_dict=None, **kwargs):
        if valuation_dict is not None:
            valuation = valuation_dict
        elif kwargs is not None:
            valuation = kwargs

        topological_ordering = self.get_topological_ordering()

        consistent_count = 0
        for _ in range(sample_size):
            candidate_val = {}
            for i, var in enumerate(topological_ordering):
                local_prob = self.local_probs[var]
                val = local_prob.gen_random_sample_given_parents(candidate_val)
                candidate_val[var] = val

            if Variable.are_consistent(valuation, candidate_val):
                consistent_count += 1

        return consistent_count/sample_size

    def conjunctive_query_by_likelihood_weighting(self, sample_size, **kwargs):
        evidence_valuation = kwargs

        topological_ordering = self.get_topological_ordering()

        sum_of_weights = 0
        for _ in range(sample_size):
            topo_val = {}
            weight = 1
            for i, var in enumerate(topological_ordering):
                local_prob = self.local_probs[var]
                if var not in evidence_valuation:
                    val = local_prob.gen_random_sample_given_parents(topo_val)
                    topo_val[var] = val
                else:
                    topo_val[var] = evidence_valuation[var]
                    weight *= local_prob.evaluate(topo_val)

            sum_of_weights += weight

        return sum_of_weights/sample_size

    def conjunctive_query_by_gibbs_sampling(self, sample_size, **kwargs):
        evidence_valuation = kwargs

        def get_prob(index, ordering, old_valuation, new_valuation):
            import random

            valuation = {}
            for i, var in enumerate(ordering):
                if i < index:
                    valuation[var] = new_valuation[var]
                elif i > index:
                    valuation[var] = old_valuation[var]
            target_var = ordering[index]
            dist = self.get_probability_given_markov_blanket(target_var,
                                                             valuation)
            lp = LocalProbability(self[target_var], [])
            lp.set_values(dist.values)

            return lp.gen_random_sample_given_parents({})

        old_valuation = {v: evidence_valuation[v] for v in evidence_valuation}
        for v in self.nodes:
            if v not in evidence_valuation:
                old_valuation[v] = random.choice(self[v].domain)
        from pprint import pprint

        ordering = list(self.nodes)
        consistent_count = 0

        valuations = [old_valuation, {}]

        for k in range(sample_size):
            old_valuation = valuations[k % 2]
            new_valuation = valuations[(k + 1) % 2]

            for i, var in enumerate(ordering):
                new_valuation[var] = get_prob(i, ordering, old_valuation,
                                              new_valuation)
            if Variable.are_consistent(new_valuation, evidence_valuation):
                consistent_count += 1

        return consistent_count/sample_size



if __name__ == "__main__":
    from programods import EXAMPLE_FILES_PATH
    from os import path

    asia_file = path.join(EXAMPLE_FILES_PATH, 'bayesnet', 'asia', 'asia.bif')
    rain_file = path.join(EXAMPLE_FILES_PATH, 'bayesnet', 'rain', 'rain.bif')

    asia = BayesNet.init_from_bif_file(asia_file)
    rain = BayesNet.init_from_bif_file(rain_file)

    # p, q = asia.local_probs['lung'], asia.local_probs['xray']
    # print(p)
    # print(q)
    # r = p * q
    # print(r)
    # v = asia['smoke']
    # z = r % v
    # print(z)
    valuation = {'xray': 'yes', 'dysp': 'no'}
    print(asia.conjunctive_query(valuation))

    for prob in sorted(asia.local_probs.values(), key=lambda x: len(x.scope)):
        print(prob.get_markdown_table())
