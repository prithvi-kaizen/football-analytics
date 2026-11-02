"""Bounded JSON interface for the public explorer, using unchanged research implementations.

No uploads, dataset discovery, file paths or arbitrary Python are accepted by this interface.
"""
from dataclasses import replace
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np

from .event_fusion import fuse_events
from .event_worlds import generate_twins
from .features import extract
from .hierarchical import hierarchical
from .models import hmm, state_machine
from .phase1_experiments import methods
from .phase1_metrics import boundary_errors
from .schema import TrackingBatch
from .synthetic import SyntheticConfig, generate
from .synthetic_tags import observe_actions, uninformative_tags

NAMES = {
    "nearest": "Nearest observed team", "state_machine": "Control state machine", "hmm": "Temporal HMM",
    "hierarchical": "Hierarchical model", "sm_no_stationary": "State machine · no stationarity",
    "hmm_no_stationary": "HMM · no stationarity", "hier_no_stationary": "Hierarchy · no stationarity",
    "hier_missing_as_static": "Hierarchy · missing treated as static", "hier_no_duration": "Hierarchy · no duration prior",
    "hier_no_continuity": "Hierarchy · no team continuity", "reference_raw": "Reference · raw nearest player",
    "reference_25": "Reference · ±25-frame vote", "reference_50": "Reference · ±50-frame vote",
    "reference_125": "Reference · ±125-frame vote", "event_conservative": "Conservative event evidence",
    "event_probabilistic": "Probabilistic event fusion"}


def metric_module():
    try:
        import explorer_metrics
        return explorer_metrics
    except ImportError:
        from .official import metrics_module
        return metrics_module()


def reference_module():
    try:
        import explorer_reference
        return explorer_reference
    except ImportError:
        from .official import DEFAULT_OFFICIAL
        spec = importlib.util.spec_from_file_location("explorer_reference", DEFAULT_OFFICIAL / "starter/baseline.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


def finite_list(values, decimals=3):
    array = np.asarray(values)
    if np.issubdtype(array.dtype, np.floating):
        array = np.round(array, decimals).astype(object)
        array[~np.isfinite(np.asarray(values, dtype=float))] = None
    return array.tolist()


def _scores(truth, labels, pm):
    if truth is None:
        return None
    gt, pred = pm.label_codes(truth), pm.label_codes(labels)
    score = pm.evaluate(gt, pred)
    cm = np.asarray(score["confusion"])
    pred_d, gt_d = cm[:3, 2].sum(), cm[2].sum()
    return {"macro_f1": score["macro_f1"], "spell_f1": score["spell_f1_mean"],
            "D_precision": float(cm[2, 2] / pred_d) if pred_d else None,
            "D_recall": float(cm[2, 2] / gt_d) if gt_d else None,
            "possessions": score["n_pred_spells"], "true_possessions": score["n_gt_spells"],
            "accuracy": score["accuracy"], "graded_frames": score["n_graded"],
            "abstained_frames": score["n_abstain_on_graded"], **boundary_errors(pm, gt, pred)}


def describe_batch(batch, truth, title, config=None, tags=None):
    f, pm = extract(batch), metric_module()
    outputs = {name: runner(f) for name, runner in methods({}).items()}
    # The supplied smoothing implementation is used unchanged; only the input adapter is new.
    dh = np.where(np.isfinite(f.nearest_home_m), f.nearest_home_m, np.inf)
    da = np.where(np.isfinite(f.nearest_away_m), f.nearest_away_m, np.inf)
    codes = np.where(np.minimum(dh, da) == np.inf, -1, np.where(dh <= da, 0, 1))
    for window in (0, 25, 50, 125):
        name = "reference_raw" if not window else f"reference_{window}"
        labels = reference_module().smooth(codes, window)
        labels[batch.period == 0] = "X"
        outputs[name] = labels
    if tags is not None:
        for mode in ("conservative", "probabilistic"):
            outputs["event_" + mode] = fuse_events(f, tags, mode)
    model_results = []
    order = ["nearest", "state_machine", "hmm", "hierarchical", "reference_raw", "reference_25", "reference_50", "reference_125"]
    order += [name for name in outputs if name not in order]
    for name in order:
        value = outputs[name]
        labels = value.labels if hasattr(value, "labels") else value
        model_results.append({"id": name, "name": NAMES[name], "labels": "".join(labels),
                              "group": "reference" if name.startswith("reference_") else "ablation" if name not in ("nearest", "state_machine", "hmm", "hierarchical") and not name.startswith("event_") else "event" if name.startswith("event_") else "baseline",
                              "metrics": _scores(truth, labels, pm)})
    return {"title": title, "fps": batch.fps, "frames": len(batch.frame), "pitch": batch.pitch,
            "truth": "".join(truth) if truth is not None else None,
            "tracking": {"ball": finite_list(batch.ball), "home": finite_list(batch.home), "away": finite_list(batch.away),
                         "period": finite_list(batch.period), "time_s": finite_list(batch.time_s),
                         "home_distance": finite_list(f.nearest_home_m), "away_distance": finite_list(f.nearest_away_m),
                         "ball_speed": finite_list(f.ball_speed_mps), "reliability": finite_list(f.reliability)},
            "models": model_results, "config": config, "provenance": batch.provenance,
            "metrics_scope": "synthetic single-scenario diagnostics" if truth is not None else "unlabelled public tracking; no accuracy evaluation",
            "runtime": {"python": sys.version.split()[0], "numpy": np.__version__}}


def scenario(request=None):
    request = request or {}
    allowed = {"seed", "mechanism", "noise", "loss", "gap_start", "gap_duration"}
    if set(request) - allowed:
        raise ValueError("unsupported scenario parameter")
    config = {"seed": 101, "mechanism": "ordinary", "noise": 0.12, "loss": 0.05,
              "gap_start": 12.0, "gap_duration": 6.0, **request}
    seed = config["seed"]
    if not isinstance(seed, int) or isinstance(seed, bool) or not 1 <= seed <= 99999:
        raise ValueError("seed must be an integer in 1..99999")
    limits = {"noise": (0, .5), "loss": (0, .7), "gap_start": (0, 110), "gap_duration": (0, 15)}
    for name, (lo, hi) in limits.items():
        if not np.isfinite(config[name]) or not lo <= config[name] <= hi:
            raise ValueError(f"invalid {name}")
    if config["mechanism"] not in ("ordinary", "stationary_live", "contested", "identity_switches", "player_gaps"):
        raise ValueError("unknown synthetic mechanism")
    gen = SyntheticConfig(noise_m=config["noise"], occlusion_rate=config["loss"],
                          stationary_live=config["mechanism"] == "stationary_live",
                          contested=config["mechanism"] == "contested",
                          identity_switches=config["mechanism"] == "identity_switches",
                          player_gap_rate=.35 if config["mechanism"] == "player_gaps" else .01)
    match = generate(gen, seed)
    ball = match.tracking.ball.copy()
    start = round(config["gap_start"] * match.tracking.fps)
    stop = start + round(config["gap_duration"] * match.tracking.fps)
    ball[start:stop] = np.nan
    return describe_batch(replace(match.tracking, ball=ball), match.truth, "A ball disappears across a handover", config)


def observability(request=None):
    request = request or {}
    if set(request) - {"seed", "kind", "evidence"}:
        raise ValueError("unsupported observability parameter")
    seed, kind, evidence = request.get("seed", 22001), request.get("kind", "static"), request.get("evidence", "none")
    if not isinstance(seed, int) or not 1 <= seed <= 99999 or kind not in ("static", "invisible") or evidence not in ("none", "independent", "null"):
        raise ValueError("invalid observability settings")
    live, dead = generate_twins(kind, seed)
    worlds, summaries = [], []
    for world in (live, dead):
        tags = ()
        if evidence == "independent":
            tags = observe_actions(world.visible_cues(), world.tracking.period, seed + 900000)
        elif evidence == "null":
            tags = uninformative_tags(world.tracking.period, seed + 5)
        data = describe_batch(world.tracking, world.truth, "Same tracking, different hidden state", tags=tags)
        data["tags"] = [{"start": e.start, "stop": e.stop, "code": e.code, "team": e.team_hint} for e in tags]
        target = np.flatnonzero(world.target)
        data["target"] = [int(target[0]), int(target[-1]) + 1]
        worlds.append(data)
    pm = metric_module()
    for model in worlds[0]["models"]:
        key = model["id"]
        accuracies = []
        for data, world in zip(worlds, (live, dead)):
            labels = next(m["labels"] for m in data["models"] if m["id"] == key)
            filled = pm.fill_abstentions(pm.label_codes(labels), pm.valid_runs(pm.label_codes(world.truth)))
            accuracies.append(float((filled[world.target] == pm.label_codes(world.truth)[world.target]).mean()))
        summaries.append({"id": key, "balanced_target_accuracy": sum(accuracies) / 2})
    return {"worlds": worlds, "identical_tracking": worlds[0]["tracking"] == worlds[1]["tracking"],
            "evidence": evidence, "seed": seed, "kind": kind, "summary": summaries,
            "scope": "One synthetic pair; illustrative, not a benchmark estimate"}


def run_json(mode, request_json="{}"):
    request = json.loads(request_json)
    if not isinstance(request, dict):
        raise ValueError("JSON object required")
    if mode == "scenario":
        output = scenario(request)
    elif mode == "observability":
        output = observability(request)
    else:
        raise ValueError("unknown explorer operation")
    return json.dumps(output, allow_nan=False, separators=(",", ":"))
