import json

import numpy as np
import pytest

from possession_lab.explorer_api import scenario, observability, run_json, describe_batch
from possession_lab.models import hmm
from possession_lab.features import extract
from possession_lab.synthetic import SyntheticConfig, generate


def test_explorer_predictions_match_existing_models():
    data = scenario({"gap_duration": 0})
    match = generate(SyntheticConfig(), 101)
    original = "".join(hmm(extract(match.tracking)))
    assert next(m["labels"] for m in data["models"] if m["id"] == "hmm") == original
    assert len(data["models"]) == 14
    assert all(len(m["labels"]) == data["frames"] for m in data["models"])


def test_missing_ball_intervention_does_not_change_truth():
    a, b = scenario({"gap_duration": 0}), scenario({"gap_duration": 7})
    assert a["truth"] == b["truth"]
    assert b["tracking"]["ball"][12 * 25:19 * 25] == [[None, None]] * (7 * 25)
    assert json.loads(run_json("scenario", '{"gap_duration":0}'))["truth"] == a["truth"]


def test_unlabelled_public_data_never_has_accuracy(controlled_batch):
    data = describe_batch(controlled_batch, None, "Unlabelled public demonstration")
    assert data["truth"] is None
    assert all(m["metrics"] is None for m in data["models"])


@pytest.mark.parametrize("evidence", ["none", "null", "independent"])
def test_observability_inputs_identical_and_null_cannot_resolve(evidence):
    data = observability({"evidence": evidence})
    assert data["identical_tracking"]
    assert data["worlds"][0]["truth"] != data["worlds"][1]["truth"]
    if evidence != "independent":
        assert all(row["balanced_target_accuracy"] <= 0.5 for row in data["summary"])


@pytest.mark.parametrize("parameters", [{"seed": 0}, {"noise": 99}, {"loss": float("nan")},
                                     {"mechanism": "restricted"}, {"path": "/private/file"}])
def test_api_accepts_no_paths_or_unbounded_inputs(parameters):
    with pytest.raises(ValueError):
        scenario(parameters)
