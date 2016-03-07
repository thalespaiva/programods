#!/usr/bin/python3

import problogic
import pyparsing as pp


class Function:

    def __init__(self, variables):
        self.variables = variables
        self.values = {}

    def add_value(self, valuation, value):
        self.values[valuation] = value


class BIF_Parser:

    def parse(file_path):
        pp.ParserElement.setDefaultWhitespaceChars(", |\t\n")

        word = pp.Word(pp.alphas + '_-', pp.alphanums + '_-')
        integ = pp.Word(pp.nums)
        number = pp.Combine(integ + pp.Optional('.' + pp.Optional(integ)))
        lpar, rpar, lbr, rbr, lsqbr, rsqbr, sc = map(pp.Suppress, '(){}[];')

        keywords = ["network", "variable", "probability", "property",
                    "type", "discrete", "default", "table"]
        lit_keywords = map(pp.Literal, keywords)
        net, var, prob, prop, vartype, disc, defvals, tabvals = lit_keywords

        prop_decl = pp.Group(prop + pp.Regex(r'[^;]*') + sc)
        var_name = word
        var_value = pp.Word(pp.alphanums + '_-')
        var_values_list = pp.OneOrMore(var_value)

        net_cont = lbr + pp.Group(pp.ZeroOrMore(prop_decl)) + rbr
        net_decl = pp.Group(net + word + net_cont)

        disc_var = vartype + disc + lsqbr + integ + rsqbr + lbr + \
            pp.Group(var_values_list) + rbr + sc
        var_cont = lbr + pp.ZeroOrMore(prop_decl) + pp.Group(disc_var) + \
            pp.ZeroOrMore(prop_decl) + rbr
        var_decl = pp.Group(var + var_name + var_cont)

        number_list = pp.OneOrMore(number)
        var_list = pp.OneOrMore(var_name)

        prob_def_entry = number_list + sc
        prob_table = pp.Group(tabvals + pp.Group(number_list) + sc)
        prob_entry = lpar + pp.Group(var_values_list) + rpar + \
            pp.Group(number_list) + sc
        # prob_cont = lbr + "table 0.01, 0.99;" + rbr
        prob_cont = lbr + pp.ZeroOrMore(prop_decl |
                                        prob_def_entry |
                                        pp.Group(prob_entry) |
                                        prob_table) + rbr

        prob_decl = pp.Group(prob + lpar +
                             pp.Group(var_name +
                                      pp.Group(pp.Optional(var_list))) +
                             rpar + prob_cont)

        bif_file = net_decl + pp.ZeroOrMore(var_decl | prob_decl)
        # bif_file = net_decl + pp.ZeroOrMore(pp.printables)

        return bif_file.parseFile(file_path).asList()
        return bif_file


class Variable:

    def __init__(self, name, type_, domain):
        self.name = name
        self.type = type_
        self.domain = domain

    def parse_variable_declaration(name, str_var_decl):
        word, number, value = map(pp.Word,
                                  [pp.alphas, pp.nums, pp.alphanums + '_'])
        rbr, lbr, lsqbr, rsqbr = map(pp.Suppress, '{}[]')

        var_type = pp.Suppress('type') + word
        var_values = lbr + value + pp.Optional(',' + value) + rbr
        var_info = lbr + var_type + lsqbr + number + lsqbr + var_values

        name, type_, values = var_info.parseString(str_var_decl)

        return Variable(name, type_, values)


class BayesNet:

    def __init__(self):
        pass

    def init_from_bif_file(bif_file_path):
        pass

    def parse_bif_file(bif_file_path):
        bif_file = open(bif_file_path, 'r')
