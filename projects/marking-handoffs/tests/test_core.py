import copy
import unittest
from pathlib import Path
import json

import numpy as np

from marking_handoffs.baseline import nearest, runs
from marking_handoffs.graph import edge_features
from marking_handoffs.temporal import assign, candidate_events
from marking_handoffs.data import attack_sign

CFG = json.loads((Path(__file__).resolve().parents[1] / "configs/pilot.json").read_text())


class CoreTests(unittest.TestCase):
    def test_nearest_and_tie(self):
        np.testing.assert_array_equal(nearest(np.array([[3., 2.], [1., 1.]])), [1, 0])
        with self.assertRaises(ValueError):
            nearest(np.array([[np.nan, 1]]))

    def test_half_direction(self):
        m = dict(home_team=dict(id=1), away_team=dict(id=2), home_team_side=["right_to_left", "left_to_right"])
        self.assertEqual(attack_sign(m, 1, 1), -1)
        self.assertEqual(attack_sign(m, 2, 2), -1)
        with self.assertRaises(ValueError):
            attack_sign(m, 3, 1)

    def test_confirm_and_margin(self):
        f = dict(score=np.tile([1., 2.], (20, 1)), plausible=np.ones((20, 2), bool), retain=np.ones((20, 2), bool))
        f["score"][10:] = [2, 1]
        expected = [-1] * 4 + [0] * 10 + [1] * 6
        np.testing.assert_array_equal(assign(f, CFG), expected)
        f["score"][10:] = [1.5, 1]
        self.assertTrue(np.all(assign(f, CFG)[4:] == 0))

    def test_invalid_release_and_reset(self):
        f = dict(score=np.tile([1., 2.], (20, 1)), plausible=np.ones((20, 2), bool), retain=np.ones((20, 2), bool))
        reset = np.zeros(20, bool)
        reset[10] = True
        labels = assign(f, CFG, reset)
        self.assertTrue(np.all(labels[10:15] == -1))
        f["plausible"][10:] = False
        f["retain"][10:] = False
        self.assertTrue(np.all(assign(f, CFG)[10:] == -1))

    def test_future_cannot_change_prefix(self):
        f = dict(score=np.tile([1., 2.], (30, 1)), plausible=np.ones((30, 2), bool), retain=np.ones((30, 2), bool))
        a = assign(f, CFG)
        g = copy.deepcopy(f)
        g["score"][15:] = [10, -10]
        np.testing.assert_array_equal(assign(g, CFG)[:15], a[:15])

    def test_graph_translation_and_mirror(self):
        a = np.array([[0., 0.], [.1, .3]])
        d = np.array([[[1., 1.], [2., -2.]], [[1., 1.], [2., -2.]]])
        av, dv = np.ones_like(a), np.zeros_like(d)
        f = edge_features(a, d, av, dv, 1, CFG)
        g = edge_features(a + [8, -3], d + [8, -3], av, dv, 1, CFG)
        h = edge_features(-a, -d, -av, -dv, -1, CFG)
        for k in f:
            np.testing.assert_allclose(f[k], g[k], atol=1e-9)
            np.testing.assert_allclose(f[k], h[k], atol=1e-9)

    def test_graph_known_scalar_features_and_gates(self):
        a = np.zeros((1, 2))
        d = np.array([[[1., 0.], [3., 0.], [2., 0.]]])
        av, dv = np.zeros_like(a), np.zeros_like(d)
        dv[0, 0, 0] = 1
        f = edge_features(a, d, av, dv, 1, CFG)
        self.assertAlmostEqual(f["radial"][0, 0], 1)
        self.assertAlmostEqual(f["predicted"][0, 0], 1.4)
        self.assertAlmostEqual(f["structure"][0, 0], 2)
        self.assertAlmostEqual(f["score"][0, 0], 1 + .35 + .12 * 2)
        d[0, 0] = [-2, 0]
        f = edge_features(a, d, av, dv, 1, CFG)
        self.assertFalse(f["plausible"][0, 0])
        d[0, 0] = [7, 0]
        dv[:] = 0
        f = edge_features(a, d, av, dv, 1, CFG)
        self.assertFalse(f["plausible"][0, 0])
        self.assertTrue(f["retain"][0, 0])

    def test_gap_independent_of_unassigned_delay(self):
        labels = np.r_[np.zeros(20, int), np.full(8, -1), np.ones(20, int)]
        a = np.column_stack([np.arange(48) * .1, np.zeros(48)])
        p = np.ones((48, 2), bool)
        f = dict(plausible=p, score=np.tile([2., 3.], (48, 1)))
        e = candidate_events(labels, f, a, CFG)[0]
        self.assertEqual(e["gap_s"], 0)
        self.assertEqual(e["unassigned_s"], .8)
        p[20:28] = False
        e = candidate_events(labels, f, a, CFG)[0]
        self.assertEqual(e["longest_gap_s"], .8)
        self.assertEqual(e["category"], "gap")

    def test_same_defender_return_is_not_transfer(self):
        labels = np.r_[np.zeros(20, int), np.full(8, -1), np.zeros(20, int)]
        f = dict(plausible=np.ones((48, 2), bool), score=np.ones((48, 2)))
        a = np.column_stack([np.arange(48), np.zeros(48)])
        self.assertEqual(candidate_events(labels, f, a, CFG), [])

    def test_long_gap_not_joined(self):
        labels = np.r_[np.zeros(20, int), np.full(21, -1), np.ones(20, int)]
        f = dict(plausible=np.ones((61, 2), bool), score=np.ones((61, 2)))
        a = np.column_stack([np.arange(61), np.zeros(61)])
        self.assertEqual(candidate_events(labels, f, a, CFG), [])

    def test_empty_runs(self):
        self.assertEqual(runs([]), [])


if __name__ == "__main__":
    unittest.main()
