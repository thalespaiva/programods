
from ..distribution import Variable
from ..distribution import Potential

FLOAT_ERROR = 1e-10


def assert_almost_equals(a, b):
    assert abs(a - b) < FLOAT_ERROR


class TestVariable:

    def test_get_consistent_valuation_X_1_Y_3(self):
        X = Variable('X', range(2))
        Y = Variable('Y', range(4))

        valuation = Variable.get_consistent_valuation([X, Y], [1, 3])
        assert valuation == {'X': 1, 'Y': 3}

    def test_get_consistent_valuation_for_inconsistent_valuation(self):
        X = Variable('X', range(2))
        Y = Variable('Y', range(4))

        valuation = Variable.get_consistent_valuation([X, Y, X], [1, 3, 0])
        assert valuation is None

    def test_cardinality(self):
        X = Variable('X', 8)
        Y = Variable('Y', [1, 2, 4])

        assert X.cardinality == 8
        assert Y.cardinality == 3


class TestPotential:

    def test_evaluate(self):
        A = Variable('A', 3)
        values = {(1,): 0.3, (2,): 0.6, (3,): 0.1}

        d = Potential([A], values)
        assert_almost_equals(d.evaluate({A.name: 1}), 0.3)
        assert_almost_equals(d.evaluate({A.name: 2}), 0.6)
        assert_almost_equals(d.evaluate({A.name: 3}), 0.1)

    def test_product(self):
        A = Variable('A', 2)
        B = Variable('B', 2)

        values1 = {(0,): 0.4, (1,): 0.6}
        values2 = {(0, 0): 0.7, (0, 1): 0.2, (1, 0): 0.3, (1, 1): 0.8}

        d1 = Potential([A], values1)
        d2 = Potential([B, A], values2)

        p = d1 * d2
        assert_almost_equals(p.evaluate({'A': 0, 'B': 0}), 0.28)
        assert_almost_equals(p.evaluate({'A': 0, 'B': 1}), 0.12)
        assert_almost_equals(p.evaluate({'A': 1, 'B': 0}), 0.12)
        assert_almost_equals(p.evaluate({'A': 1, 'B': 1}), 0.48)

    def test_variable_elimination(self):
        A = Variable('A', 2)
        B = Variable('B', 2)

        values1 = {(0,): 0.1, (1,): 0.9}  # A
        values2 = {(0, 0): 0.7, (0, 1): 0.2, (1, 0): 0.3, (1, 1): 0.8}  # B A

        d1 = Potential([A], values1)
        d2 = Potential([B, A], values2)
        d3 = (d1*d2) % A

        assert_almost_equals(d3.evaluate({'B': 0}), 0.25)
        assert_almost_equals(d3.evaluate({'B': 1}), 0.75)
