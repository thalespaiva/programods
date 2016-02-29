
class Variable:

    def __init__(self, name, dimension):
        self.name = name
        self.dimension = dimension

    def get_valuation(variables, values):
        return dict(zip([var.name for var in variables], values))

    def __str__(self):
        return self.name


class Distribution:

    def __init__(self, variables, probabilities):
        """ {
                (0,0,0): 0.75,
                (0,0,1): 0.25,
            }
        """
        self.variables = variables  # tuple
        self.probabilities = probabilities  # dict

    def init_from_file(input_file_path):
        import re

        variables_list = []
        probabilities = {}

        var_regex = re.compile(r'var *([a-zA-Z0-9]*) */ *([0-9])*')

        str_varvals_regex = r' *(\([^, ] *(?:,[^, ] *)*\)) *'
        str_probvals_regex = r' *([0-9]\.?(?:[0-9]*))'
        prob_regex = re.compile(str_varvals_regex + ':' + str_probvals_regex)

        input_file = open(input_file_path, 'r')

        reading_dist_flag = False
        for line in input_file:
            line = line.strip()

            if line.startswith('dist'):
                reading_dist_flag = True

            elif line.startswith('var'):
                var_name, var_dim = re.findall(var_regex, line)[0]
                variables_list.append(Variable(var_name, var_dim))

            elif reading_dist_flag:
                if line.startswith('.'):
                    reading_dist_flag = False
                    continue

                str_var_values, str_prob = re.findall(prob_regex, line)[0]
                var_values = str_var_values[1:-1].split(',')
                key = tuple([v.strip() for v in var_values])

                probabilities[key] = float(str_prob)

        return Distribution(tuple(variables_list), probabilities)

    def query_probability(self, expression):
        total_probability = 0

        if isinstance(expression, str):
            expression = Expression(expression)

        for values, probability in self.probabilities.items():
            valuation = Variable.get_valuation(self.variables, values)
            if expression.evaluate(valuation):
                print(valuation)
                total_probability += probability

        return total_probability

    # def get_conditionate_by_fixing_valuation(self, fixed_valuation):
    #     new_variables

    #     for values, probability in self.probability.items():
    #         for var, value in fixed_valuation.items():
    #             index = self.variables.index(var)
    #             if self.values[index] != value:
    #                 break

    #         else:
    #             break


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

    def _evaluate_tree(expression_tree, val):
        sent_type, sent_elements = expression_tree.sentence

        if sent_type == Expression.BINOP_SENT:
            if sent_elements[0] == Expression.OR:
                return (Expression._evaluate_tree(expression_tree[0], val) or
                        Expression._evaluate_tree(expression_tree[1], val))

            elif sent_elements[0] == Expression.AND:
                return (Expression._evaluate_tree(expression_tree[0], val) and
                        Expression._evaluate_tree(expression_tree[1], val))

        elif sent_type == Expression.NOT_SENT:
            return not Expression._evaluate_tree(expression_tree[0], val)

        elif sent_type == Expression.ASSERT_SENT:
            if val[sent_elements[0]] == sent_elements[1]:
                print(sent_elements, 'T')
                return True
            else:
                print(sent_elements, 'F')
                return False

    def evaluate(self, valuation):
        expression_tree = self.get_tree()
        return Expression._evaluate_tree(expression_tree, valuation)

    def evaluate_stack(self, valuation):
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

    def get_tree(self):
        stack = self.get_stack()
        expression_tree = ExpressionTree(sentence=stack.pop())

        def _gen_tree_from_stack(root):
            if len(stack) == 0:
                return

            sent_type, sent_elements = root.sentence

            for i in range(ExpressionTree.NUMBER_OF_CHILDREN[sent_type]):
                child = ExpressionTree(sentence=stack.pop())
                _gen_tree_from_stack(child)

                root.push_child(child)

        _gen_tree_from_stack(expression_tree)
        return expression_tree


class ExpressionTree:

    NUMBER_OF_CHILDREN = {
        Expression.BINOP_SENT: 2,
        Expression.NOT_SENT: 1,
        Expression.ASSERT_SENT: 0
    }

    def __init__(self, sentence):
        self.sentence = sentence
        self.children = []

    def __getitem__(self, key):
        return self.children[key]

    def push_child(self, child):
        return self.children.append(child)

    def pop_child(self):
        return self.children.pop()

    def __str__(self):
        n_spaces = 0

        def rec__str__(tree, n_spaces):
            out = ' '*n_spaces + str(tree.sentence[1])
            out += ' << ' + tree.sentence[0]

            n_spaces += 2
            for child in tree.children:
                out += '\n' + rec__str__(child, n_spaces)
            n_spaces -= 2

            return out

        return rec__str__(self, n_spaces)

sent = "((Sensore=0) or (Sensor2=3))"
e1 = Expression("((not((X=3) or ((Y=3) and (not(Z=3))))) and (W=3))")
e2 = Expression("((Y=3) and (not(Z=3)))")
e3 = Expression("((X=3) or ((Y=3) and (Z=4)))")
e9 = Expression("((X=3) or (Y=4))")
e4 = Expression("(not((X=3) or ((Y=3) and (not(Z=3)))))")

valuation = {'X': '2', 'Y': '3', 'Z': '3', 'W': '3'}

e5 = Expression("((not(S=1)) or (T=3))")
e6 = Expression("((not(S=0)) and (T=0))")

e1.get_stack()

d = Distribution.init_from_file('examples/alarm.model')
d.query_probability('((Temp=1) or ((Sensor1=1) and (Sensor2=0)))')
