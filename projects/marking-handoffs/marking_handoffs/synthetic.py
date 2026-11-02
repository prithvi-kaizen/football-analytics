"""Controlled geometric trajectories with reserved evaluation seeds."""
from __future__ import annotations
import numpy as np
from .baseline import nearest, runs
from .graph import edge_features
from .temporal import assign, longest_true


def changes(labels, valid=None):
    valid = np.ones(len(labels), bool) if valid is None else valid
    output = []
    old = -1
    for i, label in enumerate(labels):
        if not valid[i]:
            old = -1
        elif label >= 0:
            if old >= 0 and label != old:
                output.append(i)
            old = label
    return output


def scenario(kind, seed, noise=0.15):
    rng = np.random.default_rng(seed)
    n = 140
    t = np.arange(n) / 10
    a = np.column_stack([np.zeros(n), np.linspace(-5, 5, n)])
    if kind == "stationary":
        a[:, 1] = -.2
    d = np.tile([[1., -3.], [1., 3.]], (n, 1, 1))
    if kind == "gap":
        # Smooth finite-speed retreat around the crossing, then recovery.
        retreat = np.maximum(0, 1 - np.abs(np.arange(n) - 70) / 20)
        d[:, :, 0] += 9 * retreat[:, None]
    valid = np.ones(n, bool)
    if kind == "missing":
        valid[60:80] = False
    dist = np.linalg.norm(d - a[:, None], axis=2)
    truth = nearest(dist)
    truth[dist.min(axis=1) > 6] = -1
    truth[~valid] = -1
    observed_a = a + rng.normal(0, noise, a.shape)
    observed_d = d + rng.normal(0, noise, d.shape)
    # Same trailing finite-difference rule as real tracking; no centered smoothing.
    av, dv = np.zeros_like(a), np.zeros_like(d)
    av[3:] = (observed_a[3:] - observed_a[:-3]) / .3
    dv[3:] = (observed_d[3:] - observed_d[:-3]) / .3
    return observed_a, observed_d, av, dv, truth, valid


def match_changes(predicted, truth, tolerance=15):
    available = set(range(len(truth)))
    errors = []
    for p in predicted:
        candidates = [j for j in available if abs(p - truth[j]) <= tolerance]
        if candidates:
            j = min(candidates, key=lambda j: abs(p - truth[j]))
            errors.append((p - truth[j]) / 10)
            available.remove(j)
    return len(errors), len(predicted) - len(errors), len(available), errors


def evaluate(config, seeds=range(1000, 1100)):
    rows, latency = [], {"nearest": [], "proposed": []}
    for seed in seeds:
        for kind in ["stationary", "crossing", "gap", "missing"]:
            a, d, av, dv, truth, valid = scenario(kind, seed)
            features = edge_features(a, d, av, dv, 1, config)
            baseline = nearest(features["distance"])
            method = assign(features, config, reset=~valid)
            true_events = changes(truth, valid)
            for name, labels in [("nearest", baseline), ("proposed", method)]:
                pred = changes(labels, valid)
                tp, fp, fn, errors = match_changes(pred, true_events)
                latency[name].extend(errors)
                predicted_gap = ~features["plausible"].any(axis=1)
                gap_error = (longest_true(predicted_gap & valid) - longest_true((truth < 0) & valid)) / 10
                rows.append(dict(seed=seed, scenario=kind, method=name, tp=tp, fp=fp, fn=fn,
                                 switches=len(pred), true_changes=len(true_events),
                                 excess_switches=max(0, len(pred) - len(true_events)),
                                 gap_error_s=gap_error, eligible_frames=int(valid.sum())))
    metrics = {}
    for name in ["nearest", "proposed"]:
        selected = [r for r in rows if r["method"] == name]
        tp, fp, fn = (sum(r[k] for r in selected) for k in ["tp", "fp", "fn"])
        metrics[name] = dict(tp=tp, fp=fp, fn=fn, precision=tp / max(1, tp + fp),
                             recall=tp / max(1, tp + fn), f1=2 * tp / max(1, 2 * tp + fp + fn),
                             excess_switches=sum(r["excess_switches"] for r in selected),
                             median_signed_latency_s=float(np.median(latency[name])) if latency[name] else None,
                             median_absolute_latency_s=float(np.median(np.abs(latency[name]))) if latency[name] else None)
    # Gap is a property of the shared geometric support, not a baseline capability.
    gap_rows = [r for r in rows if r["method"] == "proposed" and r["scenario"] == "gap"]
    metrics["geometric_gap"] = dict(mean_absolute_longest_gap_error_s=float(np.mean([abs(r["gap_error_s"]) for r in gap_rows])),
                                    scenarios=len(gap_rows))
    b, m = metrics["nearest"], metrics["proposed"]
    reduction = 1 - m["excess_switches"] / max(1, b["excess_switches"])
    clauses = dict(excess_switch_reduction_at_least_25pct=reduction >= .25,
                   recall_loss_at_most_005=m["recall"] >= b["recall"] - .05,
                   median_latency_at_most_1s=m["median_signed_latency_s"] is not None and 0 <= m["median_signed_latency_s"] <= 1)
    metrics["hypothesis"] = dict(clauses=clauses, all_pass=all(clauses.values()), excess_switch_reduction=reduction)
    metrics["protocol"] = dict(noise_sd_m=.15, seeds=[min(seeds), max(seeds)], trajectories=len(rows) // 2,
                                tolerance_s=1.5, truth="Noiseless instantaneous nearest within 6 m; missing interval resets identity",
                                warning="Controlled geometric simulation, not tactical or communication labels")
    # Seed clusters retain dependence across scenarios generated with the same noise.
    per_seed = []
    for seed in seeds:
        per_seed.append([[sum(r[k] for r in rows if r["seed"] == seed and r["method"] == name)
                          for k in ["tp", "fp", "fn"]] for name in ["nearest", "proposed"]])
    counts = np.array(per_seed)
    rng = np.random.default_rng(config["seed"])
    draws = rng.integers(len(counts), size=(2000, len(counts)))
    sums = counts[draws].sum(axis=1)
    recall = sums[:, :, 0] / np.maximum(1, sums[:, :, 0] + sums[:, :, 2])
    precision = sums[:, :, 0] / np.maximum(1, sums[:, :, 0] + sums[:, :, 1])
    metrics["seed_cluster_bootstrap"] = dict(replicates=2000, clusters=len(counts),
        recall_delta_95pct=np.quantile(recall[:, 1] - recall[:, 0], [.025, .975]).tolist(),
        proposed_precision_95pct=np.quantile(precision[:, 1], [.025, .975]).tolist(),
        scope="Noise-seed resampling for these four specified geometric scenarios only")
    return metrics, rows
