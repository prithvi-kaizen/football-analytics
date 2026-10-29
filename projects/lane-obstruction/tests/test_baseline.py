import unittest
import numpy as np
from lane_obstruction.baseline import corridor_obstruction, marginal_obstruction


class GeometryTests(unittest.TestCase):
    def test_known_lanes_and_flat_endpoints(self):
        m = corridor_obstruction([0, 0], [[10, 0]], [[5, .8], [5, 1.1], [-1, 0], [9, 0]])
        np.testing.assert_array_equal(m, [[True, False, False, False]])

    def test_rotation_translation_invariance(self):
        b = np.array([1., 2.]); t = np.array([[11., 2.], [6., 10.]])
        d = np.array([[5., 2.2], [7., 8.]])
        r = np.array([[0., -1.], [1., 0.]])
        np.testing.assert_array_equal(corridor_obstruction(b, t, d), corridor_obstruction(b@r+7, t@r+7, d@r+7))

    def test_shared_credit_is_not_double_counted(self):
        team, marginal = marginal_obstruction([[1, 1], [0, 1]])
        np.testing.assert_array_equal(team, [1, 1])
        np.testing.assert_allclose(marginal, [0, .5])

    def test_reject_degenerate(self):
        with self.assertRaises(ValueError):
            corridor_obstruction([0, 0], [[0, 0]], [[5, 0]])


if __name__ == '__main__':
    unittest.main()
