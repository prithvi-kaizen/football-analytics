"""Local experiments. All scored truth is generated here; public samples are unscored."""
from dataclasses import asdict
import json
from pathlib import Path
import platform
import sys

import numpy as np
import pandas as pd

from .csv_io import write_submission
from .models import ModelConfig
from .official import MANIFEST, ROOT, metrics_module, sha256, verify
from .pipeline import infer
from .synthetic import SyntheticConfig, generate

METHODS = ("nearest", "state_machine", "hmm")


def _json(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n")


def benchmark(config_path, out):
    import matplotlib
    matplotlib.use("Agg")
    from .plots import diagnostic_plot, metric_plot

    config_path, out = Path(config_path), Path(out)
    config = json.loads(config_path.read_text())
    if set(config) != {"seeds", "model", "scenarios"} or not config["seeds"] or not config["scenarios"]:
        raise ValueError("benchmark needs nonempty seeds/scenarios and explicit model config")
    if len(set(config["seeds"])) != len(config["seeds"]):
        raise ValueError("duplicate benchmark seeds")
    model = ModelConfig(**config["model"])
    out.mkdir(parents=True, exist_ok=True)
    pm = metrics_module()
    rows, timelines = [], {}
    for name, overrides in config["scenarios"].items():
        if not name.replace("_", "").isalnum():
            raise ValueError("scenario names must be simple identifiers")
        synthetic = SyntheticConfig(**overrides)
        for seed in config["seeds"]:
            match = generate(synthetic, seed)
            batch = match.tracking
            truth = pm.label_codes(match.truth)
            folder = out / name / str(seed)
            folder.mkdir(parents=True, exist_ok=True)
            write_submission(folder / "truth.csv", match.truth)
            predictions = {}
            for method in METHODS:
                result = infer(batch, method, model)
                pred = pm.label_codes(result.labels)
                scores = pm.evaluate(truth, pred)
                write_submission(folder / f"{method}.csv", result.labels)
                _json(folder / f"{method}.json", scores)
                graded = match.truth != "X"
                error = result.labels != match.truth
                row = {"scenario": name, "seed": seed, "method": method,
                       "macro_f1": scores["macro_f1"], "spell_f1": scores["spell_f1_mean"],
                       "possessions": scores["n_pred_spells"], "true_possessions": scores["n_gt_spells"],
                       "fragmentation": scores["fragmentation"], "dead_f1": scores["per_class"]["D"]["f1"],
                       "transition_f1_25": scores["transitions"][25]["f1"],
                       "mean_abs_latency_frames": scores["transitions"][25]["mean_abs_latency"],
                       "abstention_rate": float(np.mean(result.labels[graded] == "X"))}
                for group, mask in {**match.diagnostics, "ball_observed": result.features.ball_observed}.items():
                    subset = mask & graded
                    row[f"error_{group}"] = float(error[subset].mean()) if subset.any() else None
                rows.append(row)
                predictions[method] = result.labels
            f = result.features
            pd.DataFrame({"frame": batch.frame, "period": batch.period, "truth": match.truth,
                          "ball_observed": f.ball_observed, "home_distance_m": f.nearest_home_m,
                          "away_distance_m": f.nearest_away_m, "ball_speed_mps": f.ball_speed_mps,
                          "player_speed_mps": f.player_speed_mps, "reliability": f.reliability,
                          "stationary_seconds": f.stationary_seconds,
                          **match.diagnostics}).to_csv(folder / "features.csv", index=False)
            if seed == config["seeds"][0]:
                timelines[name] = (batch.time_s, match.truth, predictions, f.ball_observed)
    table = pd.DataFrame(rows)
    table.to_csv(out / "metrics.csv", index=False)
    summary = table.groupby(["scenario", "method"], sort=True)[
        ["macro_f1", "spell_f1", "dead_f1", "fragmentation", "abstention_rate"]].agg(["mean", "std"])
    summary.to_csv(out / "summary.csv")
    metric_plot(table, out / "metrics.png")
    diagnostic_plot(timelines, out / "failure_modes.png")
    _json(out / "config.json", config)
    _json(out / "manifest.json", {
        "scope": "synthetic only; no competition-performance estimate; no model fitting",
        "python": sys.version, "platform": platform.platform(), "numpy": np.__version__,
        "pandas": pd.__version__, "official_commit": json.loads(MANIFEST.read_text())["commit"],
        "config_sha256": sha256(config_path), "requirements_sha256": sha256(ROOT / "requirements.lock.txt"),
        "source_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in sorted((ROOT / "src").rglob("*.py"))},
        "resolved_synthetic": {name: asdict(SyntheticConfig(**x)) for name, x in config["scenarios"].items()},
        "model": asdict(model), "run_count": len(rows),
        "aggregation": "equal-weight mean across seeds, sample standard deviation; not confidence intervals"})
    verify()
    return table


def sample_smoke(home, away, out, max_frames=None):
    from .adapters.metrica_csv import MetricaCSVAdapter
    from .features import extract
    from .models import hmm, state_machine

    batch = MetricaCSVAdapter(Path(home), Path(away), max_frames=max_frames).load()
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    f = extract(batch)
    predictions = {"nearest": f.nearest_team, "state_machine": state_machine(f), "hmm": hmm(f)}
    for method, labels in predictions.items():
        labels[batch.period == 0] = "X"
        write_submission(out / f"{method}.csv", labels, len(batch.frame))
    receipt = {"purpose": "adapter and inference smoke test only; no possession truth or accuracy scores",
               "frames": len(batch.frame), "periods": sorted(map(int, np.unique(batch.period))),
               "ball_observed_fraction": float(f.ball_observed.mean()),
               "home_slots": batch.home.shape[1], "away_slots": batch.away.shape[1],
               "pitch_m": batch.pitch, "provenance": batch.provenance,
               "labels": {name: {x: int(np.sum(labels == x)) for x in ("H", "A", "D", "X")}
                          for name, labels in predictions.items()}}
    _json(out / "receipt.json", receipt)
    return receipt
