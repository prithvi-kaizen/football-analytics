from dataclasses import replace

import numpy as np
import pytest

from possession_lab.features import extract
from possession_lab.schema import blocks, periods_from_inclusive, to_metres


def test_physical_dimensions():
    np.testing.assert_allclose(to_metres([[0.5, 0.5], [1, 1]], (105.3, 68)),
                               [[52.65, 34], [105.3, 68]])


def test_scale_preserves_nan_and_off_pitch():
    xy = to_metres([[np.nan, 0.5], [1.1, -0.1]], (100, 60))
    assert np.isnan(xy[0, 0])
    np.testing.assert_allclose(xy[1], [110, -6])


@pytest.mark.parametrize("pitch,convention", [((0, 68), "unit"), ((105, np.nan), "unit"),
                                               ((105, 68), "guess")])
def test_invalid_normalization(pitch, convention):
    with pytest.raises(ValueError):
        to_metres([[1, 1]], pitch, convention)


def test_anisotropic_nearest(controlled_batch):
    b = controlled_batch
    ball = np.tile([0.5, 0.5], (300, 1))
    home = np.tile([0.53, 0.5], (300, 2, 1))
    away = np.tile([0.5, 0.54], (300, 2, 1))
    b = replace(b, ball=to_metres(ball, (105, 68)), home=to_metres(home, (105, 68)),
                away=to_metres(away, (105, 68)))
    f = extract(b)
    assert f.nearest_team[0] == "A"
    assert f.nearest_home_m[0] == pytest.approx(3.15)
    assert f.nearest_away_m[0] == pytest.approx(2.72)


@pytest.mark.parametrize("field,value", [("frame", np.arange(300) + 1),
    ("frame", np.arange(300, dtype=float)), ("time_s", np.zeros(300)),
    ("period", np.ones(300, dtype=float)), ("fps", 0), ("pitch", (-1, 68)),
    ("provenance", {"kind": "restricted"}), ("ball", np.zeros((300, 3)))])
def test_batch_rejects_invalid_axis(controlled_batch, field, value):
    with pytest.raises(ValueError):
        replace(controlled_batch, **{field: value})


def test_nan_masks_and_infinity(controlled_batch):
    ball = controlled_batch.ball.copy()
    ball[30:50] = np.nan
    ball[60, 0] = np.nan
    home = controlled_batch.home.copy()
    home[70] = np.nan
    f = extract(replace(controlled_batch, ball=ball, home=home))
    assert not f.ball_observed[30:50].any()
    assert not f.ball_observed[60]
    assert np.isnan(f.nearest_home_m[70])
    assert f.reliability[70] == 0
    assert np.isnan(f.ball_speed_mps[30:50]).all()
    assert f.observation_age_s[45] == pytest.approx(16 / 25)
    ball[0] = np.inf
    with pytest.raises(ValueError):
        replace(controlled_batch, ball=ball)


def test_period_resets_motion_and_missing_age(controlled_batch):
    p = np.r_[np.ones(100, int), np.zeros(100, int), np.full(100, 2)]
    ball = controlled_batch.ball.copy()
    ball[200:220] = np.nan
    f = extract(replace(controlled_batch, period=p, ball=ball))
    assert blocks(p) == [(0, 100), (200, 300)]
    assert np.isnan(f.ball_speed_mps[200:210]).all()
    assert np.isinf(f.observation_age_s[200:220]).all()
    p[-1] = 1
    with pytest.raises(ValueError):
        replace(controlled_batch, period=p)


def test_input_not_mutated(controlled_batch):
    ball = controlled_batch.ball.copy()
    home = controlled_batch.home.copy()
    extract(controlled_batch)
    np.testing.assert_array_equal(controlled_batch.ball, ball)
    np.testing.assert_array_equal(controlled_batch.home, home)


def test_published_period_endpoints_are_inclusive():
    p = periods_from_inclusive(199319, [(1, 11185, 90651), (2, 110808, 190197)])
    assert p[11184] == p[90652] == p[110807] == p[190198] == 0
    assert p[11185] == p[90651] == 1
    assert p[110808] == p[113741] == p[113742] == p[190197] == 2
    assert (p > 0).sum() == 158857


@pytest.mark.parametrize("ranges", [[(1, -1, 10)], [(1, 10, 9)], [(0, 0, 2)],
                                     [(1, 0, 10), (2, 10, 20)], [(1, 0, 5), (1, 8, 10)]])
def test_bad_period_ranges(ranges):
    with pytest.raises(ValueError):
        periods_from_inclusive(30, ranges)
