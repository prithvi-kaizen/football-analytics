import json

import pandas as pd

from possession_lab.experiments import benchmark
from possession_lab.official import reproduce


def test_supplied_baselines_only(tmp_path):
    stdout = reproduce(tmp_path)
    assert "baseline_smooth125" in stdout
    receipt = json.loads((tmp_path / "receipt.json").read_text())
    assert receipt["passed"]


def test_small_end_to_end_harness(tmp_path):
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"seeds": [909], "model": {}, "scenarios": {"smoke": {}}}))
    a = benchmark(config, tmp_path / "a")
    b = benchmark(config, tmp_path / "b")
    pd.testing.assert_frame_equal(a, b)
    assert len(a) == 3
    for file in ("metrics.png", "failure_modes.png", "manifest.json", "summary.csv"):
        assert (tmp_path / "a" / file).stat().st_size > 0
    assert (tmp_path / "a/smoke/909/hmm.csv").read_bytes() == (tmp_path / "b/smoke/909/hmm.csv").read_bytes()
