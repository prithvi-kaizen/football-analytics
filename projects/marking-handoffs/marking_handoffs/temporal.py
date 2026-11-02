"""Causal hysteresis and retrospectively confirmed candidate events."""
from __future__ import annotations

import numpy as np
from .baseline import runs


def assign(features, config, reset=None):
    score, plausible, retain = (features[k] for k in ["score", "plausible", "retain"])
    n = len(score)
    reset = np.zeros(n, dtype=bool) if reset is None else np.asarray(reset)
    if config["confirm_frames"] < 1 or config["switch_margin_m"] < 0:
        raise ValueError("Invalid hysteresis parameters")
    labels = np.full(n, -1, dtype=int)
    current = pending = -1
    count = 0
    for t in range(n):
        if reset[t]:
            current = pending = -1
            count = 0
            continue
        if current >= 0 and not retain[t, current]:
            current = -1
            pending, count = -1, 0
        candidates = np.where(plausible[t], score[t], np.inf)
        best = int(np.argmin(candidates))
        if not np.isfinite(candidates[best]):
            best = -1
        challenge = best >= 0 and best != current
        if current >= 0 and challenge:
            challenge = score[t, best] + config["switch_margin_m"] < score[t, current]
        if challenge:
            if pending == best:
                count += 1
            else:
                pending, count = best, 1
            if count >= config["confirm_frames"]:
                current, pending, count = best, -1, 0
        else:
            pending, count = -1, 0
        labels[t] = current
    return labels


def longest_true(mask):
    return max((b - a for a, b, v in runs(np.asarray(mask, dtype=int)) if v == 1), default=0)


def candidate_events(labels, features, attacker_xy, config):
    """Do not bridge unknown frames: caller supplies separate contiguous segments."""
    r = runs(labels)
    events = []
    for i, (a, b, old) in enumerate(r):
        if old < 0 or b - a < config["min_stable_frames"] or i + 1 == len(r):
            continue
        j = i + 1
        if r[j][2] < 0:
            if r[j][1] - r[j][0] > config["max_bridge_frames"]:
                continue
            j += 1
        if j == len(r):
            continue
        c, d, new = r[j]
        if new < 0 or new == old or d - c < config["min_stable_frames"]:
            continue
        left, right = max(0, b - 20), min(len(labels) - 1, c + 20)
        displacement = float(np.linalg.norm(attacker_xy[right] - attacker_xy[left]))
        if displacement < config["min_attacker_movement_m"]:
            continue
        lo, hi = max(a, b - 5), min(d, c + 5)
        gap = ~features["plausible"][lo:hi].any(axis=1)
        total, longest = int(gap.sum()), longest_true(gap)
        kind = "gap" if longest >= config["gap_frames"] else "brief_gap" if total else "continuous"
        # A small score separation exposes ambiguous alternatives, not confidence.
        scores = np.sort(np.where(features["plausible"][c], features["score"][c], np.inf))
        margin = float(scores[1] - scores[0]) if len(scores) > 1 and np.isfinite(scores[:2]).all() else None
        events.append(dict(old=old, new=new, outgoing_end=b, incoming_start=c,
                           window_start=lo, window_end=hi, event_index=c,
                           gap_s=total / 10, longest_gap_s=longest / 10, category=kind,
                           unassigned_s=(c - b) / 10, attacker_displacement_m=displacement,
                           alternative_margin_m=margin, ambiguous=margin is not None and margin < 1.0))
    return events
