"""Real-data integration tests. No synthetic observations enter published outputs."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from invisible_runner.analysis import RunConfig, detect_runs
from invisible_runner.data import REVISION, attack_sign, clock_seconds, sha256
from invisible_runner.pipeline import analyze
from invisible_runner.viz import pitch_figure, replay_frames

PROJECT = Path(__file__).resolve().parents[1]


def manifest_for(scope):
    path = PROJECT / "outputs" / f"1886347-{scope}" / "manifest.json"
    if not path.exists():
        pytest.skip(f"Download {scope} first with python -m invisible_runner run")
    manifest = json.loads(path.read_text())
    if not Path(manifest["clean_path"]).exists():
        pytest.skip("Local processed cache missing; reproduce the pipeline first")
    return manifest


@pytest.mark.real_data
def test_real_sample_pipeline_and_cache(tmp_path):
    manifest = manifest_for("sample-300s")
    bundle = {k: manifest[k] for k in ["match_id", "revision", "paths", "sources", "scope"]}
    result = analyze(bundle, tmp_path)
    runs = pd.read_csv(tmp_path / "runs.csv")
    assert result["revision"] == REVISION
    assert result["audit"]["source_frames"] == 3000
    assert result["audit"]["null_period_frames"] == 10
    assert result["run_count"] > 0
    assert runs.run_id.is_unique
    assert (runs.distance_m >= 5).all()
    assert (runs.progress_m >= 3).all()
    assert (runs.duration_s >= 1).all()
    assert (runs.peak_speed_mps <= 12.5).all()
    assert runs.runner_detected_fraction.between(0, 1).all()
    assert runs.free_area_start_m2.dropna().between(0, 120).all()
    assert np.allclose((runs.free_area_end_m2 - runs.free_area_start_m2).dropna(), runs.free_area_delta_m2.dropna())
    assert result["outputs"]["runs_sha256"] == sha256(tmp_path / "runs.csv")
    assert (tmp_path / "space-change.png").stat().st_size > 10000
    assert (tmp_path / "findings.md").exists()
    cached = analyze(bundle, tmp_path)
    assert cached["outputs"] == result["outputs"]
    clean = pd.read_parquet(result["clean_path"])
    run = runs.sort_values("start_frame").iloc[0]
    frames, timeline = replay_frames(clean, run, result["metadata"], RunConfig())
    assert timeline.free_area_m2.iloc[0] == run.free_area_start_m2
    assert timeline.free_area_m2.iloc[-1] == run.free_area_end_m2
    figure = pitch_figure(frames[0], run, clean, result["metadata"])
    assert len(figure.data) >= 10
    assert figure.to_json()


@pytest.mark.real_data
def test_real_full_match_both_periods_and_directions():
    manifest = manifest_for("full")
    runs = pd.read_csv(PROJECT / "outputs/1886347-full/runs.csv")
    assert set(runs.period) == {1, 2}
    assert manifest["sources"]["tracking"]["complete"]
    assert manifest["audit"]["source_frames"] == 59061
    m = manifest["metadata"]
    for run in runs.itertuples():
        sign = attack_sign(m, run.team_id, run.period)
        assert (run.end_x - run.start_x) * sign == pytest.approx(run.progress_m)
        assert run.start_clock_s == pytest.approx(clock_seconds(run.start_frame, run.period, m))
    assert manifest["audit"]["raw_jump_rows"] > 0
    assert runs.context_valid.isin([True, False]).all()


@pytest.mark.real_data
def test_provider_labels_do_not_enter_detector():
    manifest = manifest_for("sample-300s")
    clean = pd.read_parquet(manifest["clean_path"])
    forbidden = ["off_ball_run", "intended_run_behind", "lead_to_goal", "lead_to_shot", "pass_epv_total"]
    assert not set(forbidden) & set(clean)
    runs = detect_runs(clean, manifest["metadata"], RunConfig())
    assert len(runs) == manifest["run_count"]
