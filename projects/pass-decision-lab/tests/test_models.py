import numpy as np
import pandas as pd
import pytest

from passlab.choices import evaluate_candidates
from passlab.models import (
    FEATURE_SETS,
    logistic_bundle,
    make_estimator,
    predict_bundle,
    scores,
    split_matches,
    support_flags,
)


def test_match_split_stratifies_and_is_repeatable():
    df = pd.DataFrame(
        [{"match_id": i, "tournament": "A" if i < 5 else "B"} for i in range(10) for _ in range(30)]
    )
    split = split_matches(df)
    assert split == split_matches(df.sample(frac=1, random_state=1))
    assert not set(split["train"]) & set(split["test"])
    assert set(split["train"] + split["test"]) == set(range(10))
    assert {("A" if i < 5 else "B") for i in split["test"]} == {"A", "B"}
    with pytest.raises(ValueError):
        split_matches(df[df.match_id == 0])


def test_json_inference_matches_sklearn_and_train_only_scaling():
    # Numerical fixtures only, not claimed as sampled football observations.
    df = pd.DataFrame(
        {
            "start_x": [0, 10, 20, 30, 40, 50, 60, 70],
            "start_y": [20, 30, 40, 50, 20, 30, 40, 50],
            "period": [1] * 8,
            "complete": [1, 1, 0, 1, 1, 0, 1, 0],
            "match_id": [1] * 8,
        }
    )
    cols = FEATURE_SETS["event"]
    model = make_estimator("logistic").fit(df[cols], df.complete)
    bundle = logistic_bundle(model, cols, df)
    np.testing.assert_allclose(predict_bundle(bundle, df), model.predict_proba(df[cols])[:, 1])
    test = pd.DataFrame([{"start_x": 1000, "start_y": 40, "period": 1}])
    before = bundle["mean"].copy()
    predict_bundle(bundle, test)
    assert bundle["mean"] == before
    assert support_flags(bundle, test.iloc[0].to_dict())
    assert not make_estimator("boosted").steps[-1][1].early_stopping


def test_probability_metrics_known_values():
    m = scores([1, 0], [0.5, 0.5])
    assert m["brier"] == 0.25
    assert m["log_loss"] == pytest.approx(np.log(2))
    assert m["roc_auc"] == 0.5
    assert scores([1, 1], [0.8, 0.9])["roc_auc"] is None


def test_candidate_without_model_is_geometry_only():
    scene = {
        "origin": [40, 40],
        "opponents": [[45, 42]],
        "target_candidate_id": None,
        "teammates": [
            {"candidate_id": "T01", "location": [70, 40], "keeper": False, "inside_visible_area": True}
        ],
    }
    c = evaluate_candidates({"start_x": 40, "start_y": 40, "period": 1}, scene, None)
    assert c.iloc[0].forward_gain == 30
    assert c.iloc[0].xpass is None
    assert not c.iloc[0].supported
    assert not c.iloc[0].review_flag


def test_review_queue_keeps_candidate_columns_and_only_holdout(monkeypatch):
    from passlab.choices import build_review_queue

    df = pd.DataFrame(
        [
            {
                "event_id": "test",
                "match_id": 2,
                "tournament": "Fixture",
                "team": "Fixture",
                "player": "Synthetic",
                "minute": 1,
                "second": 2,
                "partition": "test",
                "has_target": True,
            },
            {"event_id": "train", "match_id": 1, "partition": "train", "has_target": True},
        ]
    )
    candidate = pd.DataFrame(
        [
            {
                "candidate_id": "T02",
                "proxy_target": False,
                "supported": True,
                "review_flag": True,
                "xpass": 0.8,
                "forward_gain": 20,
                "expected_forward_gain": 16,
            }
        ]
    )
    monkeypatch.setattr("passlab.choices.evaluate_candidates", lambda *args: candidate)
    queue, audit = build_review_queue(df, {"test": {}}, {"model": "fixture"})
    assert queue.iloc[0].candidate_id == "T02"
    assert queue.iloc[0].event_id == "test"
    assert set(queue.match_id) == {2}
    assert audit["flagged_events"] == audit["flagged_lanes"] == 1


def test_off_pitch_target_is_never_assigned_a_probability():
    scene = {
        "origin": [40, 40],
        "opponents": [[45, 42]],
        "target_candidate_id": None,
        "teammates": [
            {
                "candidate_id": "T01",
                "location": [70, -1],
                "on_pitch": False,
                "keeper": False,
                "inside_visible_area": True,
            }
        ],
    }
    # Empty feature bundle makes geometry guards vacuous; the pitch guard must still hold.
    c = evaluate_candidates(
        {"start_x": 40, "start_y": 40, "period": 1}, scene, {"features": [], "bounds": {}}
    )
    assert not c.iloc[0].supported
    assert c.iloc[0].xpass is None
    assert "target outside pitch" in c.iloc[0].support_warning
