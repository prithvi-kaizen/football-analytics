import numpy as np
import pandas as pd
import pytest

from possession_lab.official import metrics_module
from possession_lab.phase1_metrics import boundary_errors, paired_deltas, summarise_trials


def test_boundary_errors_have_known_offset():
    pm = metrics_module()
    gt = pm.label_codes(["H"] * 50 + ["A"] * 50 + ["D"] * 50)
    pred = pm.label_codes(["H"] * 54 + ["A"] * 50 + ["D"] * 46)
    result = boundary_errors(pm, gt, pred)
    assert result["boundary_matched"] == 3
    assert result["boundary_mae_frames"] == 4
    assert result["boundary_missed"] == result["boundary_spurious"] == 0


def test_boundary_types_and_halves_cannot_cross_match():
    pm = metrics_module()
    gt = pm.label_codes(["H"] * 5 + ["A"] * 5 + ["X"] + ["H"] * 5 + ["A"] * 5)
    pred = pm.label_codes(["H"] * 10 + ["X"] + ["A"] * 10)
    scores = boundary_errors(pm, gt, pred)
    assert scores["boundary_matched"] == 0
    assert scores["boundary_missed"] == 4
    assert scores["boundary_mae_frames"] is None


def test_whole_trial_bootstrap_is_reproducible_and_preserves_undefined():
    table = pd.DataFrame({"scenario": ["s"] * 3, "method": ["m"] * 3,
                          "trial": [1, 2, 3], "score": [0., 0.5, 1.], "undefined": [np.nan] * 3})
    a = summarise_trials(table, ["score", "undefined"], draws=100)
    b = summarise_trials(table, ["score", "undefined"], draws=100)
    pd.testing.assert_frame_equal(a, b)
    assert a.iloc[0]["mean"] == pytest.approx(0.5)
    assert a.iloc[0].low <= 0.5 <= a.iloc[0].high
    assert a.iloc[1].defined_trials == 0
    assert np.isnan(a.iloc[1]["mean"])


def test_bootstrap_pairs_methods_instead_of_unpaired_resampling():
    base = pd.DataFrame({"scenario": ["s"] * 3, "method": ["hierarchical"] * 3,
                          "trial": [1, 2, 3], "score": [0.1, 0.5, 0.8]})
    other = base.assign(method="ablation", score=base.score + 0.1)
    result = paired_deltas(pd.concat([base, other]), ["score"], draws=100)
    np.testing.assert_allclose(result[["mean", "low", "high"]], 0.1)
