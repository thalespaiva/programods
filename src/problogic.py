
class Variable:

    def __init__(self, name, dimension):
        self.name = name
        self.dimension = dimension

    def get_valuation(variables, values):
        return dict(zip(variables, values))


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

    BINOP_SENT = 'BINOP'
    ASSERT_SENT = 'ASSERT'
    NOT_SENT = 'NOT'

    OR = 'or'
    AND = 'and'
    NOT = 'not'

    def __init__(self, str_expression):
        self.str_expression = str_expression

    def _evaluate_and_sentence(stack, valuation):
        left_side = Expression._evaluate_stack(stack, valuation)
        right_side = Expression._evaluate_stack(stack, valuation)

        return left_side and right_side

    def _evaluate_or_sentence(stack, valuation):
        left_side = Expression._evaluate_stack(stack, valuation)
        right_side = Expression._evaluate_stack(stack, valuation)

        return left_side or right_side

    def _evaluate_not_sentence(stack, valuation):
        return not Expression._evaluate_stack(stack, valuation)

    def _evaluate_stack(stack, valuation):
        sent_type, sent_elements = stack.pop()

        if sent_type == Expression.BINOP_SENT:
            if sent_elements[0] == Expression.OR:
                return Expression._evaluate_or_sentence(stack, valuation)

            elif sent_elements[0] == Expression.AND:
                return Expression._evaluate_and_sentence(stack, valuation)

        elif sent_type == Expression.NOT_SENT:
            return Expression._evaluate_not_sentence(stack, valuation)

        elif sent_type == Expression.ASSERT_SENT:
            if valuation[sent_elements[0]] == sent_elements[1]:
                print(sent_elements, 'T')
                return True
            else:
                print(sent_elements, 'F')
                return False

    def evaluate(self, valuation):
        expression_stack = self.get_stack()

        return Expression._evaluate_stack(expression_stack, valuation)

    def get_stack(self):
        import pyparsing as pp

        expression_stack = []

        def _push_with_sent_type(sent_type):

            def _push_to_stack(string, loc, tokens):
                expression_stack.append((sent_type, tokens.asList()))

            return _push_to_stack

        var = pp.Word(pp.alphanums)
        val = pp.Word(pp.alphanums)
        eq = pp.Literal('=').suppress()

        tk_or = pp.CaselessLiteral(Expression.OR)
        tk_and = pp.CaselessLiteral(Expression.AND)
        tk_not = pp.CaselessLiteral(Expression.NOT)

        bop = tk_and | tk_or

        lpar = pp.Literal('(').suppress()
        rpar = pp.Literal(')').suppress()

        sent = pp.Forward()
        assrt_sent = lpar + var + eq + val + rpar
        bop_sent = lpar + sent.suppress() + bop + sent.suppress() + rpar
        not_sent = lpar + tk_not + sent.suppress() + rpar

        bop_sent.setParseAction(_push_with_sent_type(Expression.BINOP_SENT))
        assrt_sent.setParseAction(_push_with_sent_type(Expression.ASSERT_SENT))
        not_sent.setParseAction(_push_with_sent_type(Expression.NOT_SENT))

        sent << (bop_sent | assrt_sent | not_sent)
        sent.parseString(self.str_expression)

        return expression_stack


sent = "((Sensore=0) or (Sensor2=3))"
e1 = Expression("((not((X=3) or ((Y=3) and (not(Z=3))))) and (W=3))")
e2 = Expression("((Y=3) and (not(Z=3)))")
e3 = Expression("((X=3) or ((Y=3) and (Z=4)))")
e9 = Expression("((X=3) or (Y=4))")
e4 = Expression("(not((X=3) or ((Y=3) and (not(Z=3)))))")

valuation = {'X':'2', 'Y':'3', 'Z':'3', 'W':'3'}

e5 = Expression("((not(S=1)) or (T=3))")
e6 = Expression("((not(S=0)) and (T=0))")

e1.get_stack()
