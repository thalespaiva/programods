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

    def _get_probability_from_data_item(item, variables):
        vars_info = item.pop(0)
        main_var = variables[vars_info.pop(0)]
        cond_vars = [variables[v] for v in vars_info.pop(0)]

        probability = Function([main_var] + cond_vars)

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

    def get_data_from_file(file_path):
        data_list = BIF_Parser.parse(file_path)

        network_name = 'None'
        variables = {}
        for item in data_list:
            item_type = item.pop(0)
            if item_type == BIF_Parser.NET_KEY:
                network_name = item.pop(0)
                network_properties = item.pop(0)

            elif item_type == BIF_Parser.VAR_KEY:
                variable = BIF_Parser._get_variable_from_data_item(item)
                variables[variable.name] = variable

            if item_type == BIF_Parser.PROB_KEY:
                BIF_Parser._get_probability_from_data_item(item, variables)
        return (network_name, variables)


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
            out.append('    %10s : %s\n' % (valuation, self.values[valuation]))

        return ''.join(out)

    def evaluate(self, var_valuation):
        valuation = tuple(var_valuation[v.name] for v in self.variables)

        return self.values[valuation]

    def __mul__(self, function):
        variables_union = list(set(self.variables) | set(function.variables))
        print('asldk', variables_union)
        product = Function(variables_union)

        for valuation in it.product(*[v.domain for v in product.variables]):
            var_names = [var.name for var in product.variables]
            var_valuation = dict(zip(var_names, valuation))
            val = self.evaluate(var_valuation)*function.evaluate(var_valuation)
            product.values[valuation] = val

        return product


class Probability(Function):
    pass


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


class Node:

    def __init__(name, parents):
        pass


class BayesNet:

    def __init__(self, name):
        self.variables = variables
        self.node = None

    def init_empty_net():
        return BayesNet('None')

    def init_from_bif_file(bif_file_path):
        return BIF_Parser.get_bayesnet_from_file(bif_file_path)
