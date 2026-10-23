"""Run `python -m passlab.pipeline --sample 2` before the full analysis."""

from __future__ import annotations

import argparse
import hashlib
import platform
from importlib.metadata import version
from pathlib import Path

import pandas as pd

from .choices import build_review_queue
from .data import REVISION, Cache, download_matches, select_matches, write_json
from .features import extract_dataset
from .models import FEATURE_SETS, calibration_table, fit_evaluate, split_matches
from .report import calibration_chart, write_findings, write_tournament_metrics

PROJECT = Path(__file__).resolve().parents[1]


def run(cache_root: Path, output: Path, sample=2, offline=False, models="all"):
    output.mkdir(parents=True, exist_ok=True)
    cache = Cache(cache_root, offline=offline)
    matches = select_matches(cache, sample)
    print(f"Loading {len(matches)} pinned matches from both tournaments...", flush=True)
    tables, scenes, audits = [], {}, []
    for offset in range(0, len(matches), 4):
        payloads = download_matches(cache, matches[offset : offset + 4])
        table, chunk_scenes, chunk_audits = extract_dataset(payloads)
        tables.append(table)
        scenes.update(chunk_scenes)
        audits.extend(chunk_audits)
        del payloads
        print(f"  {min(offset + 4, len(matches))}/{len(matches)} matches parsed", flush=True)
    df = pd.concat(tables, ignore_index=True)
    print(f"Parsed {len(df):,} passes; {int(df.has_target.sum()):,} target proxies.", flush=True)
    split = split_matches(df)
    df["partition"] = df.match_id.map(lambda m: "train" if m in split["train"] else "test")
    metrics, predictions, bundles, omissions = fit_evaluate(
        df, split, kinds=("logistic",) if models == "baseline" else ("logistic", "boosted")
    )
    queue, candidate_audit = build_review_queue(df, scenes, bundles.get("target_360"))
    queue.to_csv(output / "review-queue.csv", index=False)
    write_json(output / "candidate-audit.json", candidate_audit)
    df.to_csv(output / "passes.csv", index=False)
    predictions.to_csv(output / "predictions.csv", index=False)
    calibration = pd.concat(
        [calibration_table(g).assign(model_id=name) for name, g in predictions.groupby("model_id")],
        ignore_index=True,
    )
    calibration.to_csv(output / "calibration.csv", index=False)
    metrics.to_csv(output / "metrics.csv", index=False)
    write_json(output / "scenes.json", scenes)
    write_json(output / "model-bundles.json", bundles)
    write_json(output / "split.json", split)
    write_json(output / "audit.json", audits)
    calibration_chart(predictions, metrics, output, PROJECT / "assets")
    write_findings(df, audits, metrics, split, omissions, output, sample, candidate_audit)
    write_tournament_metrics(predictions, output)
    provenance = {
        "revision": REVISION,
        "selection": "all" if sample is None else f"earliest {sample} per tournament",
        "matches": matches,
        "source_receipts": cache.receipts(),
        "split": split,
        "features": FEATURE_SETS,
        "models": models,
        "omissions": omissions,
        "python": platform.python_version(),
        "versions": {
            p: version(p)
            for p in ["numpy", "pandas", "scikit-learn", "streamlit", "mplsoccer", "plotly", "matplotlib"]
        },
        "output_hashes": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(output.iterdir())
            if p.is_file()
            and p.name
            in [
                "passes.csv",
                "scenes.json",
                "predictions.csv",
                "metrics.csv",
                "model-bundles.json",
                "split.json",
                "audit.json",
                "calibration.png",
                "calibration.svg",
                "findings.md",
                "tournament-metrics.json",
                "calibration.csv",
                "review-queue.csv",
                "candidate-audit.json",
            ]
        },
    }
    write_json(output / "provenance.json", provenance)
    summary = {
        "revision": REVISION,
        "selection": provenance["selection"],
        "matches": len(matches),
        "eligible_passes": len(df),
        "frames_with_defenders": int((df.has_frame & df.has_opponents.fillna(False)).sum()),
        "recipient_proxies": int(df.has_target.sum()),
        "split": split,
        "omissions": omissions,
        "versions": provenance["versions"],
        "candidate_audit": candidate_audit,
        "output_hashes": provenance["output_hashes"],
    }
    write_json(output / "run-summary.json", summary)
    print(metrics[["model_id", "train_n", "n", "log_loss", "brier"]].to_string(index=False), flush=True)
    print(f"Wrote reproducible results to {output}", flush=True)
    return df, metrics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument(
        "--sample", type=int, default=2, metavar="N", help="earliest N matches per tournament (default 2)"
    )
    selection.add_argument("--full", action="store_true", help="all 82 matches in the pinned source")
    parser.add_argument(
        "--offline", action="store_true", help="require verified cached files; never use network"
    )
    parser.add_argument("--models", choices=["baseline", "all"], default="all")
    parser.add_argument("--cache", type=Path, default=PROJECT / "data" / "raw")
    parser.add_argument("--output", type=Path, default=PROJECT / "outputs")
    args = parser.parse_args()
    try:
        run(args.cache, args.output, None if args.full else args.sample, args.offline, args.models)
    except (ValueError, FileNotFoundError, OSError) as exc:
        parser.exit(1, f"Pipeline stopped: {exc}\n")


if __name__ == "__main__":
    main()
