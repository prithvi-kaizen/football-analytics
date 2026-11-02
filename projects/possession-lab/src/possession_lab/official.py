"""Read-only use of the pinned public scorer, with integrity verification before import/run."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OFFICIAL = ROOT.parent / "more-than-a-hack-2027"
MANIFEST = ROOT / "docs" / "official_manifest.json"


def sha256(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def verify(root=DEFAULT_OFFICIAL):
    manifest = json.loads(MANIFEST.read_text())
    root = Path(root)
    for name, expected in manifest["files"].items():
        if sha256(root / name) != expected:
            raise ValueError(f"official file changed: {name}")
    return manifest


def metrics_module(root=DEFAULT_OFFICIAL):
    verify(root)
    spec = importlib.util.spec_from_file_location("_mtah_public_metrics", Path(root) / "evaluation/possession_metrics.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def score_synthetic(truth, prediction, fps=25, root=DEFAULT_OFFICIAL, bootstrap_n=0):
    """Arrays only, synthetic labels supplied by caller. No ground-truth file input API."""
    if fps != 25:
        raise ValueError("official duration/transition units assume 25 fps")
    pm = metrics_module(root)
    return pm.evaluate(pm.label_codes(truth), pm.label_codes(prediction), bootstrap_n=bootstrap_n)


EXPECTED = {"baseline_raw": (0.5972, 0.0378), "baseline_smooth25": (0.6200, 0.2868),
            "baseline_smooth50": (0.6207, 0.3256), "baseline_smooth125": (0.5812, 0.4242)}


def reproduce(out, root=DEFAULT_OFFICIAL):
    """Only the four immutable supplied files enter this public-label sanity check."""
    import pandas as pd

    manifest = verify(root)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    inputs = out / "supplied_baselines"
    inputs.mkdir(exist_ok=True)
    if set(p.stem for p in inputs.glob("*.csv")) - set(EXPECTED):
        raise ValueError("sanity-check directory contains non-official predictions")
    for name in EXPECTED:
        shutil.copyfile(Path(root) / "evaluation/results" / f"{name}.csv", inputs / f"{name}.csv")
    result = subprocess.run([sys.executable, str(Path(root) / "evaluation/run_evaluation.py"),
                             "--gt", "public", "--results", str(inputs.resolve()),
                             "--out", str(out.resolve()), "--no-detail"],
                            check=True, capture_output=True, text=True)
    (out / "stdout.txt").write_text(result.stdout)
    table = pd.read_csv(out / "scoreboard.csv")
    if set(table.submission) != set(EXPECTED) or set(table.status) != {"scored"}:
        raise AssertionError("not all four supplied baselines scored")
    for row in table.itertuples():
        actual = (row.macro_f1, row.spell_f1_mean)
        if not np.allclose(actual, EXPECTED[row.submission], atol=0.00005, rtol=0):
            raise AssertionError(f"baseline reproduction mismatch: {row.submission}")
    verify(root)
    (out / "receipt.json").write_text(json.dumps({"purpose": "supplied baseline sanity only; no fitting or selection",
                                                  "official_commit": manifest["commit"], "passed": True}, indent=2) + "\n")
    return result.stdout
