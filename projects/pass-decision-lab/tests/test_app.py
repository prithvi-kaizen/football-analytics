"""Streamlit rerun and selection tests use a previously generated real-data run."""

import json
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "outputs/smoke"


@pytest.mark.integration
def test_empty_app_has_setup_state(tmp_path, monkeypatch):
    monkeypatch.setenv("PASSLAB_OUTPUT", str(tmp_path))
    app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=30)
    assert not app.exception
    assert "No local analysis" in app.info[0].value


@pytest.mark.integration
def test_app_smoke_controls_and_unavailable_target(monkeypatch):
    if not (SMOKE / "passes.csv").exists():
        pytest.skip("Generate outputs/smoke first")
    monkeypatch.setenv("PASSLAB_OUTPUT", str(SMOKE))
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    assert not app.exception

    def select(label):
        return next(x for x in app.selectbox if x.label == label)

    select("Tournament").select("Women's Euro 2025").run()
    assert not app.exception
    select("Match partition").select("All matches").run()
    assert not app.exception
    data = pd.read_csv(SMOKE / "passes.csv")
    data = data[(data.tournament == "Women's Euro 2025") & data.has_frame]
    match_id = int(data.match_id.max())
    select("Match").select(match_id).run()
    assert not app.exception
    data = data[data.match_id == match_id]
    team = sorted(data.team.unique())[-1]
    select("Team in possession").select(team).run()
    assert not app.exception
    data = data[data.team == team]
    possession = int(data.groupby("possession").size().idxmax())
    select("Historical possession").select(possession).run()
    assert not app.exception
    event_id = data[data.possession == possession].sort_values("event_index").event_id.iloc[-1]
    select("Pass in this possession").select(event_id).run()
    assert not app.exception
    scenes = json.loads((SMOKE / "scenes.json").read_text())
    candidate = scenes[event_id]["teammates"][-1]["candidate_id"]
    select("Highlight visible teammate").select(candidate).run()
    assert not app.exception
    app.multiselect[0].set_value([]).run()
    assert not app.exception
    assert app.warning


@pytest.mark.integration
def test_invalid_outputs_show_error(tmp_path, monkeypatch):
    for name in [
        "passes.csv",
        "scenes.json",
        "metrics.csv",
        "predictions.csv",
        "model-bundles.json",
        "run-summary.json",
    ]:
        (tmp_path / name).write_text("invalid")
    monkeypatch.setenv("PASSLAB_OUTPUT", str(tmp_path))
    app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=30)
    assert not app.exception
    assert "Cannot read the local analysis" in app.error[0].value


@pytest.mark.integration
def test_full_app_review_filter_and_population(monkeypatch):
    if not (ROOT / "outputs/review-queue.csv").exists():
        pytest.skip("Generate the full model outputs first")
    import pandas as pd

    monkeypatch.setenv("PASSLAB_OUTPUT", str(ROOT / "outputs"))
    queue = pd.read_csv(ROOT / "outputs/review-queue.csv")
    if queue.empty:
        pytest.skip("No review flags in this run")
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=45).run()
    assert not app.exception

    def select(label):
        return next(x for x in app.selectbox if x.label == label)

    select("Decision view").select("Experimental review flags").run()
    assert not app.exception
    assert any("Inferred chosen recipient:" in x.value for x in app.caption)
    select("Evaluation population").select("recipient_proxy").run()
    assert not app.exception
    assert select("Pass in this possession").value in set(queue.event_id)
