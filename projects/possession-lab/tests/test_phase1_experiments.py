import json

import pandas as pd

from possession_lab.phase1_experiments import evaluate_phase1


def test_phase1_harness_reproduces_scores_and_pairs(tmp_path):
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"trials": [913, 914], "scenarios": ["iid", "twin_static_dead", "twin_static_live"],
                                 "hierarchical": {}, "bootstrap_draws": 30, "bootstrap_seed": 9}))
    a = evaluate_phase1(config, tmp_path / "a", make_report=True)
    b = evaluate_phase1(config, tmp_path / "b", make_report=False)
    assert len(a) == 60
    timing = ["feature_ms", "decode_ms", "total_ms", "realtime_factor"]
    pd.testing.assert_frame_equal(a.drop(columns=timing), b.drop(columns=timing))
    assert (a[timing] >= 0).all().all()
    checks = json.loads((tmp_path / "a/ambiguity_checks.json").read_text())
    assert len(checks) == 20
    assert all(row["identical_predictions"] for row in checks)
    first = tmp_path / "a/trials/iid/913.csv"
    assert first.read_bytes() == (tmp_path / "b/trials/iid/913.csv").read_bytes()
    confidence = pd.read_csv(tmp_path / "a/confidence.csv")
    assert set(confidence.trials) == {2}
    report = (tmp_path / "a/report.md").read_text()
    assert "30 draws" in report
    assert "2 trial clusters" in report
