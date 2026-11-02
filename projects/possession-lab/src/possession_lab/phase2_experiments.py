"""Paired synthetic event-channel experiment; historical files are never overwritten."""
import argparse
from dataclasses import asdict, replace
import json
from pathlib import Path
import platform
import sys
from time import perf_counter

import numpy as np
import pandas as pd

from .event_fusion import FusionConfig, fuse_events
from .event_worlds import generate_twins, generate_world
from .features import extract
from .hierarchical import hierarchical
from .models import hmm
from .official import ROOT, metrics_module, sha256, verify
from .phase1_metrics import boundary_errors, paired_deltas, summarise_trials
from .synthetic_tags import AnnotationConfig, observe_actions, relocate_tags, uninformative_tags

METRICS = ["spell_f1", "macro_f1", "D_precision", "D_recall", "boundary_f1", "boundary_missed",
           "boundary_spurious", "boundary_mae_frames", "restart_precision", "restart_recall",
           "restart_mae_frames", "accuracy", "occluded_accuracy", "false_D_live", "wrong_team_live",
           "abstention_rate", "target_accuracy", "target_filled_accuracy", "decode_ms", "feature_ms", "total_ms"]
METHODS = ("hmm", "hierarchical", "conservative", "probabilistic", "tags_shuffled", "tags_shifted",
           "tags_uninformative", "no_team", "no_restarts", "restart_only", "ball_mask")


def save_json(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n")


def verify_phase1_freeze():
    frozen = json.loads((ROOT / "docs/phase2/phase1_freeze.json").read_text())
    for name, digest in frozen["files"].items():
        if sha256(ROOT / name) != digest:
            raise AssertionError(f"frozen Phase 1 file changed: {name}")
    return len(frozen["files"])


def reproduce_history(out):
    """Recompute elsewhere; timing fields are excluded from equality, historical files stay intact."""
    from .phase1_experiments import evaluate_phase1, verify_legacy
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    receipt = verify_legacy(recompute=True)
    table = evaluate_phase1(ROOT / "configs/phase1.json", out / "phase1", make_report=False)
    old = pd.read_csv(ROOT / "outputs/phase1/metrics.csv")
    timing = {"feature_ms", "decode_ms", "total_ms", "realtime_factor"}
    cols = [c for c in table.columns if c not in timing]
    pd.testing.assert_frame_equal(table[cols].reset_index(drop=True), old[cols].reset_index(drop=True),
                                  check_exact=False, atol=1e-14, rtol=0)
    receipt.update({"phase1_score_rows_reproduced": len(table), "frozen_files_intact": verify_phase1_freeze()})
    save_json(out / "receipt.json", receipt)
    return receipt


def run_method(name, f, tags, controls, cfg):
    if name == "hmm":
        return hmm(f)
    if name == "hierarchical":
        return hierarchical(f)
    if name == "conservative":
        return fuse_events(f, tags, "conservative", cfg)
    if name in controls:
        return fuse_events(f, controls[name], cfg=cfg)
    if name == "no_team":
        tags = tuple(replace(e, team_hint=None) for e in tags)
    elif name == "no_restarts":
        tags = tuple(e for e in tags if e.code != "set pieces")
    elif name == "restart_only":
        tags = tuple(e for e in tags if e.code == "set pieces")
    elif name == "ball_mask":
        cfg = replace(cfg, event_coverage=False)
    elif name != "probabilistic":
        raise ValueError("unknown Phase 2 method")
    return fuse_events(f, tags, cfg=cfg)


def restart_errors(pm, gt, pred):
    # Same destination-typed transition matching as official, but restrict to D -> alive.
    runs = pm.valid_runs(gt)
    filled = pm.fill_abstentions(pred, runs)
    matched, missed, spurious, errors = 0, 0, 0, []
    for run in runs:
        gs = [x for x in pm.transitions(gt, [run]) if x[1] == pm.D and x[2] in (pm.H, pm.A)]
        ps = [x for x in pm.transitions(filled, [run]) if x[1] == pm.D and x[2] in (pm.H, pm.A)]
        pairs, no, extra = pm.match_transitions(gs, ps, 25)
        matched += len(pairs)
        missed += len(no)
        spurious += len(extra)
        errors.extend(abs(p[0] - g[0]) for g, p in pairs)
    return {"restart_precision": matched / (matched + spurious) if matched + spurious else None,
            "restart_recall": matched / (matched + missed) if matched + missed else None,
            "restart_mae_frames": float(np.mean(errors)) if errors else None,
            "restart_missed": missed, "restart_spurious": spurious}


def score(pm, world, labels, f):
    gt, pred = pm.label_codes(world.truth), pm.label_codes(labels)
    filled = pm.fill_abstentions(pred, pm.valid_runs(gt))
    result = pm.evaluate(gt, pred)
    cm = np.asarray(result["confusion"])
    predicted_dead, true_dead = int(cm[:3, 2].sum()), int(cm[2].sum())
    graded, live = world.truth != "X", np.isin(world.truth, ["H", "A"])
    occluded = graded & ~f.ball_observed
    return {"spell_f1": result["spell_f1_mean"], "macro_f1": result["macro_f1"],
            "D_precision": float(cm[2, 2] / predicted_dead) if predicted_dead else None,
            "D_recall": float(cm[2, 2] / true_dead) if true_dead else None,
            "D_predicted_frames": predicted_dead, "D_true_frames": true_dead,
            "accuracy": float((labels[graded] == world.truth[graded]).mean()),
            "occluded_accuracy": float((labels[occluded] == world.truth[occluded]).mean()) if occluded.any() else None,
            "false_D_live": float((labels[live] == "D").mean()) if live.any() else None,
            "wrong_team_live": float((np.isin(labels[live], ["H", "A"]) & (labels[live] != world.truth[live])).mean()) if live.any() else None,
            "abstention_rate": float((labels[graded] == "X").mean()),
            "target_accuracy": float((labels[world.target] == world.truth[world.target]).mean()) if world.target.any() else None,
            "target_filled_accuracy": float((filled[world.target] == gt[world.target]).mean()) if world.target.any() else None,
            **boundary_errors(pm, gt, pred), **restart_errors(pm, gt, pred)}


def _cases(cfg):
    for family in cfg["world_families"]:
        for regime in cfg["regimes"]:
            yield family, regime, "single"
    for kind in cfg["twin_kinds"]:
        for regime in cfg["twin_regimes"]:
            for state in ("live", "dead"):
                yield "twins_" + kind, regime, state


def _make_inputs(family, regime, state, trial, cfg):
    annotation_cfg = AnnotationConfig(**cfg["regimes"][regime])
    if family.startswith("twins_"):
        worlds = generate_twins(family.removeprefix("twins_"), trial)
        streams = [observe_actions(w.visible_cues(), w.tracking.period, trial + 900000,
                   annotation_cfg, np.isfinite(w.tracking.ball).all(axis=1)) for w in worlds]
        world, tags = worlds[int(state == "dead")], streams[int(state == "dead")]
        # A donor stream selected without knowing the evaluated world. Both worlds get the
        # identical control payload; this is an exact conditional-information null.
        donor = streams[int(np.random.default_rng(trial + 17).integers(0, 2))]
    else:
        world = generate_world(family, trial, occluded=regime in ("occluded", "shared_view"))
        tags = observe_actions(world.visible_cues(), world.tracking.period, trial + 900000,
                                annotation_cfg, np.isfinite(world.tracking.ball).all(axis=1))
        donor = tags
    controls = {"tags_shuffled": relocate_tags(donor, world.tracking.period, trial + 4),
                "tags_shifted": relocate_tags(donor, world.tracking.period, trial + 4, "shift"),
                "tags_uninformative": uninformative_tags(world.tracking.period, trial + 5)}
    return world, tags, controls


def evaluate_phase2(config_path, out, make_report=True):
    cfg = json.loads(Path(config_path).read_text())
    required = {"trials", "world_families", "regimes", "twin_kinds", "twin_regimes", "fusion", "bootstrap_draws", "bootstrap_seed"}
    if (set(cfg) != required or not cfg["trials"] or len(set(cfg["trials"])) != len(cfg["trials"])
            or not set(cfg["world_families"]) <= {"episodes", "renewal"}
            or not set(cfg["twin_kinds"]) <= {"static", "invisible"}
            or not set(cfg["twin_regimes"]) <= set(cfg["regimes"]) or cfg["bootstrap_draws"] <= 0):
        raise ValueError("invalid Phase 2 configuration")
    fusion = FusionConfig(**cfg["fusion"])
    for options in cfg["regimes"].values():
        AnnotationConfig(**options)
    cases = list(_cases(cfg))
    if not cases:
        raise ValueError("at least one generator/counterexample required")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    frozen_count = verify_phase1_freeze()
    pm = metrics_module()
    warm_world, warm_tags, warm_controls = _make_inputs(*cases[0], 73, cfg)
    warm_f = extract(warm_world.tracking)
    for method in METHODS:
        run_method(method, warm_f, warm_tags, warm_controls, fusion)
    rows, twin_checks = [], []
    twins_seen = {}
    for family, regime, state in cases:
        scenario = ":".join([family, regime, state])
        for trial in cfg["trials"]:
            world, tags, controls = _make_inputs(family, regime, state, trial, cfg)
            start = perf_counter()
            f = extract(world.tracking)
            feature_ms = (perf_counter() - start) * 1000
            predictions = {"frame": world.tracking.frame, "truth": world.truth, "ball_observed": f.ball_observed}
            ordered_methods = list(METHODS)
            np.random.default_rng(trial).shuffle(ordered_methods)
            for method in ordered_methods:
                start = perf_counter()
                result = run_method(method, f, tags, controls, fusion)
                elapsed = (perf_counter() - start) * 1000
                labels = result.labels.copy() if hasattr(result, "labels") else result.copy()
                labels[world.tracking.period == 0] = "X"
                row = {"scenario": scenario, "family": family, "regime": regime, "world": state,
                       "trial": trial, "method": method, "frames": len(labels), "tag_count": len(tags),
                       "unknown_team_tags": sum(e.team_hint is None for e in tags),
                       "duplicate_tags": len(tags) - len(set(tags)), "feature_ms": feature_ms,
                       "decode_ms": elapsed, "total_ms": feature_ms + elapsed,
                       **score(pm, world, labels, f)}
                rows.append(row)
                predictions[method] = labels
                if state != "single" and method in ("hmm", "hierarchical", *controls):
                    key = (family, regime, trial, method)
                    store = twins_seen.setdefault(key, {})
                    store[state] = (labels.copy(), row["target_accuracy"], row["target_filled_accuracy"])
                    if len(store) == 2:
                        identical = bool(np.array_equal(store["live"][0], store["dead"][0]))
                        balanced = (store["live"][1] + store["dead"][1]) / 2
                        balanced_filled = (store["live"][2] + store["dead"][2]) / 2
                        if not identical or max(balanced, balanced_filled) > 0.5 + 1e-12:
                            raise AssertionError("uninformative twin tags generated a false information gain")
                        twin_checks.append({"family": family, "regime": regime, "trial": trial,
                                            "method": method, "identical_predictions": identical,
                                            "balanced_target_accuracy": balanced,
                                            "balanced_filled_target_accuracy": balanced_filled})
            folder = out / "trials" / family / regime / state
            folder.mkdir(parents=True, exist_ok=True)
            pd.DataFrame(predictions).to_csv(folder / f"{trial}.csv", index=False)
            save_json(folder / f"{trial}_observed_tags.json", [asdict(e) for e in tags])
            save_json(folder / f"{trial}_control_tags.json", {name: [asdict(e) for e in seq] for name, seq in controls.items()})
            save_json(folder / f"{trial}_private_actions.json", [asdict(e) for e in world.actions])
            save_json(folder / f"{trial}_target.json", np.flatnonzero(world.target).tolist())
        print(f"Completed {scenario}: {len(cfg['trials'])} paired trials x {len(METHODS)} methods", flush=True)
    table = pd.DataFrame(rows).sort_values(["scenario", "trial", "method"]).reset_index(drop=True)
    table.to_csv(out / "metrics.csv", index=False)
    summary = summarise_trials(table, METRICS, cfg["bootstrap_draws"], cfg["bootstrap_seed"])
    summary.to_csv(out / "confidence.csv", index=False)
    deltas = paired_deltas(table, METRICS[:13], draws=cfg["bootstrap_draws"], seed=cfg["bootstrap_seed"])
    deltas.to_csv(out / "paired_deltas.csv", index=False)
    alignment = []
    for control in ("tags_shuffled", "tags_shifted", "tags_uninformative"):
        for scenario, group in table.groupby("scenario"):
            a = group[group.method == "probabilistic"].set_index("trial")
            b = group[group.method == control].set_index("trial").loc[a.index]
            d = a[METRICS[:13]] - b[METRICS[:13]]
            d["scenario"], d["method"], d["trial"] = scenario, "aligned_minus_" + control, a.index
            alignment.append(summarise_trials(d.reset_index(drop=True), METRICS[:13], cfg["bootstrap_draws"], cfg["bootstrap_seed"]))
    pd.concat(alignment, ignore_index=True).to_csv(out / "alignment_deltas.csv", index=False)
    twin_rows = table[table.world != "single"]
    balanced = twin_rows.groupby(["family", "regime", "trial", "method"], as_index=False)[["target_accuracy", "target_filled_accuracy"]].mean()
    balanced["scenario"] = balanced.family + ":" + balanced.regime
    balanced.to_csv(out / "twin_balanced.csv", index=False)
    if len(balanced):
        summarise_trials(balanced, ["target_accuracy", "target_filled_accuracy"], cfg["bootstrap_draws"], cfg["bootstrap_seed"]).to_csv(out / "twin_confidence.csv", index=False)
        paired_deltas(balanced, ["target_accuracy", "target_filled_accuracy"], draws=cfg["bootstrap_draws"], seed=cfg["bootstrap_seed"]).to_csv(out / "twin_deltas.csv", index=False)
    save_json(out / "null_twin_checks.json", twin_checks)
    save_json(out / "config.json", cfg)
    save_json(out / "manifest.json", {"scope": "synthetic event-channel experiment; no fitting or competition inference",
        "python": sys.version, "platform": platform.platform(), "numpy": np.__version__, "pandas": pd.__version__,
        "config_sha256": sha256(config_path), "requirements_sha256": sha256(ROOT / "requirements.lock.txt"),
        "source_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in sorted((ROOT / "src").rglob("*.py"))},
        "frozen_phase1_files": frozen_count, "official_files_verified": len(verify()["files"]),
        "method_runs": len(table), "world_cases": len(cases) * len(cfg["trials"]),
        "unique_null_pair_checks": len(twin_checks), "aggregation": "whole-trial paired bootstrap; paired worlds for twin accuracy"})
    if make_report:
        from .phase2_report import write_phase2_report
        write_phase2_report(table, summary, out)
    verify_phase1_freeze()
    return table


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/phase2.json")
    parser.add_argument("--out", type=Path, default=ROOT / "outputs/phase2")
    parser.add_argument("--history-only", action="store_true")
    args = parser.parse_args()
    if args.history_only:
        print(reproduce_history(args.out / "historical_reproduction"))
    else:
        result = evaluate_phase2(args.config, args.out)
        print(f"Completed {len(result)} synthetic method runs")


if __name__ == "__main__":
    main()
