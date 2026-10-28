"""Run this stage before adding orientation features."""

from pathlib import Path
import json
import hashlib
import pandas as pd
from .data import build_receptions
from .models import fit_predict, metrics


def run(root, cfg):
    out = Path(root) / "outputs"
    out.mkdir(exist_ok=True)
    rows = []
    audit = {}
    for m in cfg["matches"]:
        data, report, _ = build_receptions(Path(root) / "data/raw", m, cfg)
        rows.append(data)
        audit[str(m)] = report
    data = pd.concat(rows, ignore_index=True)
    data.to_csv(out / "receptions_baseline.csv", index=False)
    results = []
    for tr, te in [
        (cfg["train_match"], cfg["test_match"]),
        (cfg["test_match"], cfg["train_match"]),
    ]:
        train = data[data.match_id.eq(tr)]
        test = data[data.match_id.eq(te)]
        p, _ = fit_predict(train, test, cfg["baseline_features"], cfg)
        import numpy as np

        results.append(
            {
                "train_match": tr,
                "test_match": te,
                "train_n": len(train),
                "baseline": metrics(test.target, p),
                "constant": metrics(
                    test.target, np.full(len(test), train.target.mean())
                ),
            }
        )
    (out / "baseline_results.json").write_text(json.dumps(results, indent=2) + "\n")
    (out / "baseline_audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    assert all(
        r["baseline"]["n"] > 100 and r["baseline"]["log_loss"] > 0 for r in results
    )
    (out / "BASELINE_VALIDATED.json").write_text(
        json.dumps(
            {
                "sha256": hashlib.sha256(
                    (out / "receptions_baseline.csv").read_bytes()
                ).hexdigest(),
                "config_sha256": hashlib.sha256(
                    json.dumps(cfg, sort_keys=True).encode()
                ).hexdigest(),
                "stage": "real-data baseline ran before pose method",
            },
            indent=2,
        )
        + "\n"
    )
    print(json.dumps(results, indent=2))
    return data
