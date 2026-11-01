"""Failure-driven, paired synthetic evaluation. No fitting or actual-match tag generation."""
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import platform
import sys
from time import perf_counter

import numpy as np
import pandas as pd

from .features import extract
from .hierarchical import HierarchicalConfig, hierarchical
from .models import ModelConfig, evidence, hmm, state_machine
from .official import ROOT, metrics_module, sha256, verify
from .phase1_metrics import boundary_errors, paired_deltas, summarise_trials
from .schema import LABELS
from .synthetic_trials import SCENARIOS, generate_trial

METRICS = ["spell_f1", "macro_f1", "D_precision", "D_recall", "boundary_f1",
           "boundary_missed", "boundary_spurious", "boundary_mae_frames", "boundary_p90_frames",
           "accuracy", "abstention_rate", "feature_ms", "decode_ms", "total_ms", "realtime_factor"]


def _json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def methods(config):
    cfg = HierarchicalConfig(**config)
    return {
        "nearest": lambda f: f.nearest_team.copy(),
        "state_machine": state_machine,
        "hmm": hmm,
        "sm_no_stationary": lambda f: state_machine(replace(f, stationary_seconds=np.zeros(len(f.period)))),
        "hmm_no_stationary": lambda f: hmm(replace(f, stationary_seconds=np.zeros(len(f.period)))),
        "hierarchical": lambda f: hierarchical(f, cfg),
        "hier_no_stationary": lambda f: hierarchical(f, replace(cfg, stationarity_weight=0.0)),
        "hier_missing_as_static": lambda f: hierarchical(f, replace(cfg, missing_masks=False)),
        "hier_no_duration": lambda f: hierarchical(f, replace(cfg, duration_priors=False)),
        "hier_no_continuity": lambda f: hierarchical(f, replace(cfg, possession_continuity=False)),
    }


def verify_legacy(recompute=False):
    manifest = json.loads((ROOT / "docs/phase1/baseline_manifest.json").read_text())
    for name, expected in manifest["source_hashes"].items():
        if sha256(ROOT / name) != expected:
            raise AssertionError(f"legacy source changed: {name}")
    if recompute:
        from .synthetic import SyntheticConfig, generate
        from .pipeline import infer
        cfg = json.loads((ROOT / "configs/benchmark.json").read_text())
        checked = 0
        for scenario, overrides in cfg["scenarios"].items():
            for seed in cfg["seeds"]:
                trial = generate(SyntheticConfig(**overrides), seed)
                arrays = {"truth": trial.truth}
                arrays.update({name: infer(trial.tracking, name, ModelConfig(**cfg["model"])).labels
                               for name in ("nearest", "state_machine", "hmm")})
                for name, labels in arrays.items():
                    path = f"outputs/synthetic/{scenario}/{seed}/{name}.csv"
                    digest = hashlib.sha256(("frame,label\n" + "".join(
                        f"{i},{v}\n" for i, v in enumerate(labels))).encode()).hexdigest()
                    if digest != manifest["legacy_predictions"][path]:
                        raise AssertionError(f"legacy prediction changed: {path}")
                    checked += 1
        return {"unchanged_source_files": len(manifest["source_hashes"]), "identical_csvs": checked}
    return {"unchanged_source_files": len(manifest["source_hashes"])}


def diagnose_legacy(out):
    from .synthetic import SyntheticConfig, generate
    trial = generate(SyntheticConfig(stationary_live=True), 101)
    f = extract(trial.tracking)
    live = np.isin(trial.truth, ["H", "A"])
    ordinary = evidence(f, ModelConfig())
    no_static = evidence(replace(f, stationary_seconds=np.zeros(len(f.period))), ModelConfig())
    rows = {"frame": trial.tracking.frame, "truth": trial.truth, "ball_speed_mps": f.ball_speed_mps,
            "player_speed_mps": f.player_speed_mps, "stationary_s": f.stationary_seconds,
            "reliability": f.reliability, "out_of_bounds": f.out_of_bounds,
            "evidence": ordinary, "evidence_no_stationary": no_static,
            "state_machine": state_machine(f), "hmm": hmm(f)}
    pd.DataFrame(rows).to_csv(out / "legacy_trace.csv", index=False)
    result = {"scenario": "old stationary_live, seed 101", "live_frames": int(live.sum()),
              "live_stationarity_fraction": float((f.stationary_seconds[live] >= 1.2).mean()),
              "control_overwritten_D": int((live & np.isin(no_static, ["H", "A"]) & (ordinary == "D")).sum()),
              "live_out_of_bounds": int((live & f.out_of_bounds).sum()),
              "SM_live_D_fraction": float((rows["state_machine"][live] == "D").mean()),
              "HMM_live_D_fraction": float((rows["hmm"][live] == "D").mean())}
    _json(out / "diagnosis.json", result)
    return result


def evaluate_phase1(config_path, out, make_report=True):
    cfg_path, out = Path(config_path), Path(out)
    cfg = json.loads(cfg_path.read_text())
    if (set(cfg) != {"trials", "scenarios", "hierarchical", "bootstrap_draws", "bootstrap_seed"}
            or not cfg["trials"] or len(set(cfg["trials"])) != len(cfg["trials"])
            or not cfg["scenarios"] or len(set(cfg["scenarios"])) != len(cfg["scenarios"])
            or not set(cfg["scenarios"]) <= set(SCENARIOS) or cfg["bootstrap_draws"] <= 0):
        raise ValueError("invalid explicit experiment configuration")
    out.mkdir(parents=True, exist_ok=True)
    baseline_check = verify_legacy()
    pm = metrics_module()
    runners = methods(cfg["hierarchical"])
    # Warm-up uses an unrelated synthetic fixture; it is never used to select a parameter.
    warm = extract(generate_trial("iid", 67).tracking)
    for runner in runners.values():
        runner(warm)
    rows, ambiguity_checks = [], []
    paired_predictions = {}
    for scenario in cfg["scenarios"]:
        for seed in cfg["trials"]:
            trial = generate_trial(scenario, seed)
            batch = trial.tracking
            begin = perf_counter()
            f = extract(batch)
            feature_ms = (perf_counter() - begin) * 1000
            gt = pm.label_codes(trial.truth)
            graded = trial.truth != "X"
            outputs = {"frame": batch.frame, "truth": trial.truth}
            # Counterbalance model order to avoid systematically favouring a later warmed decoder.
            order = list(runners)
            np.random.default_rng(seed).shuffle(order)
            for name in order:
                begin = perf_counter()
                result = runners[name](f)
                decode_ms = (perf_counter() - begin) * 1000
                labels = result.labels.copy() if hasattr(result, "labels") else result.copy()
                labels[batch.period == 0] = "X"
                if not set(labels) <= set(LABELS):
                    raise ValueError("invalid inference labels")
                pred = pm.label_codes(labels)
                scores = pm.evaluate(gt, pred)
                cm = np.asarray(scores["confusion"])
                pred_d, true_d = int(cm[:3, 2].sum()), int(cm[2].sum())
                row = {"scenario": scenario, "trial": seed, "method": name,
                       "frames": len(gt), "duration_s": len(gt) / batch.fps,
                       "spell_f1": scores["spell_f1_mean"], "macro_f1": scores["macro_f1"],
                       "D_precision": float(cm[2, 2] / pred_d) if pred_d else None,
                       "D_recall": float(cm[2, 2] / true_d) if true_d else None,
                       "D_predicted_frames": pred_d, "D_true_frames": true_d,
                       "accuracy": float((labels[graded] == trial.truth[graded]).mean()),
                       "abstention_rate": float((labels[graded] == "X").mean()),
                       "feature_ms": feature_ms, "decode_ms": decode_ms,
                       "total_ms": feature_ms + decode_ms,
                       "realtime_factor": (feature_ms + decode_ms) / 1000 / (len(gt) / batch.fps),
                       **boundary_errors(pm, gt, pred)}
                row["target_accuracy"] = float((labels[trial.target] == trial.truth[trial.target]).mean()) if trial.target.any() else None
                rows.append(row)
                outputs[name] = labels
                if seed == cfg["trials"][0] and name == "hierarchical":
                    trace = pd.DataFrame({"frame": batch.frame, "truth": trial.truth,
                        "observed": f.ball_observed, "stationary_s": f.stationary_seconds,
                        "local_live": result.local_live_probability, "local_home_if_live": result.local_home_given_live,
                        "smoothed_live": result.live_probability, "smoothed_home_if_live": result.home_given_live,
                        "prediction": labels})
                    trace.to_csv(out / f"{scenario}_probabilities.csv", index=False)
                if scenario.startswith("twin_"):
                    _, kind, state = scenario.split("_")
                    key = (kind, seed, name)
                    worlds = paired_predictions.setdefault(key, {})
                    worlds[state] = labels.copy()
                    if set(worlds) == {"live", "dead"}:
                        ambiguity_checks.append({"kind": kind, "trial": seed, "method": name,
                                                 "identical_predictions": bool(np.array_equal(worlds["live"], worlds["dead"]))})
            folder = out / "trials" / scenario
            folder.mkdir(parents=True, exist_ok=True)
            pd.DataFrame({name: outputs[name] for name in sorted(outputs)}).to_csv(folder / f"{seed}.csv", index=False)
            _json(folder / f"{seed}.json", trial.description)
        print(f"Completed {scenario}: {len(cfg['trials'])} trials x {len(runners)} methods", flush=True)
    table = pd.DataFrame(rows).sort_values(["scenario", "trial", "method"]).reset_index(drop=True)
    table.to_csv(out / "metrics.csv", index=False)
    summary = summarise_trials(table, METRICS, cfg["bootstrap_draws"], cfg["bootstrap_seed"])
    summary.to_csv(out / "confidence.csv", index=False)
    deltas = paired_deltas(table, METRICS[:5], draws=cfg["bootstrap_draws"], seed=cfg["bootstrap_seed"])
    deltas.to_csv(out / "paired_deltas.csv", index=False)
    diagnosis = diagnose_legacy(out)
    _json(out / "ambiguity_checks.json", ambiguity_checks)
    _json(out / "config.json", cfg)
    _json(out / "manifest.json", {"scope": "synthetic only; no fitting; no competition inference",
        "python": sys.version, "platform": platform.platform(), "numpy": np.__version__,
        "pandas": pd.__version__, "config_sha256": sha256(cfg_path),
        "requirements_sha256": sha256(ROOT / "requirements.lock.txt"),
        "source_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in sorted((ROOT / "src").rglob("*.py"))},
        "baseline_check": baseline_check, "official_commit": verify()["commit"],
        "hierarchical_config": asdict(HierarchicalConfig(**cfg["hierarchical"])),
        "trial_count": len(cfg["scenarios"]) * len(cfg["trials"]), "method_runs": len(table),
        "uncertainty": "95% whole-trial percentile bootstrap; paired trial IDs; conditional on generator",
        "runtime": "warm, counterbalanced single-host wall time; extraction + decoder; excludes I/O/scoring"})
    if make_report:
        from .phase1_report import write_report
        write_report(table, summary, diagnosis, out)
    return table
