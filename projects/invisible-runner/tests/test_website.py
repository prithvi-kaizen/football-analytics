"""The published release must work from a clone without raw tracking or a venv."""

import gzip
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def snapshot():
    return json.loads(gzip.decompress((ROOT / "web/snapshot.json.gz").read_bytes()))


def test_published_profiles_reconcile(snapshot):
    assert {speed: len(profile["runs"]) for speed, profile in snapshot["profiles"].items()} == {"4.5":444,"5.0":303,"5.5":209}
    baseline = snapshot["profiles"]["5.0"]["runs"]
    assert sum(r["free_area_delta_m2"] is not None for r in baseline) == 299
    assert sum(r["runner_detected_fraction"] == 1 for r in baseline) == 223
    assert sum(r["runner_detected_fraction"] == 1 and r["context_endpoint_detected_fraction"] == 1 and r["ball_endpoint_detected"] for r in baseline) == 5


def test_every_replay_uses_real_ids_and_endpoints(snapshot):
    player_ids = {int(pid) for pid in snapshot["metadata"]["players"]}
    for profile in snapshot["profiles"].values():
        for run in profile["runs"]:
            frames = run["replay"]
            assert frames[0]["frame"] == run["start_frame"]
            assert frames[-1]["frame"] == run["end_frame"]
            assert frames[-1]["elapsed_s"] == pytest.approx(run["duration_s"])
            for frame in frames:
                assert {p[0] for p in frame["players"]} <= player_ids
            if run["free_area_delta_m2"] is not None:
                assert frames[0]["free_area_m2"] == run["free_area_start_m2"]
                assert frames[-1]["free_area_m2"] == run["free_area_end_m2"]


def test_static_build_uses_standard_library(tmp_path):
    subprocess.run([sys.executable,"-S",str(ROOT / "scripts/build_website.py"),"--output",str(tmp_path)],check=True,capture_output=True)
    release = json.loads((tmp_path / "release.json").read_text())
    assert release["encoding"] == "gzip"
    data = json.loads(gzip.decompress((tmp_path / release["snapshot"]).read_bytes()))
    assert len(data["profiles"]["5.0"]["runs"]) == 303
    assert (tmp_path / "vendor/plotly.min.js").exists()


def test_release_has_no_local_paths_or_private_player_fields(snapshot):
    text = json.dumps(snapshot)
    assert "/Users/" not in text
    assert "clean_path" not in text
    assert "birthday" not in text
    assert "127.0.0.1" not in text


def test_tampered_asset_fails_build(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("release_builder", ROOT / "scripts/build_website.py")
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    shutil.copytree(ROOT / "web",tmp_path / "web")
    (tmp_path / "web/app.js").write_text("tampered")
    monkeypatch.setattr(builder,"ROOT",tmp_path)
    with pytest.raises(ValueError,match="Integrity check failed"):
        builder.build(tmp_path / "dist")
