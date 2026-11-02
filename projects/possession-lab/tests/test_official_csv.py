import json

import numpy as np
import pandas as pd
import pytest

from possession_lab.csv_io import write_submission
from possession_lab import official


@pytest.fixture(scope="module")
def pm():
    return official.metrics_module()


def test_original_files_unchanged():
    assert official.verify()["commit"] == "f8f2629ff1e0985f81d7e59d8413678514ee1530"


def test_integrity_rejects_edit(tmp_path, monkeypatch):
    file = tmp_path / "scorer.py"
    file.write_text("original")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"files": {"scorer.py": official.sha256(file)}}))
    monkeypatch.setattr(official, "MANIFEST", manifest)
    file.write_text("changed")
    with pytest.raises(ValueError, match="changed"):
        official.verify(tmp_path)


def test_full_submission_contract(tmp_path, pm):
    labels = np.resize(np.array(list("HADX")), 199319)
    path = write_submission(tmp_path / "submission.csv", labels, 199319)
    assert pm.validate_submission(pm.read_label_csv(path), 199319) is None
    first = path.read_bytes()
    write_submission(path, labels, 199319)
    assert first == path.read_bytes()


@pytest.mark.parametrize("labels,rows", [(["H", ""], 2), (["Q"], 1), (["h"], 1),
                                       (["H"], 2), ([], 0), ([["H"]], 1)])
def test_writer_rejects_invalid(tmp_path, labels, rows):
    with pytest.raises(ValueError):
        write_submission(tmp_path / "bad.csv", labels, rows)


@pytest.mark.parametrize("frames,labels", [([1, 2], ["H", "A"]), ([0, 0], ["H", "A"]),
    ([0.0, 1.0], ["H", "A"]), ([0, 1], ["H", None]), ([0, 1], ["H", "Q"])])
def test_official_rejects_bad_csv(frames, labels, pm):
    assert pm.validate_submission(pd.DataFrame({"frame": frames, "label": labels}), 2) is not None


def test_exact_spells_and_dead_boundaries(pm):
    gt = pm.label_codes(list("HHDDHHAA"))
    result = pm.evaluate(gt, gt)
    assert result["macro_f1"] == pytest.approx(1)
    assert result["spell_f1_mean"] == pytest.approx(1)
    assert result["n_gt_spells"] == 3
    assert pm.possession_spells(gt, pm.valid_runs(gt)) == [(0, 2, 0), (4, 6, 0), (6, 8, 1)]


def test_abstention_frame_penalty_temporal_fill(pm):
    gt = pm.label_codes(list("HHHAAADD"))
    pred = pm.label_codes(list("HXHAXADD"))
    scores = pm.evaluate(gt, pred)
    assert scores["macro_f1"] < 1
    assert scores["spell_f1_mean"] == pytest.approx(1)


def test_halftime_never_merges_or_fills(pm):
    gt = pm.label_codes(list("HHXXXHH"))
    pred = pm.label_codes(list("HHXXXXX"))
    runs = pm.valid_runs(gt)
    assert len(pm.possession_spells(gt, runs)) == 2
    assert pm.transitions(gt, runs) == []
    assert list(pm.fill_abstentions(pred, runs)[5:]) == [pm.X, pm.X]


def test_same_team_matching_and_one_to_one(pm):
    overlaps = pm.spell_overlaps([(0, 10, pm.H)], [(0, 5, pm.H), (5, 10, pm.H), (0, 10, pm.A)])
    assert pm.match_spells(overlaps, 1, 3, 0.5) == (1, 2, 0)


def test_absent_class_macro_policy(pm):
    h = pm.label_codes(list("HHHH"))
    assert pm.evaluate(h, h)["macro_f1"] == pytest.approx(1 / 3)


def test_synthetic_score_no_fps_confusion():
    with pytest.raises(ValueError):
        official.score_synthetic(["H"], ["H"], fps=30)


def test_bootstrap_repeatable(pm):
    gt = pm.label_codes(list("HHHAAADDDHHHAAA"))
    a = pm.evaluate(gt, gt, bootstrap_n=20)
    b = pm.evaluate(gt, gt, bootstrap_n=20)
    assert a == b
