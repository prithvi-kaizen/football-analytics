from dataclasses import asdict

import numpy as np
import pytest

from possession_lab.features import extract
from possession_lab.hierarchical import HierarchicalConfig
from possession_lab.phase1_experiments import methods
from possession_lab.synthetic_trials import SCENARIOS, ambiguous_pair, generate_trial


@pytest.mark.parametrize("kind", ["static", "invisible"])
def test_counterexamples_share_entire_observation_sequence(kind):
    live, dead = ambiguous_pair(kind, 19)
    assert live.tracking is dead.tracking
    assert not np.array_equal(live.truth, dead.truth)
    assert set(live.truth[live.target]) == {"H"}
    assert set(dead.truth[dead.target]) == {"D"}
    f = extract(live.tracking)
    for runner in methods(asdict(HierarchicalConfig())).values():
        result = runner(f)
        labels = result.labels if hasattr(result, "labels") else result
        live_acc = (labels[live.target] == live.truth[live.target]).mean()
        dead_acc = (labels[dead.target] == dead.truth[dead.target]).mean()
        assert live_acc + dead_acc <= 1 + 1e-12


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_trial_reproduction_and_label_contract(scenario):
    a, b = generate_trial(scenario, 71), generate_trial(scenario, 71)
    np.testing.assert_array_equal(a.tracking.ball, b.tracking.ball)
    np.testing.assert_array_equal(a.truth, b.truth)
    assert set(a.truth) <= set("HADX")
    assert set(a.truth[a.tracking.period == 0]) <= {"X"}


def test_schedules_vary_and_mechanisms_are_structural():
    a, b = generate_trial("iid", 32), generate_trial("iid", 33)
    assert a.description["schedule"] != b.description["schedule"]
    burst = generate_trial("bursty", 32)
    np.testing.assert_array_equal(a.truth, burst.truth)
    # Mechanism comparison holds latent schedule fixed while changing visibility process.
    assert not np.array_equal(np.isnan(a.tracking.ball), np.isnan(burst.tracking.ball))
    hidden = generate_trial("invisible_stoppages", 32)
    assert np.isnan(hidden.tracking.ball[hidden.truth == "D"]).all()


def test_unknown_scenario_rejected():
    with pytest.raises(ValueError):
        generate_trial("competition_game", 7)
