"""Operational diagnostics and paired phase-cluster resampling."""
import numpy as np
from .baseline import summary, runs
from .synthetic import changes


def operational(segments, assignments, features):
    metrics = summary(segments, assignments)
    unsupported = assigned = covered = total = bridged = 0
    for labels, f in zip(assignments, features):
        labels = np.asarray(labels)
        valid = labels >= 0
        assigned += int(valid.sum())
        unsupported += int((~f["plausible"][np.flatnonzero(valid), labels[valid]]).sum())
        covered += int(f["plausible"].any(axis=1).sum())
        total += len(labels)
        bridged += len(changes(labels))
    metrics.update(identity_changes_including_unassigned=int(bridged),
                   identity_changes_per_attacker_minute=bridged / metrics["eligible_attacker_minutes"] if total else None,
                   assigned_without_entry_geometry_fraction=unsupported / assigned if assigned else None,
                   geometric_cover_fraction=covered / total if total else None)
    return metrics


def phase_bootstrap(segments, baseline, proposed, seed, replicates=2000):
    phase_ids = sorted(set(s["phase"] for s in segments))
    rows = []
    for phase in phase_ids:
        ids = [i for i, s in enumerate(segments) if s["phase"] == phase]
        exposure = sum(len(segments[i]["frames"]) for i in ids) / 600
        counts = []
        for labels in [baseline, proposed]:
            counts.extend([sum(len(changes(labels[i])) for i in ids),
                           sum(sum(v >= 0 and b - a < 5 for a, b, v in runs(labels[i])[1:-1]) for i in ids)])
        rows.append([exposure] + counts)
    values = np.array(rows, dtype=float)
    rng = np.random.default_rng(seed)
    draws = rng.integers(len(values), size=(replicates, len(values)))
    totals = values[draws].sum(axis=1)
    diffs = (totals[:, 3:5] - totals[:, 1:3]) / totals[:, :1]
    overall = values.sum(axis=0)
    result = dict(clusters=len(values), replicates=replicates, seed=seed,
                  interpretation="95% percentile intervals from paired phase resampling within one held-out match; not between-match uncertainty")
    for j, name in enumerate(["identity_changes_per_attacker_minute", "short_runs_per_attacker_minute"]):
        result[name] = dict(proposed_minus_nearest=(overall[j + 3] - overall[j + 1]) / overall[0],
                            low=float(np.quantile(diffs[:, j], .025)), high=float(np.quantile(diffs[:, j], .975)))
    return result
