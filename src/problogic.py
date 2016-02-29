#!/usr/bin/python3


class Variable:

    def __init__(self, name, cardinality):
        self.name = name
        self.cardinality = cardinality

    def get_valuation(variables, values):
        return dict(zip([var.name for var in variables], values))

    def __str__(self):
        return self.name


class Distribution:

    def __init__(self, variables, probabilities):
        # { (0,0,0): 0.75, (0,0,1): 0.25, }
        self.variables = variables  # tuple
        self.probabilities = probabilities  # dict

    def init_from_file(input_file_path):
        import re

        variables_list = []
        probabilities = {}

        str_varvals_regex = r' *(\([^,]*(?:,[^,]*)*\)) *'
        str_probvals_regex = r' *([0-9]\.?(?:[0-9]*))'
        var_regex = re.compile(r'var *([a-zA-Z0-9]*) */ *([0-9])*')
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
                total_probability += probability

        return total_probability

    def query_independence(self, this, that):
        prob = self.query_probability(this)
        prob_cond = self.query_conditional_probability(this, that)

        return prob == prob_cond

    def query_conditional_probability(self, expression, condition):
        # Gaaaambiarra !
        exp_and_cond = '(' + expression + ' and ' + condition + ')'

        prob_intersection = self.query_probability(exp_and_cond)
        prob_condition = self.query_probability(condition)

        return prob_intersection/prob_condition

    def query_cond_independence(this, that, cond):
        inter_cond = '(' + expression + ' and ' + condition + ')'
        prob_cond = self.query_conditional_probability()


class Expression:

    BINOP_SENT = 'BINOP'
    ASSERT_SENT = 'ASSERT'
    NOT_SENT = 'NOT'

    OR = 'or'
    AND = 'and'
    NOT = 'not'

    def __init__(self, str_expression):
        self.str_expression = str_expression

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
                return True
            else:
                return False

    def evaluate(self, valuation):
        expression_tree = self.get_tree()
        return Expression._evaluate_tree(expression_tree, valuation)

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


class Query:

    PROB_TYPE = 'prob'
    COND_TYPE = 'cond'
    INDEP_TYPE = 'indep'
    CONDIND_TYPE = 'condind'

    import re

    prob_regex = re.compile(PROB_TYPE + r'([^\.]*)\.')
    cond_regex = re.compile(COND_TYPE + r'([^\|]*)\|([^\.]*)\.')
    indep_regex = re.compile(INDEP_TYPE + r'([^,]*),([^\?]*)\?')
    condind_regex = re.compile(CONDIND_TYPE + r'([^,]*),([^\|]*)\|([^\?]*)\?')

    def resolve_prob_query(line, model):
        query = re.findall(Query.prob_regex, line)[0]
        query = query.strip()

        print(' %.5f = Prob( %s )' % (model.query_probability(query), query))

    def resolve_cond_query(line, model):
        query, cond = re.findall(Query.cond_regex, line)[0]
        query, cond = query.strip(), cond.strip()

        prob = model.query_conditional_probability(query, cond)
        print(' %.5f = Prob( %s | %s )' % (prob, query, cond))

    def resolve_indep_query(line, model):
        this, that = re.findall(Query.indep_regex, line)[0]
        this, that = this.strip(), that.strip()

        indep = model.query_independence(this, that)
        print(' %-7r = is %s indep %s ?' % (indep, this, that))

    def resolve_condindep_query(line, model):
        this, that, cond = re.findall(Query.indep_regex, line)[0]
        this, that, cond = this.strip(), that.strip(), cond.strip()

        indep = model.query_cond_independence(this, that, cond)
        print(' %-7r = is %s indep %s | %s ?' % (indep, this, that, cond))

    def resolve_str_query(line, model):
        if line.startswith(Query.PROB_TYPE):
            return Query.resolve_prob_query(line, model)
        elif line.startswith(Query.COND_TYPE):
            return Query.resolve_cond_query(line, model)
        elif line.startswith(Query.INDEP_TYPE):
            return Query.resolve_indep_query(line, model)
        elif line.startswith(Query.CONDIND_TYPE):
            return Query.resolve_condindep_query(line, model)


if __name__ == "__main__":
    import sys
    import re

    LABEL_MARK = '['

    if len(sys.argv) != 3:
        print("Usage: %s <model_file> <queries_file>" % sys.argv[0])
        sys.exit(1)

    model_file_name = sys.argv[1]
    queries_file_name = sys.argv[2]

    model = Distribution.init_from_file(model_file_name)
    queries_file = open(queries_file_name, 'r')

    for line in queries_file:
        line = line.strip()

        if line.startswith(LABEL_MARK):
            print(line)
        Query.resolve_str_query(line, model)
