
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

    def get_valuation(variables, values):
        return Variable.get_consistent_valuation(variables, values)

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


class Potential:

    def __init__(self, scope, values=None):
        self.scope_set = set(scope)  # for fast __in__
        self.scope = tuple(scope)     # to keep order of values indexes

        if values is None:
            self.values = {}
        else:
            self.set_values(values)

    def __in__(self, variable):
        return variable in self.scope_set

    def __str__(self):
        out = []

        if not isinstance(self, LocalProbability):
            out.append("[+] Potential\n")
        out.append("[ ] Scope: %s\n" % Variable.get_names_string(self.scope))

        for valuation in Variable.domains_product(self.scope):
            out.append("[ ] %10s | " % ','.join(map(str, valuation)))
            out.append("[ ] %-.4f\n" % self[valuation])
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
            cnstnt_val = Variable.get_consistent_valuation(var_names, values)
            if cnstnt_val:
                value = self.evaluate(cnstnt_val)*himself.evaluate(cnstnt_val)
                product[values] = value

        return product

    def __mod__(self, variable):
        var_name = variable.name

        elim_vars = [v for v in self.scope if v.name != var_name]
        elim_func = Potential(elim_vars)

        elim_var_names = Variable.get_names(elim_func.scope)

        # factor = 1/len(variable.domain)

        for elim_vals in Variable.domains_product(elim_func.variables):
            consist_val = Variable.get_consistent_valuation(elim_var_names,
                                                            elim_vals)
            if consist_val:
                sum_ = 0
                for value in variable.domain:
                    consist_val[var_name] = value
                    sum_ += self.evaluate(consist_val)
                elim_func[elim_vals] = sum_  # *factor

        return elim_func

    def __truediv__(self, probab):
        quotient = Potential(self.scope_set | himself.scope_set)

        var_names = Variable.get_names(quotient.scope)
        for values in Variable.domains_product(quotient.scope):
            cnstnt_val = Variable.get_consistent_valuation(var_names, values)
            if cnstnt_val:
                value = self.evaluate(cnstnt_val)/himself.evaluate(cnstnt_val)
                quotient[values] = value

        return quotient

    def normalize(self):
        total = sum(self.values.values())

        for k, v in self.values.items():
            self.values[k] = v/total

    def combine(potentials):
        if len(potentials) == 1:
            return potentials.pop()
        else:
            return potentials.pop() * product(potentials)

    def variable_elimination(potentials, variables):
        for variable in variables:
            dependent = []
            for potential in potentials:
                if variable in potential:
                    potentials.remove(porential)
                    dependent.append(dependent)
            combined = Porentials.combine(dependent_potentials)
            potentials.append(combined % variable)

        return Potential.product(potentials)

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
