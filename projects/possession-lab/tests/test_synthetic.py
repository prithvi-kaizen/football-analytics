from dataclasses import replace

import numpy as np
import pytest

from possession_lab.features import extract
from possession_lab.pipeline import infer
from possession_lab.synthetic import SyntheticConfig, generate


def test_reproducible_truth_and_observations():
    c = SyntheticConfig(contested=True, gap_seconds=2, identity_switches=True)
    a, b = generate(c, 123), generate(c, 123)
    np.testing.assert_array_equal(a.truth, b.truth)
    np.testing.assert_array_equal(a.tracking.ball, b.tracking.ball)
    np.testing.assert_array_equal(a.tracking.home, b.tracking.home)
    assert not np.array_equal(a.tracking.ball, generate(c, 124).tracking.ball, equal_nan=True)
    assert set(a.truth) == set("HADX")
    assert set(a.truth[a.tracking.period == 0]) == {"X"}


def test_identity_switch_preserves_collective_geometry():
    clean = SyntheticConfig(noise_m=0, player_gap_rate=0, occlusion_rate=0)
    a = generate(clean, 23).tracking
    b = generate(replace(clean, identity_switches=True), 23).tracking
    fa, fb = extract(a), extract(b)
    np.testing.assert_allclose(fa.nearest_home_m, fb.nearest_home_m, equal_nan=True)
    np.testing.assert_allclose(fa.nearest_away_m, fb.nearest_away_m, equal_nan=True)


def test_occlusion_does_not_change_latent_truth():
    a = generate(SyntheticConfig(occlusion_rate=0, gap_seconds=0))
    b = generate(SyntheticConfig(occlusion_rate=1, gap_seconds=2))
    np.testing.assert_array_equal(a.truth, b.truth)
    assert np.isnan(b.tracking.ball).all()
    assert set(infer(b.tracking).labels) == {"X"}


def test_contests_leave_truth_with_owner():
    match = generate(SyntheticConfig(contested=True))
    assert match.diagnostics["contested"].any()
    assert set(match.truth[match.diagnostics["contested"]]) <= {"H", "A"}


def test_stoppage_control():
    assert "D" not in generate(SyntheticConfig(stoppages=False)).truth
    match = generate(SyntheticConfig(invisible_stoppages=True))
    assert np.isnan(match.tracking.ball[match.truth == "D"]).all()


@pytest.mark.parametrize("kwargs", [{"fps": 30}, {"gap_seconds": -2}, {"occlusion_rate": 1.1},
                                     {"player_gap_rate": -1}, {"noise_m": np.nan}])
def test_generator_validation(kwargs):
    with pytest.raises(ValueError):
        SyntheticConfig(**kwargs)
