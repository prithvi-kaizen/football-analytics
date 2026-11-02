import csv
from pathlib import Path

import numpy as np
import pytest

from possession_lab.adapters.metrica_csv import MetricaCSVAdapter
from possession_lab.pipeline import infer
from possession_lab.official import ROOT


def fixture_file(path, team, rows=None):
    rows = rows or [[1, 1, 0.04, 0.25, 0.5, 0.5, 0.5],
                    [1, 2, 0.08, "NaN", "NaN", 0.51, 0.5]]
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerows([["", "", "", team, "", "", ""],
                          ["", "", "", "11", "", "", ""],
                          ["Period", "Frame", "Time [s]", "Player11", "", "Ball", ""], *rows])


def test_sample_normalization_and_no_truth(tmp_path):
    h, a = tmp_path / "home.csv", tmp_path / "away.csv"
    fixture_file(h, "Home")
    fixture_file(a, "Away")
    b = MetricaCSVAdapter(h, a).load()
    np.testing.assert_allclose(b.home[0, 0], [26.25, 34])
    np.testing.assert_allclose(b.ball[0], [52.5, 34])
    assert np.isnan(b.home[1]).all()
    assert b.provenance["source_frame_start"] == 1
    assert "unlabelled" in b.provenance["label_status"]
    assert not hasattr(b, "truth")


@pytest.mark.parametrize("problem", ["frame", "side", "ball", "time", "header"])
def test_schema_conflicts_fail_explicitly(tmp_path, problem):
    h, a = tmp_path / "home.csv", tmp_path / "away.csv"
    fixture_file(h, "Home")
    rows = [[1, 1, 0.04, 0.25, 0.5, 0.5, 0.5], [1, 2, 0.08, 0.26, 0.5, 0.51, 0.5]]
    if problem == "frame":
        rows[1][1] = 3
    elif problem == "ball":
        rows[0][-1] = 0.9
    elif problem == "time":
        rows[1][2] = 0.1
    fixture_file(a, "Home" if problem == "side" else "Away", rows)
    if problem == "header":
        a.write_text(a.read_text().replace("Period", "Half"))
    with pytest.raises(ValueError):
        MetricaCSVAdapter(h, a).load()


@pytest.mark.parametrize("game", [1, 2])
def test_real_public_sample_prefix(game):
    root = ROOT.parent / "public-sample-data" / "data" / f"Sample_Game_{game}"
    h = root / f"Sample_Game_{game}_RawTrackingData_Home_Team.csv"
    a = root / f"Sample_Game_{game}_RawTrackingData_Away_Team.csv"
    if not h.exists():
        pytest.skip("optional public sample checkout not present; fixture tests still run")
    b = MetricaCSVAdapter(h, a, max_frames=1000).load()
    assert len(infer(b, "hmm").labels) == 1000
