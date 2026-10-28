"""Causal shoulder-vector geometry. No gaze or intention is inferred."""

from collections import Counter, defaultdict
from pathlib import Path
import math
import json
import numpy as np
import pandas as pd
from .data import iter_frames, clock_seconds

TAU = 2 * math.pi


def wrap(angle):
    return (angle + math.pi) % TAU - math.pi


def shoulder_measurement(player):
    joints = player.get("joints")
    if not joints:
        return {"reason": "no_pose"}
    left = joints.get("lShoulder")
    right = joints.get("rShoulder")
    if not left or not right:
        return {"reason": "missing_shoulder"}
    a = np.asarray(left["xyz"][:2], float)
    b = np.asarray(right["xyz"][:2], float)
    error = max(float(left["p90_mae_cm"]), float(right["p90_mae_cm"]))
    if not np.isfinite([*a, *b, error]).all() or error < 0:
        return {"reason": "invalid_shoulder"}
    dx, dy = b - a
    width = math.hypot(dx, dy)
    xy = np.array([player["x"], player["y"]], float)
    return {
        "reason": "measured",
        "heading": math.atan2(dx, -dy),
        "width": width,
        "error": error,
        "midpoint_residual": float(np.linalg.norm((a + b) / 2 - xy)),
    }


def gate(sample, cfg):
    if sample.get("reason") != "measured":
        return sample.get("reason", "no_pose")
    if (
        not cfg["shoulder_width_min_m"]
        <= sample["width"]
        <= cfg["shoulder_width_max_m"]
    ):
        return "width"
    if sample["error"] > cfg["shoulder_error_cm"]:
        return "error"
    if not math.isfinite(sample["midpoint_residual"]):
        return "pose_xy_missing"
    if sample["midpoint_residual"] > 2:
        return "pose_xy_misalignment"
    if "tracking_residual" in sample:
        if sample["tracking_residual"] is None:
            return "native_tracking_missing"
        if sample["tracking_residual"] > 2:
            return "native_tracking_misalignment"
    return "valid"


def causal_heading(samples, cutoff, cfg):
    """cutoff in seconds on global video clock; never round to a future pose frame."""
    window = cfg["smooth_seconds"]
    minimum = 1 if window == 0 else cfg["minimum_pose_samples"]
    candidates = [
        s
        for s in samples
        if 0 <= cutoff - s["frame"] / 25 <= max(window, 0.04) + 1e-8
        and gate(s, cfg) == "valid"
    ]
    if window == 0 and candidates:
        candidates = [max(candidates, key=lambda s: s["frame"])]
    if len(candidates) < minimum:
        return None, "insufficient_samples"
    newest = max(s["frame"] / 25 for s in candidates)
    if cutoff - newest > cfg["max_latest_age_seconds"] + 1e-8:
        return None, "stale"
    # Do not smooth across a missing-pose gap longer than 80 ms.
    times = sorted(s["frame"] / 25 for s in candidates)
    if len(times) > 1 and max(np.diff(times)) > 0.080001:
        return None, "gap"
    vec = np.mean(
        [[math.cos(s["heading"]), math.sin(s["heading"])] for s in candidates], axis=0
    )
    resultant = float(np.linalg.norm(vec))
    if resultant < cfg["minimum_resultant"]:
        return None, "incoherent"
    return {
        "heading": math.atan2(vec[1], vec[0]),
        "resultant": resultant,
        "samples": len(candidates),
        "latest_frame": max(s["frame"] for s in candidates),
        "mean_error_cm": float(np.mean([s["error"] for s in candidates])),
    }, "valid"


def extract_match(path, receptions, track, cfg, out):
    """One full streaming pass; retain only short pre-reception shoulder windows."""
    wanted = defaultdict(list)
    for r in receptions.to_dict("records"):
        for f in range(
            max(0, math.floor((r["frame"] / 10 - 0.85) * 25)),
            math.floor(r["frame"] * 2.5) + 1,
        ):
            wanted[f].append((r["event_id"], int(r["player_id"]), int(r["period"])))
    samples = defaultdict(list)
    audit = Counter()
    gates = Counter()
    periods = Counter()
    joint_counts = Counter()
    prev = -1
    players = {p["id"]: p for p in track.metadata["players"]}
    active = {}
    for pid, p in players.items():
        span = p["playing_time"]["total"]
        active[pid] = (
            (span["start_frame"] * 2.5, span["end_frame"] * 2.5)
            if span
            else (math.inf, -math.inf)
        )
    clock_diffs = []
    xy_diff = []
    frame_ranges = defaultdict(lambda: [math.inf, -math.inf])
    for row in iter_frames(path):
        f = row["frame"]
        period = row["period"]
        if f <= prev:
            raise ValueError("Pose frame order/duplicate failure")
        prev = f
        audit["frames"] += 1
        if period not in [1, 2]:
            audit["outside_period_frames"] += 1
            continue
        periods[period] += 1
        frame_ranges[period][0] = min(frame_ranges[period][0], f)
        frame_ranges[period][1] = max(frame_ranges[period][1], f)
        plist = row["player_data"]
        pids = [p["player_id"] for p in plist]
        if len(pids) != len(set(pids)):
            raise ValueError("Duplicate player ID within pose frame")
        if set(pids) - set(players):
            raise ValueError("Unknown pose player ID")
        lookup = {p["player_id"]: p for p in plist}
        frame_has_pose = False
        for player in plist:
            pid = player["player_id"]
            audit["roster_player_frames"] += 1
            is_active = active[pid][0] <= f <= active[pid][1]
            if is_active:
                audit["active_player_frames"] += 1
            if player.get("joints"):
                audit["player_frames_with_pose"] += 1
                frame_has_pose = True
                joint_counts[len(player["joints"])] += 1
                if is_active:
                    audit["active_player_frames_with_pose"] += 1
                if not player["is_detected"]:
                    audit["pose_despite_xy_not_detected"] += 1
                s = shoulder_measurement(player)
                reason = gate(s, cfg)
                gates[reason] += 1
                if reason == "valid":
                    audit["valid_shoulder_roster_player_frames"] += 1
                    if is_active:
                        audit["valid_shoulder_active_player_frames"] += 1
            else:
                gates["no_pose"] += 1
        if frame_has_pose:
            audit["frames_with_any_pose"] += 1
        if f % 5 == 0:
            tf = f * 2 // 5
            if tf < len(track.period) and track.period[tf] in [1, 2]:
                audit["exact_aligned_frames_checked"] += 1
                if period != track.period[tf]:
                    raise ValueError("Pose/tracking period mismatch")
                if row["timestamp"] is not None:
                    clock_diffs.append(
                        abs(clock_seconds(row["timestamp"]) - track.clock[tf])
                    )
                # Native tracking may have no XY while the pose file still interpolates roster locations.
                for p in plist:
                    i = track.lookup[p["player_id"]]
                    xy = track.xy[tf, i]
                    if (
                        np.isfinite(xy).all()
                        and p["x"] is not None
                        and p["y"] is not None
                    ):
                        xy_diff.append(math.hypot(p["x"] - xy[0], p["y"] - xy[1]))
        for event, pid, ep in wanted.get(f, []):
            if ep != period:
                continue
            player = lookup.get(pid)
            s = shoulder_measurement(player) if player else {"reason": "no_pose"}
            tf = f * 2 // 5
            residual = None
            if player and tf < len(track.period) and track.period[tf] == period:
                xy = track.xy[tf, track.lookup[pid]]
                if (
                    np.isfinite(xy).all()
                    and player["x"] is not None
                    and player["y"] is not None
                ):
                    residual = float(
                        math.hypot(player["x"] - xy[0], player["y"] - xy[1])
                    )
            s["tracking_residual"] = residual
            samples[event].append({"frame": f, "period": period, **s})
        if audit["frames"] % 25000 == 0:
            print(Path(path).name, "scanned", audit["frames"], "frames", flush=True)
    audit = dict(audit)
    audit.update(
        period_frames=dict(periods),
        period_frame_ranges=dict(frame_ranges),
        shoulder_gates=dict(gates),
        joint_count_distribution=dict(joint_counts),
        maximum_exact_alignment_clock_error_s=max(clock_diffs) if clock_diffs else None,
        exact_alignment_xy_residual_quantiles_m=np.quantile(
            xy_diff, [0, 0.5, 0.9, 0.99, 1]
        ).tolist()
        if xy_diff
        else [],
    )
    audit["exact_alignment_player_comparisons"] = len(xy_diff)
    audit["exact_alignment_player_residual_above_2m"] = sum(d > 2 for d in xy_diff)
    if clock_diffs and max(clock_diffs) > 0.001:
        raise ValueError("Clock alignment exceeds 1 ms at exact frames")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "pose_audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    (out / "shoulder_windows.json").write_text(
        json.dumps(samples, separators=(",", ":"))
    )
    return dict(samples), audit


def dot_direction(theta, dx, dy):
    norm = math.hypot(dx, dy)
    if not math.isfinite(norm) or norm < 0.1:
        return None
    return (math.cos(theta) * dx + math.sin(theta) * dy) / norm


def make_features(receptions, windows, cfg, cutoff_shift=0, noise_degrees=0):
    rows = []
    reasons = Counter()
    rng = np.random.default_rng(cfg["seed"])
    for r in receptions.to_dict("records"):
        samples = windows.get(r["event_id"], [])
        cut = r["frame"] / 10 + cutoff_shift
        h, reason = causal_heading(samples, cut, cfg)
        if h is None:
            reasons[reason] += 1
            continue
        theta = h["heading"] + rng.normal(0, math.radians(noise_degrees))
        ball = dot_direction(theta, r["ball_dx"], r["ball_dy"])
        opp = dot_direction(theta, r["opp_dx"], r["opp_dy"])
        if ball is None or opp is None:
            reasons["direction_context_missing"] += 1
            continue
        prev, _ = causal_heading(samples, cut - cfg["turn_lookback_seconds"], cfg)
        turn = (
            abs(
                wrap(
                    theta
                    - (prev["heading"] + rng.normal(0, math.radians(noise_degrees)))
                )
            )
            / cfg["turn_lookback_seconds"]
            if prev
            else 0
        )
        rel = wrap(theta - (0 if r["attack_sign"] == 1 else math.pi))
        degrees = abs(math.degrees(rel))
        cat = (
            "forward"
            if degrees < 45
            else ("sideways" if degrees <= 135 else "backward")
        )
        r.update(
            facing_attack_cos=math.cos(rel),
            facing_attack_sin=math.sin(rel),
            facing_ball_cos=ball,
            facing_opponent_cos=opp,
            pre_turn_abs_rad_s=turn,
            turn_missing=int(prev is None),
            heading=theta,
            orientation_category=cat,
            pose_samples=h["samples"],
            pose_resultant=h["resultant"],
            shoulder_mean_error_cm=h["mean_error_cm"],
            latest_pose_frame=h["latest_frame"],
            feature_cutoff=cut,
        )
        if r["latest_pose_frame"] / 25 > cut + 1e-8:
            raise AssertionError("Future pose leakage")
        reasons["valid"] += 1
        rows.append(r)
    return pd.DataFrame(rows), dict(reasons)
