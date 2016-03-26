
from ..distribution import Variable


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
