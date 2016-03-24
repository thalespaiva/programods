#!/usr/bin/python3

import itertools as it
import pyparsing as pp


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
        var_type = var_type_info.pop(0)
        # var_domain_size = var_type_info.pop(0)
        var_domain = var_info.pop(0)

        return Variable(var_name, var_type, var_domain)

    def _get_prob_from_data_item(item, variables):
        vars_info = item.pop(0)
        main_var = variables[vars_info.pop(0)]
        cond_vars = [variables[v] for v in vars_info.pop(0)]

        probability = Distribution([main_var], cond_vars)

        probs_info = item.pop(0)
        if probs_info[0] == BIF_Parser.TABVALS_KEY:
            prob_table = probs_info[1]
            domains_list = [main_var.domain] + [v.domain for v in cond_vars]
            for valuation, prob in zip(it.product(*domains_list), prob_table):
                probability.add_value(tuple(valuation), float(prob))
        else:
            for cond_valuation, probs in probs_info:
                valuations = [[d] + cond_valuation for d in main_var.domain]
                for valuation, prob in zip(valuations, probs):
                    probability.add_value(tuple(valuation), float(prob))

        return probability


class Distribution:

    def __init__(self, main_vars, cond_vars):
        self.main_vars = main_vars
        self.cond_vars = cond_vars

        self.values = {}

    @property
    def variables(self):
        return self.main_vars + self.cond_vars

    def __getitem__(self, key):
        return self.values.get(key, 0)

    def __setitem__(self, key, value):
        self.values[key] = value

    def add_value(self, valuation, value):
        self.values[valuation] = value

    def set_values(self, values):
        self.values = values

    def evaluate(self, var_valuation):
        valuation = tuple(var_valuation[v.name] for v in self.variables)

        return self[valuation]

    def __str__(self):
        out = []

        main_domains = [main.domain for main in self.main_vars]
        cond_domains = [cond.domain for cond in self.cond_vars]

        out.append("[+] Distribution(")
        out.append("%s" % ','.join(map(lambda x: x.name, self.main_vars)))
        out.append(" | ")
        out.append("%s" % ','.join(map(lambda x: x.name, self.cond_vars)))
        out.append(")\n")
        out.append("%10s " % ','.join(map(lambda x: x.name[:3],
                                          self.cond_vars)))
        for main_val in it.product(*main_domains):
            out.append("| %-8s" % ','.join(map(str, main_val)))

        for cond_val in it.product(*cond_domains):
            out.append("\n")
            out.append("%10s " % ','.join(map(str, cond_val)))
            for main_val in it.product(*main_domains):
                out.append("| %.4f  " % self[main_val + cond_val])

        return ''.join(out)

    def valuate_consist(self, valuation, variable, value):
        if not valuation.get(variable) or valuation.get(variable) == value:
            valuation[variable] = value
            return self.evaluate(valuation)
        else:
            return 0

    def gen_consistent_valuation_or_none(self, var_valuation_tuples):
        valuation = {}
        for var, value in var_valuation_tuples:
            if not valuation.get(var) or valuation.get(var) == value:
                valuation[var] = value
            else:
                return None
        return valuation

    def __mod__(self, variable):
        var_name = variable.name

        main_elim_vars = [v for v in self.main_vars if v.name != var_name]
        cond_elim_vars = [v for v in self.cond_vars if v.name != var_name]
        elim_func = Distribution(main_elim_vars, cond_elim_vars)

        elim_var_names = [var.name for var in elim_func.variables]
        domains_list = [v.domain for v in elim_func.variables]

        factor = 1/len(variable.domain)

        for elim_valuation in it.product(*domains_list):
            var_valuation = zip(elim_var_names, elim_valuation)
            consist_val = self.gen_consistent_valuation_or_none(var_valuation)
            if consist_val:
                sum_ = 0
                for value in variable.domain:
                    consist_val[var_name] = value
                    sum_ += self.evaluate(consist_val)
                elim_func.add_value(elim_valuation, sum_*factor)

        return elim_func

    def __mul__(self, probab):
        main_vars_set = self.main_vars + probab.main_vars
        cond_vars_set = self.cond_vars + probab.cond_vars
        product = Distribution(main_vars_set, cond_vars_set)

        var_names = [var.name for var in product.variables]
        for valuation in it.product(*[v.domain for v in product.variables]):
            var_valuation = zip(var_names, valuation)
            consist_val = self.gen_consistent_valuation_or_none(var_valuation)
            if consist_val:
                val = self.evaluate(consist_val)*probab.evaluate(consist_val)
                product[valuation] = val

        return product

    def __truediv__(self, probab):
        main_vars_set = self.main_vars + probab.main_vars
        cond_vars_set = self.cond_vars + probab.cond_vars
        division = Distribution(main_vars_set, cond_vars_set)

        var_names = [var.name for var in division.variables]
        for valuation in it.product(*[v.domain for v in division.variables]):
            var_valuation = zip(var_names, valuation)
            consist_val = self.gen_consistent_valuation_or_none(var_valuation)
            if consist_val:
                val = self.evaluate(consist_val)*probab.evaluate(consist_val)
                division[valuation] = val

        return division

    def normalize(self):
        total = sum(self.values.values())

        for k, v in self.values.items():
            self.values[k] = v/total


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
        return [prnt.name for prnt in self.local_probs[node_name].cond_vars]

    def child_nodes(self, node_name):
        target_node = self[node_name]
        children = []

        for node in self:
            if target_node in self.local_probs[node].cond_vars:
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

    def is_d_separated(self, this_set, that_set, observed_set):
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
                local_probs[prob.main_vars[0].name] = prob

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

    def get_conditional_distrib(self, main_vars, cond_vars):
        joint_dist = self.get_joint_distribution(main_vars + cond_vars)
        cond_dist = self.get_joint_distribution(cond_vars)

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

    def conjunctive_query(self, valuation):
        joint_distribution = self.get_joint_distribution(valuation.keys())

        return joint_distribution.evaluate(valuation)


if __name__ == "__main__":
    asia = BayesNet.init_from_bif_file('../examples/bayesnet/asia/asia.bif')
    rain = BayesNet.init_from_bif_file('../examples/bayesnet/rain/rain.bif')
    p, q = asia.local_probs['lung'], asia.local_probs['xray']
    print(p)
    print(q)
    r = p * q
    print(r)
    v = asia['smoke']
    z = r % v
    print(z)
    valuation = {'xray': 'yes', 'dysp': 'no'}
    print(asia.conjunctive_query(valuation))
