#!/usr/bin/python3

import itertools as it


class Variable:

    def __init__(self, name, domain_or_cardinality):
        self.name = name

        if isinstance(domain_or_cardinality, int):
            self.domain = range(domain_or_cardinality)
        else:
            self.domain = domain_or_cardinality

    def __str__(self):
        out = []

        out.append('[V] Name : %s\n' % self.name)
        out.append('    Dom  : %s' % self.domain)

        return "".join(out)

    def __repr__(self):
        return "Variable<" + self.name + ">"

    def get_consistent_valuation(variables, values):
        valuation = {}

        if isinstance(variables[0], str):
            var_names = variables
        else:
            var_names = [var.name for var in variables]

        for name, value in zip(var_names, values):
            if name not in valuation:
                valuation[name] = value
            elif valuation[name] != value:
                return None

        return valuation

    @property
    def cardinality(self):
        return len(self.domain)


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

    def __mod__(self, variable):
        var_name = variable.name

        main_elim_vars = [v for v in self.main_vars if v.name != var_name]
        cond_elim_vars = [v for v in self.cond_vars if v.name != var_name]
        elim_func = Distribution(main_elim_vars, cond_elim_vars)

        elim_var_names = [var.name for var in elim_func.variables]
        domains_list = [v.domain for v in elim_func.variables]

        factor = 1/len(variable.domain)

        for elim_vals in it.product(*domains_list):
            consist_val = Variable.get_consistent_valuation(elim_var_names,
                                                            elim_vals)
            if consist_val:
                sum_ = 0
                for value in variable.domain:
                    consist_val[var_name] = value
                    sum_ += self.evaluate(consist_val)
                elim_func.add_value(elim_vals, sum_*factor)

        return elim_func

    def __mul__(self, probab):
        main_vars_set = self.main_vars + probab.main_vars
        cond_vars_set = self.cond_vars + probab.cond_vars
        product = Distribution(main_vars_set, cond_vars_set)

        var_names = [var.name for var in product.variables]
        for values in it.product(*[v.domain for v in product.variables]):
            consist_val = Variable.get_consistent_valuation(var_names, values)
            if consist_val:
                value = self.evaluate(consist_val)*probab.evaluate(consist_val)
                product[values] = value

        return product

    def __truediv__(self, probab):
        main_vars_set = self.main_vars + probab.main_vars
        cond_vars_set = self.cond_vars + probab.cond_vars
        division = Distribution(main_vars_set, cond_vars_set)

        var_names = [var.name for var in division.variables]
        for values in it.product(*[v.domain for v in division.variables]):
            consist_val = Variable.get_consistent_valuation(var_names, values)
            if consist_val:
                val = self.evaluate(consist_val)*probab.evaluate(consist_val)
                division[values] = val

        return division

    def normalize(self):
        total = sum(self.values.values())

        for k, v in self.values.items():
            self.values[k] = v/total
