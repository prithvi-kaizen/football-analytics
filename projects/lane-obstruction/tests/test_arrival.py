import json
from pathlib import Path
import unittest
import numpy as np
from lane_obstruction.arrival import arrival_obstruction
from lane_obstruction.baseline import marginal_obstruction
from lane_obstruction.evaluation import spearman

CFG = json.loads((Path(__file__).resolve().parents[1]/'configs/pilot.json').read_text())


class ArrivalTests(unittest.TestCase):
    def test_slower_ball_gives_defender_more_time(self):
        args = ([0, 0], [[30, 0]], [[15, 7]], [[0, 0]])
        slow, _ = arrival_obstruction(*args, dict(CFG, ball_speed_mps=12))
        fast, _ = arrival_obstruction(*args, dict(CFG, ball_speed_mps=18))
        self.assertGreater(slow[0, 0], fast[0, 0])

    def test_towards_lane_velocity_matters(self):
        towards, _ = arrival_obstruction([0, 0], [[30, 0]], [[15, 7]], [[0, -3]], CFG)
        away, _ = arrival_obstruction([0, 0], [[30, 0]], [[15, 7]], [[0, 3]], CFG)
        self.assertGreater(towards[0, 0], away[0, 0])

    def test_already_on_route_is_immediately_reachable(self):
        score, margin = arrival_obstruction([0, 0], [[20, 0]], [[10, 0]], [[0, 0]], CFG)
        self.assertGreater(margin[0, 0], .6)
        self.assertGreater(score[0, 0], .9)

    def test_marginal_nonnegative_and_permutation_invariant(self):
        m, _ = arrival_obstruction([0, 0], [[25, 0], [10, 15]], [[10, 5], [15, 2]], [[1, 2], [-1, 0]], CFG)
        team, marginal = marginal_obstruction(m)
        other, reversed_marginal = marginal_obstruction(m[:, ::-1])
        np.testing.assert_allclose(team, other)
        np.testing.assert_allclose(marginal, reversed_marginal[::-1])
        self.assertTrue((marginal >= 0).all())
        self.assertLessEqual(marginal.sum(), team.mean()+1e-12)

    def test_rank_ties_and_missingness(self):
        self.assertAlmostEqual(spearman([1, 1, 3, np.nan], [2, 2, 6, 8]), 1)
        self.assertIsNone(spearman([1, 1, 1], [1, 2, 3]))

    def test_negative_speed_rejected(self):
        with self.assertRaises(ValueError):
            arrival_obstruction([0, 0], [[20, 0]], [[10, 1]], [[0, 0]], dict(CFG, ball_speed_mps=-1))
