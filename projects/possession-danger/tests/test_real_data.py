import json
from pathlib import Path
import pandas as pd
import pytest

from possession_danger.data import Cache, catalog, digest, select_matches
from possession_danger.pipeline import run
from possession_danger.report import render_existing

ROOT = Path(__file__).parents[1]


@pytest.mark.real_data
def test_real_sample_end_to_end_offline(tmp_path):
    cache = Cache(ROOT / "data/raw", offline=True)
    if not cache.root.exists():
        pytest.skip("Download the real six-match sample first")
    selected = select_matches(catalog(cache, "liga-f"), 6)
    first = run(cache, selected, tmp_path / "first")
    second = run(cache, selected, tmp_path / "second")
    assert first == second
    assert first["checks"]["score_reconciliations"] == 6
    assert first["checks"]["active_le_elapsed"]
    assert first["checks"]["pass_count_reconciles"]
    assert first["checks"]["shot_count_reconciles"]
    assert first["checks"]["shot_xg_reconciles"]
    assert first["test_matches"] == 2
    assert first["train_matches"] == 4
    for name in ["possessions.csv", "team_matches.csv", "actions.csv", "summary.json", "possession-vs-threat.png", "possession-vs-threat.svg"]:
        assert digest(tmp_path / "first" / name) == digest(tmp_path / "second" / name)
    render_existing(tmp_path / "first")
    (tmp_path / "first" / "summary.json").write_text("{}")
    with pytest.raises(ValueError, match="Analysis output changed"):
        render_existing(tmp_path / "first")


@pytest.mark.real_data
def test_full_league_outputs_reconcile_when_present():
    out = ROOT / "outputs/liga-f"
    if not all((out / name).exists() for name in ["manifest.json", "team_matches.csv", "possessions.csv", "score_states.csv"]):
        pytest.skip("Generate the full Liga F analysis first")
    summary = json.loads((out / "summary.json").read_text())
    assert summary["matches"] == 240
    assert summary["checks"]["score_reconciliations"] == 240
    assert summary["checks"]["pass_count_reconciles"]
    assert summary["checks"]["shot_count_reconciles"]
    assert summary["checks"]["shot_xg_reconciles"]
    assert summary["train_matches"] == 192
    assert summary["test_matches"] == 48
    totals = pd.read_csv(out / "team_matches.csv")
    assert totals.groupby("match_id").size().eq(2).all()
    for metric in ["possession_pct", "field_tilt", "threat_share"]:
        assert (totals.groupby("match_id")[metric].sum() - 100).abs().max() < 1e-8
    seq = pd.read_csv(out / "possessions.csv")
    assert abs(seq.positive_xt.sum() - totals.positive_xt.sum()) < 1e-8
    states = pd.read_csv(out / "score_states.csv")
    assert abs(states.positive_xt.sum() - totals.positive_xt.sum()) < 1e-8
    assert abs(states.active_seconds.sum() - totals.active_seconds.sum()) < 1e-6


def test_failed_build_preserves_previous_verified_output(tmp_path, monkeypatch):
    from possession_danger import pipeline
    output = tmp_path / "analysis"
    output.mkdir()
    (output / "manifest.json").write_text("previous verified build")
    def fail(cache, matches, staging, sample):
        (staging / "team_matches.csv").write_text("incomplete")
        raise ValueError("Fixture validation failed")
    monkeypatch.setattr(pipeline, "_run", fail)
    with pytest.raises(ValueError, match="Fixture validation"):
        pipeline.run(None, [], output)
    assert (output / "manifest.json").read_text() == "previous verified build"
    assert not (output / "team_matches.csv").exists()
    assert not list(tmp_path.glob(".possession-build-*"))
