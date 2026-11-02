import json

import pandas as pd

from possession_lab.phase2_experiments import evaluate_phase2, verify_phase1_freeze


def test_phase1_files_are_frozen():
    assert verify_phase1_freeze() >= 408


def test_phase2_reproduces_and_null_pairs_cannot_false_gain(tmp_path):
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"trials": [1011, 1012], "world_families": ["episodes"],
        "regimes": {"moderate": {}}, "twin_kinds": ["static"], "twin_regimes": ["moderate"],
        "fusion": {}, "bootstrap_draws": 30, "bootstrap_seed": 2}))
    a = evaluate_phase2(config, tmp_path / "a", make_report=True)
    b = evaluate_phase2(config, tmp_path / "b", make_report=False)
    timing = ["decode_ms", "feature_ms", "total_ms"]
    assert len(a) == 66
    pd.testing.assert_frame_equal(a.drop(columns=timing), b.drop(columns=timing))
    checks = json.loads((tmp_path / "a/null_twin_checks.json").read_text())
    assert len(checks) == 10
    assert all(row["identical_predictions"] and row["balanced_target_accuracy"] <= 0.5 for row in checks)
    assert (tmp_path / "a/trials/episodes/moderate/single/1011.csv").read_bytes() == (tmp_path / "b/trials/episodes/moderate/single/1011.csv").read_bytes()
    assert verify_phase1_freeze() >= 408
    assert (tmp_path / "a/report.md").exists()
    assert (tmp_path / "a/failure_cases.png").stat().st_size > 0
