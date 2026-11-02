"""Additional diagnostics; official scoring functions remain untouched."""
import numpy as np
import pandas as pd


def _boundaries(pm, codes, runs):
    out = {}
    for block, (a, b) in enumerate(runs):
        for start, stop, team in pm.possession_spells(codes, [(a, b)]):
            if start > a:
                out.setdefault((block, "start", team), []).append(start)
            if stop < b:
                out.setdefault((block, "end", team), []).append(stop)
    return out


def boundary_errors(pm, truth, prediction, tolerance=25):
    """Typed starts/ends, excluding known graded-block edges; match within blocks only."""
    if tolerance < 0:
        raise ValueError("nonnegative tolerance required")
    runs = pm.valid_runs(truth)
    pred = pm.fill_abstentions(prediction, runs)
    gt_edges, pred_edges = _boundaries(pm, truth, runs), _boundaries(pm, pred, runs)
    errors, missed, spurious = [], 0, 0
    for key in set(gt_edges) | set(pred_edges):
        gs, ps = gt_edges.get(key, []), pred_edges.get(key, [])
        i = j = 0
        while i < len(gs) and j < len(ps):
            delta = ps[j] - gs[i]
            if delta < -tolerance:
                spurious += 1
                j += 1
            elif delta > tolerance:
                missed += 1
                i += 1
            else:
                errors.append(abs(delta))
                i += 1
                j += 1
        missed += len(gs) - i
        spurious += len(ps) - j
    matched = len(errors)
    precision = matched / (matched + spurious) if matched + spurious else 0.0
    recall = matched / (matched + missed) if matched + missed else 0.0
    return {"boundary_precision": precision, "boundary_recall": recall,
            "boundary_f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
            "boundary_missed": missed, "boundary_spurious": spurious, "boundary_matched": matched,
            "boundary_mae_frames": float(np.mean(errors)) if errors else None,
            "boundary_p90_frames": float(np.percentile(errors, 90)) if errors else None}


def summarise_trials(table, metrics, draws=2000, seed=1701):
    """Whole-trial bootstrap of equally weighted trial means; preserve undefined values as NaN."""
    rows = []
    for (scenario, method), group in table.groupby(["scenario", "method"], sort=True):
        group = group.sort_values("trial")
        rng = np.random.default_rng(seed)
        picks = rng.integers(0, len(group), (draws, len(group)))
        for metric in metrics:
            values = group[metric].to_numpy(float)
            valid = np.isfinite(values)
            sampled = values[picks]
            counts = np.isfinite(sampled).sum(axis=1)
            boot = np.divide(np.nansum(sampled, axis=1), counts,
                             out=np.full(draws, np.nan), where=counts > 0)
            finite_boot = boot[np.isfinite(boot)]
            low, high = np.percentile(finite_boot, [2.5, 97.5]) if len(finite_boot) else (np.nan, np.nan)
            rows.append({"scenario": scenario, "method": method, "metric": metric,
                         "mean": float(values[valid].mean()) if valid.any() else np.nan,
                         "low": low, "high": high, "trials": len(group), "defined_trials": int(valid.sum())})
    return pd.DataFrame(rows)


def paired_deltas(table, metrics, reference="hierarchical", draws=2000, seed=1701):
    """Difference = comparator minus reference on the exact same synthetic trials."""
    rows = []
    for scenario, group in table.groupby("scenario", sort=True):
        ref = group[group.method == reference].set_index("trial")
        for method in sorted(set(group.method) - {reference}):
            other = group[group.method == method].set_index("trial")
            if set(ref.index) != set(other.index):
                raise ValueError("paired comparisons require identical trial IDs")
            delta = other.loc[ref.index, metrics] - ref[metrics]
            delta["scenario"], delta["method"], delta["trial"] = scenario, method, ref.index
            rows.append(summarise_trials(delta.reset_index(drop=True), metrics, draws, seed))
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
