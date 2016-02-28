
class Variable:

    def __init__(self, name, dimension):
        self.name = name
        self.dimension = dimension

    def get_valuation(variables, values):
        return zip(variables, values)


class Distribution:

    def __init__(self, variables, probabilities):
        """ {
                (0,0,0): 0.75,
                (0,0,1): 0.25,
            }
        """
        self.variables = variables
        self.probabilities = probabilities

    def query_probability(self, expression):
        total_probability = 0

        for values, probability in self.probabilities.items():
            valuation = Variable.get_valuation(self.variables, values)
            if expression.evaluate(valuation):
                total_probability += probability

        return total_probability


class Expression:

    def __init__(self, str_expression):
        self.str_expression = str_expression
        self.expression_stack = []

    def get_stack(self):
        import pyparsing as pp

        def _push_to_stack(string, loc, tokens):
            self.expression_stack.append(tokens.asList())

        VAR = pp.Word(pp.alphanums)
        VAL = pp.Word(pp.alphanums)
        SET = pp.Literal('=').suppress()

        OR = pp.CaselessLiteral('or')
        AND = pp.CaselessLiteral('and')
        NOT = pp.CaselessLiteral('not')

        BOP = AND | OR

        LPAR = pp.Literal('(').suppress()
        RPAR = pp.Literal(')').suppress()

        SENT = pp.Forward()
        ASSRT_SENT = LPAR + VAR + SET + VAL + RPAR
        BOP_SENT = LPAR + SENT.suppress() + BOP + SENT.suppress() + RPAR
        NOT_SENT = LPAR + NOT + SENT.suppress() + RPAR
        SENT << (BOP_SENT.setParseAction(_push_to_stack) |
                 ASSRT_SENT.setParseAction(_push_to_stack) |
                 NOT_SENT.setParseAction(_push_to_stack))

        SENT.parseString(self.str_expression)


if __name__ == "__main__":
    pass
