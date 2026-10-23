import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).parents[1]


def load_builder():
    spec = importlib.util.spec_from_file_location("possession_build_website", ROOT / "scripts/build_website.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def payload():
    bundle = json.loads((ROOT / "web/bundle.json").read_text())
    archive = (ROOT / "web/snapshot.json.gz").read_bytes()
    assert hashlib.sha256(archive).hexdigest() == bundle["snapshot"]["archive_sha256"]
    decoded = gzip.decompress(archive)
    assert hashlib.sha256(decoded).hexdigest() == bundle["snapshot"]["sha256"]
    return json.loads(decoded)


def test_static_release_builds_without_raw_data(tmp_path):
    builder = load_builder()
    builder.build(tmp_path)
    assert (tmp_path / "index.html").exists()
    release = json.loads((tmp_path / "release.json").read_text())
    assert (tmp_path / release["snapshot"]).exists()
    assert (tmp_path / "statsbomb-terms.pdf").exists()
    assert not (tmp_path / "events.csv").exists()
    assert not (tmp_path / "actions.csv").exists()


def test_public_snapshot_contains_derived_analysis_only():
    data = payload()
    assert data["schema_version"] == 1
    for dataset in data["datasets"]:
        assert not set(dataset["phase_columns"]) & {"event_id", "player", "location", "x", "y", "end_x", "end_y", "provider_owner"}
        assert "events" not in dataset
        assert "actions" not in dataset
        assert len(dataset["fixtures"]) == dataset["summary"]["matches"]
        assert len(dataset["phases"]) == dataset["summary"]["possessions"]
        train = set(dataset["model"]["train_matches"])
        test = {row["match_id"] for row in dataset["team_matches"] if row["split"] == "test"}
        assert not train & test
        assert sum(row["passes"] for row in dataset["team_matches"]) == sum(row[dataset["phase_columns"].index("passes")] for row in dataset["phases"])


def test_build_rejects_corruption_and_unsafe_paths(tmp_path):
    builder = load_builder()
    for name in ["../secret", "/absolute"]:
        with pytest.raises(ValueError, match="Invalid release path"):
            builder.safe(name)
    root = tmp_path / "source"
    (root / "web").mkdir(parents=True)
    (root / "web/snapshot.json.gz").write_bytes(b"corrupt")
    (root / "web/bundle.json").write_text(json.dumps({"snapshot": {"archive": "snapshot.json.gz", "archive_sha256": "wrong"}}))
    builder.ROOT = root
    with pytest.raises(ValueError, match="Integrity"):
        builder.build(tmp_path / "out")
    assert not (tmp_path / "out").exists()


@pytest.mark.skipif(not shutil.which("node"), reason="Node is optional; needed to verify browser/Python metric parity")
def test_browser_aggregations_match_reviewed_python_results():
    data = payload()["datasets"][0]
    source = {"teams": [row for row in data["team_matches"] if row["split"] == "test"], "states": data["score_states"]}
    script = "const m=require(process.argv[1]); let s=''; process.stdin.on('data',x=>s+=x); process.stdin.on('end',()=>{const d=JSON.parse(s); console.log(JSON.stringify({teams:m.aggregateTeams(d.teams),states:m.aggregateStates(d.states)}));});"
    result = subprocess.run([shutil.which("node"), "-e", script, str(ROOT / "web/metrics.js")], input=json.dumps(source), text=True, capture_output=True, check=True)
    actual = json.loads(result.stdout)
    for expected in data["summary"]["heldout_teams"]:
        row = next(row for row in actual["teams"] if row["team"] == expected["team"])
        assert row["possession"] == pytest.approx(expected["mean_possession_pct"], abs=1e-8)
        assert row["threat"] == pytest.approx(expected["mean_threat_share"], abs=1e-8)
        assert row["xt_per_100"] == pytest.approx(expected["xt_per_100"], abs=1e-8)
    assert sum(row["positive_xt"] for row in actual["states"]) == pytest.approx(sum(row["positive_xt"] for row in data["score_states"]))


@pytest.mark.skipif(not shutil.which("node"), reason="Node is optional for browser metric checks")
def test_browser_style_boundaries_and_absent_exposure():
    script = "const assert=require('node:assert/strict'); const m=require(process.argv[1]); assert.equal(m.classify({elapsed_seconds:30,passes:10,positive_xt:.009,shots:0}),'High volume / low threat'); assert.equal(m.classify({elapsed_seconds:15,passes:4,positive_xt:.05,shots:0}),'Direct / high threat'); assert.equal(m.classify({elapsed_seconds:40,passes:10,positive_xt:.001,shots:1}),'Other'); assert.equal(m.aggregateStates([{team:'A',score_state:'drawing',active_seconds:0,positive_xt:0,shots:0,xg:0}])[0].rate,null);"
    subprocess.run([shutil.which("node"), "-e", script, str(ROOT / "web/metrics.js")], check=True)
