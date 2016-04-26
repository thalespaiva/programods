
import itertools as it
import random


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

    def get_valuation(variables, values):
        return dict(zip(variables, values))

    def get_names(variables, num_chars=None):
        if not num_chars:
            return [var.name for var in variables]
        else:
            return [var.name[:num_chars] for var in variables]

    def get_names_string(variables, num_chars=None):
        return ','.join(Variable.get_names(variables, num_chars))

    def domains_product(variables):
        domains = [var.domain for var in variables]
        for values in it.product(*domains):
            yield values

    @property
    def cardinality(self):
        return len(self.domain)

    def are_consistent(this_valuation, that_valuation):
        for var in this_valuation:
            this_value = this_valuation[var]
            that_value = that_valuation.get(var, None)
            if that_value is not None and this_value != that_value:
                return False

        return True


class Potential:

    def __init__(self, scope, values=None):
        self.scope_set = set(scope)  # for fast __contains__
        self.scope = tuple(scope)     # to keep order of values indexes

        if values is None:
            self.values = {}
        else:
            self.set_values(values)

    def has_variable(self, variable):
        return variable in self.scope_set

    def __str__(self):
        out = []

        if not isinstance(self, LocalProbability):
            out.append("[+] Potential\n")
        out.append("[ ] Scope: %s\n" % Variable.get_names_string(self.scope))

        for valuation in Variable.domains_product(self.scope):
            out.append("[ ] %10s | " % ','.join(map(str, valuation)))
            out.append(" %-.4f \n" % self[valuation])
        out.append('[.]')
        return ''.join(out)

    def __getitem__(self, key):
        if not isinstance(key, tuple):
            raise TypeError('Keys should be tuples. len(key) == 1?')
        return self.values.get(key, 0)

    def __setitem__(self, key, value):
        if not isinstance(key, tuple):
            raise TypeError('Keys should be tuples. len(key) == 1?')
        self.values[key] = value

    def set_values(self, values):
        if not all([isinstance(key, tuple) for key in values]):
            raise TypeError('All keys should be tuples. len(key) == 1?')
        self.values = values

    def evaluate(self, var_valuation):
        valuation = tuple(var_valuation[v.name] for v in self.scope)

        return self[valuation]

    def __mul__(self, himself):
        product = Potential(self.scope_set | himself.scope_set)

        var_names = Variable.get_names(product.scope)

        for values in Variable.domains_product(product.scope):
            valuation = Variable.get_valuation(var_names, values)
            value = self.evaluate(valuation)*himself.evaluate(valuation)
            product[values] = value
        return product

    def __mod__(self, variable):

        if self.scope_set == {variable}:
            return Potential([], {(): sum(self.values.values())})

        var_name = variable.name

        elim_vars = [v for v in self.scope if v.name != var_name]
        elim_func = Potential(elim_vars)

        elim_var_names = Variable.get_names(elim_func.scope)

        for elim_vals in Variable.domains_product(elim_func.variables):
            valuation = Variable.get_valuation(elim_var_names, elim_vals)
            sum_ = 0
            for value in variable.domain:
                valuation[var_name] = value
                sum_ += self.evaluate(valuation)
            elim_func[elim_vals] = sum_

        return elim_func

    def __truediv__(self, probab):
        quotient = Potential(self.scope_set | himself.scope_set)

        var_names = Variable.get_names(quotient.scope)
        for values in Variable.domains_product(quotient.scope):
            valuation = Variable.get_valuation(var_names, values)
            value = self.evaluate(valuation)/himself.evaluate(valuation)
            quotient[values] = value

        return quotient

    def normalize(self):
        total = sum(self.values.values())

        for k, v in self.values.items():
            self.values[k] = v/total

    def combine(potentials):
        if len(potentials) == 1:
            return potentials[0]

        product = Potential(set.union(*[p.scope_set for p in potentials]))
        var_names = Variable.get_names(product.scope)

        for values in Variable.domains_product(product.scope):
            valuation = Variable.get_valuation(var_names, values)
            value = 1
            for p in potentials:
                value *= p.evaluate(valuation)
            product[values] = value

        return product

    def eliminate_variables(potentials_tuple, variables):
        potentials = list(potentials_tuple)

        for variable in variables:
            dependents = []
            for pot in potentials:
                if pot.has_variable(variable):
                    dependents.append(pot)
            combined = Potential.combine(dependents)
            for dep in dependents:
                potentials.remove(dep)
            potentials.append(combined % variable)

        return Potential.combine(potentials)

    @property
    def variables(self):
        return self.scope


class LocalProbability(Potential):

    def __init__(self, main_var, parent_vars):
        self.main_var = main_var
        self.parent_vars = parent_vars
        super().__init__([main_var] + parent_vars)

    def __str__(self):
        out = []

        out.append("[+] LocalProbability(%s" % self.main_var.name)
        out.append("|%s)\n" % ','.join(Variable.get_names(self.parent_vars)))
        out.append(super().__str__())

        return ''.join(out)

    def get_markdown_table(self):
        out = []

        out.append("**Local Probability (")
        out.append("%s" % self.main_var.name)
        if self.parent_vars:
            out.append("|%s" % ','.join([p.name for p in self.parent_vars]))
        out.append(")**\n\n")

        main_var = self.main_var
        parent_vars = self.parent_vars
        parent_vars_names = [p.name for p in self.parent_vars]

        for p in parent_vars:
            out.append('| %s' % p.name)
        for valuation in self.main_var.domain:
            out.append('|%s = %s' % (main_var.name, valuation))
        out.append('|\n')

        for p in parent_vars:
            out.append('|:-:')
        for valuation in self.main_var.domain:
            out.append('|:-:')
        out.append('|\n')

        if not self.parent_vars:
            for valuation in Variable.domains_product([main_var]):
                out.append('|%0.4f' % self[valuation])
            out.append('|\n')

        else:
            for values in Variable.domains_product(parent_vars):
                valuation = Variable.get_valuation(parent_vars_names, values)
                for parent in parent_vars:
                    out.append('|%3s' % valuation[parent.name])
                for v in main_var.domain:
                    valuation[main_var.name] = v
                    out.append("| %-.4f" % self.evaluate(valuation))
                out.append('|\n')

        return ''.join(out)

    def gen_random_sample_given_parents(self, valuation):
        limit = 1
        for value in self.main_var.domain:
            valuation[self.main_var.name] = value
            prob = self.evaluate(valuation)

            if random.uniform(0, limit) <= prob:
                return value

            limit -= prob

        # Very low probability but just in case:
        return value
