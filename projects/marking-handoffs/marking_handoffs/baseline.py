"""Shared analysis population and an unrestricted nearest-defender baseline."""
from __future__ import annotations

import math
import numpy as np

from .data import attack_sign


def build_segments(data: dict, config: dict):
    """Contiguous attacker observations, never spanning phase or quality breaks."""
    result = []
    xy, velocity = data["xy"], data["velocity"]
    for phase_id, row in enumerate(data["phase_rows"]):
        if row["team_in_possession_phase_type"] not in config["phase_types"]:
            continue
        start, stop = int(row["frame_start"]), int(row["frame_end"])
        fr = np.arange(start, stop)
        team, period = int(row["team_in_possession_id"]), int(row["period"])
        sign = attack_sign(data["metadata"], team, period)
        attackers = np.flatnonzero((data["teams"] == team) & ~data["gk"])
        defenders = np.flatnonzero((data["teams"] != team) & ~data["gk"])
        dxy = xy[start:stop, defenders]
        dvalid = data["clean"][start:stop, defenders] & np.isfinite(velocity[start:stop, defenders]).all(axis=2)
        depth = np.where(dvalid, dxy[:, :, 0] * sign, -np.inf)
        backline = np.sort(depth, axis=1)[:, -2]
        context = (data["phase"][fr] == phase_id) & (data["possession"][fr] == team)
        context &= (dvalid.sum(axis=1) == 10) & np.isfinite(data["ball"][fr]).all(axis=1)
        for ai in attackers:
            axy = xy[fr, ai]
            valid = context & data["clean"][fr, ai] & np.isfinite(velocity[fr, ai]).all(axis=1)
            valid &= np.abs(axy[:, 1]) <= data["metadata"]["pitch_width"] / 3
            relative_depth = backline - axy[:, 0] * sign
            valid &= (relative_depth >= -3) & (relative_depth <= 25)
            valid &= (data["carrier"][fr] != data["ids"][ai])
            valid &= np.linalg.norm(data["ball"][fr] - axy, axis=1) > 3
            indices = np.flatnonzero(valid)
            chunks = np.split(indices, np.flatnonzero(np.diff(indices) != 1) + 1)
            for chunk in chunks:
                if not len(chunk):
                    continue
                frames = fr[chunk]
                # Retain active defenders only; substitutions break via eligibility.
                active = np.flatnonzero(dvalid[chunk].all(axis=0))
                if len(active) != 10:
                    # Split at changes in active lineup rather than dropping valid bins.
                    lineups = dvalid[chunk]
                    changes = np.r_[0, np.flatnonzero(np.any(lineups[1:] != lineups[:-1], axis=1)) + 1, len(chunk)]
                    subchunks = [chunk[a:b] for a, b in zip(changes[:-1], changes[1:])]
                else:
                    subchunks = [chunk]
                for sub in subchunks:
                    frames = fr[sub]
                    active_defenders = defenders[np.flatnonzero(dvalid[sub].all(axis=0))]
                    if len(active_defenders) != 10:
                        raise ValueError("Expected ten outfield defenders")
                    dist = np.linalg.norm(xy[frames, ai, None] - xy[frames[:, None], active_defenders], axis=2)
                    result.append(dict(match_id=data["metadata"]["id"], phase=phase_id, period=period,
                                       team=team, sign=sign, attacker=int(ai), defenders=active_defenders,
                                       frames=frames, distance=dist))
    return result


def nearest(distance: np.ndarray) -> np.ndarray:
    """Column ids are sorted player ids, so equal distances resolve reproducibly."""
    if distance.ndim != 2 or distance.shape[1] == 0 or not np.isfinite(distance).all():
        raise ValueError("Nearest baseline requires finite defender distances")
    return np.argmin(distance, axis=1)


def runs(labels):
    labels = np.asarray(labels)
    if not len(labels):
        return []
    boundaries = np.r_[0, np.flatnonzero(labels[1:] != labels[:-1]) + 1, len(labels)]
    return [(int(a), int(b), int(labels[a])) for a, b in zip(boundaries[:-1], boundaries[1:])]


def summary(segments, assignments, fps=10):
    frames = sum(len(s["frames"]) for s in segments)
    changes = short = assigned = 0
    for labels in assignments:
        r = runs(labels)
        changes += sum(a >= 0 and b >= 0 and a != b for a, b in zip(labels[:-1], labels[1:]))
        # Edge runs are censored by the eligibility segment boundary.
        short += sum(v >= 0 and b - a < 5 for a, b, v in r[1:-1])
        assigned += int((np.asarray(labels) >= 0).sum())
    minutes = frames / fps / 60
    return dict(eligible_attacker_frames=frames, eligible_attacker_minutes=minutes,
                segments=len(segments), direct_switches=int(changes), short_assignment_runs=int(short),
                switches_per_attacker_minute=changes / minutes if minutes else None,
                short_runs_per_attacker_minute=short / minutes if minutes else None,
                assigned_fraction=assigned / frames if frames else None)


def independent_check(data, segments, assignments, seed=20261028, samples=500):
    rng = np.random.default_rng(seed)
    checked = 0
    for si in rng.permutation(len(segments)):
        s = segments[si]
        k = int(rng.integers(len(s["frames"])))
        fr, ai = int(s["frames"][k]), s["attacker"]
        ax, ay = data["xy"][fr, ai].astype(float)
        distances = []
        for di in s["defenders"]:
            dx, dy = data["xy"][fr, di].astype(float)
            distances.append(math.hypot(dx - ax, dy - ay))
        expected = min(range(len(distances)), key=lambda j: (distances[j], data["ids"][s["defenders"][j]]))
        actual = int(assignments[si][k])
        if expected != actual or not np.isclose(distances[actual], s["distance"][k, actual], atol=1e-5):
            raise AssertionError(f"Independent nearest check failed: frame {fr}")
        checked += 1
        if checked == samples:
            break
    if not checked:
        raise AssertionError("No real eligible observations for validation")
    return dict(samples_checked=checked, all_agree=True, seed=seed,
                reference="Scalar math.hypot on raw coordinates; minimum distance then stable player id")
