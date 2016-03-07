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

        probability = Probability([main_var], cond_vars)

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


class Function:

    def __init__(self, variables):
        self.variables = variables
        self.values = {}

    def add_value(self, valuation, value):
        self.values[valuation] = value

    def __str__(self):
        out = []

        out.append('[F] F over %s\n' % [v.name for v in self.variables])

        domains = [v.domain for v in self.variables]

        for valuation in it.product(*domains):
            out.append('    %-25s : %10.5f\n' % (valuation, self.values[valuation]))

        return ''.join(out)

    def evaluate(self, var_valuation):
        valuation = tuple(var_valuation[v.name] for v in self.variables)

        return self.values[valuation]

    def __mul__(self, function):
        variables_union = list(set(self.variables) | set(function.variables))
        product = Function(variables_union)

        var_names = [var.name for var in product.variables]
        for valuation in it.product(*[v.domain for v in product.variables]):
            var_valuation = dict(zip(var_names, valuation))
            val = self.evaluate(var_valuation)*function.evaluate(var_valuation)
            product.values[valuation] = val

        return product

    def __div__(self, function):
        variables_union = list(set(self.variables) | set(function.variables))
        division = Function(variables_union)

        var_names = [var.name for var in division.variables]
        for valuation in it.product(*[v.domain for v in division.variables]):
            var_valuation = dict(zip(var_names, valuation))
            if function.evaluate(var_valuation) == 0:
                val = None
            else:
                val = (self.evaluate(var_valuation) /
                       function.evaluate(var_valuation))
            division.values[valuation] = val

        return division

    def __sub__(self, variable):
        var_name = variable.name

        elim_vars = [v for v in self.variables if v.name != var_name]
        elim_func = Function(elim_vars)

        elim_var_names = [var.name for var in elim_vars]
        for elim_valuation in it.product(*[v.domain for v in elim_vars]):
            var_valuation = dict(zip(elim_var_names, elim_valuation))
            val_sum = 0
            for value in variable.domain:
                var_valuation[var_name] = value
                val_sum += self.evaluate(var_valuation)
            elim_func.add_value(elim_valuation, val_sum)

        return elim_func


class Probability(Function):

    def __init__(self, main_vars, cond_vars):
        self.main_vars = main_vars
        self.cond_vars = cond_vars
        super().__init__(main_vars + cond_vars)

    def __mod__(self, variable):
        var_name = variable.name

        main_elim_vars = [v for v in self.main_vars if v.name != var_name]
        cond_elim_vars = [v for v in self.cond_vars if v.name != var_name]
        elim_func = Probability(main_elim_vars, cond_elim_vars)

        elim_var_names = [var.name for var in elim_func.variables]
        total = 0
        domains_list = [v.domain for v in elim_func.variables]
        for elim_valuation in it.product(*domains_list):
            var_valuation = dict(zip(elim_var_names, elim_valuation))
            val_sum = 0
            for value in variable.domain:
                var_valuation[var_name] = value
                val_sum += self.evaluate(var_valuation)
            elim_func.add_value(elim_valuation, val_sum)
            total += val_sum

        for k, v in elim_func.values.items():
            elim_func.values[k] = v/total
        return elim_func

    def __mul__(self, probab):
        main_vars_set = set(self.main_vars) | set(probab.main_vars)
        cond_vars_set = (set(self.cond_vars) | set(probab.cond_vars)) - \
            main_vars_set
        product = Probability(list(main_vars_set), list(cond_vars_set))

        var_names = [var.name for var in product.variables]
        for valuation in it.product(*[v.domain for v in product.variables]):
            var_valuation = dict(zip(var_names, valuation))
            val = self.evaluate(var_valuation)*probab.evaluate(var_valuation)
            product.values[valuation] = val

        return product

    def __div__(self, probab):
        main_vars_set = set(self.main_vars) | set(probab.main_vars)
        cond_vars_set = (set(self.cond_vars) | set(probab.cond_vars)) - \
            main_vars_set
        division = Probability(list(main_vars_set), list(cond_vars_set))

        var_names = [var.name for var in division.variables]
        for valuation in it.product(*[v.domain for v in division.variables]):
            var_valuation = dict(zip(var_names, valuation))
            val = self.evaluate(var_valuation)*probab.evaluate(var_valuation)
            division.values[valuation] = val

        return division


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

    # def domain_product(*variables):
    #     domains = []
    #     return it.product(*var)


class Node:

    def __init__(name, parents):
        pass


class BayesNet:

    def __init__(self, name, nodes, probs, properties=None):
        self.name = name
        self.nodes = nodes
        self.probs = probs
        self.properties = properties

        self.var_distribution = {}

    def parent_nodes(self, node_name):
        return [parent.name for parent in self.probs[node_name].cond_vars]

    def init_from_bif_file(bif_file_path):
        data_list = BIF_Parser.parse(bif_file_path)

        network_name = 'None'
        nodes = {}  # indexed by variables names
        probs = {}  # indexed by nodes indexes
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
                probs[prob.main_vars[0].name] = prob

        return BayesNet(network_name, nodes, probs, properties)

    def draw(self, file_path):
        import graphviz as gv

        network = gv.Digraph(format='png')
        for node in self.nodes:
            network.node(node)

        for node in self.nodes:
            for parent in self.parent_nodes(node):
                network.edge(parent, node)
        network.render(file_path, view=True)

    def query(valuation):  # valuation = {'name': 'value'}
        # Factorization Theorem
        pass

    def get_var_distribution(self, var_name):
        if not self.parent_nodes(var_name):
            return self.probs[var_name]

        prob = self.probs[var_name]
        for parent in self.parent_nodes(var_name):
            prob *= self.get_var_distribution(parent)
        for var in prob.variables:
            if var.name != var_name:
                prob %= var

        return prob

    def get_ancestors_set(self, nodes):  # ancestor including the node
        parent_nodes_set = set()
        for node in nodes:
            parent_nodes_set |= set(self.parent_nodes(node))
        parent_nodes_not_in_nodes_set = parent_nodes_set - set(nodes)

        if not parent_nodes_not_in_nodes_set:
            return set()

        return set(nodes) | parent_nodes_set | \
            self.get_ancestors_set(parent_nodes_not_in_nodes_set)

    def get_joint_distribution(self, variables_names):
        ancestors_set = self.get_ancestors_set(variables_names)

        prob = self.probs[ancestors_set.pop()]
        for var_name in ancestors_set:
            prob *= self.probs[var_name]

        variables_names_set = set(variables_names)
        for var in prob.variables:
            if var.name not in variables_names_set:
                prob %= var

        return prob

    def conjunctive_query(self, valuation):
        joint_distribution = self.get_joint_distribution(valuation.keys())

        return joint_distribution.evaluate(valuation)


if __name__ == "__main__":
    v = BayesNet.init_from_bif_file('../examples/bayesnet/asia/asia.bif')
    vs = v.nodes
    fs = v.probs
    n = BayesNet.init_from_bif_file('../examples/bayesnet/asia/rain.bif')
