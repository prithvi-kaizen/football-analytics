"""Real-data integration tests read local verified caches; no network in pytest."""

import hashlib
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from passlab.choices import evaluate_candidates
from passlab.data import Cache
from passlab.features import eligible, extract_match, outcome_label
from passlab.models import predict_bundle

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path(os.environ.get("PASSLAB_TEST_OUTPUT", ROOT / "outputs"))


@pytest.fixture
def output():
    if not (OUTPUT / "provenance.json").exists():
        pytest.skip("Run the real-data pipeline first (see README)")
    return OUTPUT


@pytest.mark.integration
def test_real_pass_counts_joins_and_labels(output):
    provenance = json.loads((output / "provenance.json").read_text())
    match = provenance["matches"][0]
    cache = Cache(ROOT / "data/raw", offline=True)
    events = cache.get(f"data/events/{match['match_id']}.json")
    frames = cache.get(f"data/three-sixty/{match['match_id']}.json")
    rows, scenes, audit = extract_match(match, events, frames)
    actual = pd.read_csv(output / "passes.csv")
    actual = actual[actual.match_id == match["match_id"]]
    expected = [e for e in events if eligible(e) and outcome_label(e) is not None]
    assert len(expected) == len(rows) == len(actual)
    assert actual.event_id.is_unique
    assert set(actual.event_id) == {e["id"] for e in expected}
    by_id = {e["id"]: e for e in events}
    assert actual.complete.sum() == sum("outcome" not in e["pass"] for e in expected)
    framed = {f["event_uuid"] for f in frames}
    assert set(actual[actual.has_frame].event_id) == set(actual.event_id) & framed
    for row in rows:
        assert row["seconds"] >= 0
        assert row["start_x"] == by_id[row["event_id"]]["location"][0]
        if row["has_target"]:
            assert 0 < row["history_age"] <= 5
            assert row["history_distance"] <= 3
    assert not audit["orphan_frames"]


@pytest.mark.integration
def test_real_split_inference_support_and_hashes(output):
    df = pd.read_csv(output / "passes.csv")
    pred = pd.read_csv(output / "predictions.csv")
    bundles = json.loads((output / "model-bundles.json").read_text())
    provenance = json.loads((output / "provenance.json").read_text())
    split = provenance["split"]
    assert set(df.partition) == {"train", "test"}
    assert not set(split["train"]) & set(split["test"])
    assert set(pred.match_id) <= set(split["test"])
    assert set(df.match_id) == set(split["train"]) | set(split["test"])
    for name in ["passes.csv", "scenes.json", "metrics.csv", "model-bundles.json"]:
        assert hashlib.sha256((output / name).read_bytes()).hexdigest() == provenance["output_hashes"][name]
    for feature_set, bundle in bundles.items():
        assert set(bundle["training_matches"]) <= set(split["train"])
        observed = pred[pred.model_id.str.endswith(f"/logistic/{feature_set}")]
        features = df.set_index("event_id").loc[observed.event_id]
        np.testing.assert_allclose(predict_bundle(bundle, features), observed.probability, atol=1e-12)
    for population in pred.population.unique():
        ids = [set(g.event_id) for _, g in pred[pred.population == population].groupby("model_id")]
        assert all(x == ids[0] for x in ids)
    scenes = json.loads((output / "scenes.json").read_text())
    for _, row in df[df.partition == "test"].head(30).iterrows():
        if row.event_id not in scenes:
            continue
        candidates = evaluate_candidates(row.to_dict(), scenes[row.event_id], bundles.get("target_360"))
        if len(candidates):
            assert candidates.loc[~candidates.supported, "xpass"].isna().all()
            assert candidates.loc[candidates.supported, "xpass"].between(0, 1).all()
            assert candidates.loc[candidates.review_flag, "forward_gain"].ge(10).all()
