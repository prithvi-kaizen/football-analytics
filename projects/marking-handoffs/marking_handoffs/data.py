"""Strict JSONL loading; preserve unknown observations instead of imputing coverage."""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

import numpy as np


def phase_context(path: Path, metadata: dict, n: int):
    team = np.full(n, -1, dtype=np.int32)
    phase = np.full(n, -1, dtype=np.int32)
    period = np.zeros(n, dtype=np.int8)
    end = np.zeros(n, dtype=np.int32)
    with path.open() as f:
        rows = list(csv.DictReader(f))
    for i, row in enumerate(rows):
        start, stop, per = (int(row[k]) for k in ["frame_start", "frame_end", "period"])
        if int(row["match_id"]) != metadata["id"] or not 0 <= start < stop <= n or per not in [1, 2]:
            raise ValueError("Invalid phase interval")
        if np.any(phase[start:stop] >= 0):
            raise ValueError("Overlapping phase intervals")
        tid = int(row["team_in_possession_id"])
        sign = attack_sign(metadata, tid, per)
        if row["attacking_side"] != ("left_to_right" if sign == 1 else "right_to_left"):
            raise ValueError("Phase direction contradicts metadata")
        team[start:stop], phase[start:stop], period[start:stop], end[start:stop] = tid, i, per, stop
    return team, phase, period, end, rows


def attack_sign(metadata: dict, team_id: int, period: int) -> int:
    if period not in [1, 2]:
        raise ValueError("Unsupported period")
    if team_id not in [metadata["home_team"]["id"], metadata["away_team"]["id"]]:
        raise ValueError("Unknown team")
    direction = metadata["home_team_side"][period - 1]
    if direction not in ["left_to_right", "right_to_left"]:
        raise ValueError("Unknown attack direction")
    sign = 1 if direction == "left_to_right" else -1
    return sign if team_id == metadata["home_team"]["id"] else -sign


def clock(frame: int, period: int, metadata: dict) -> str:
    p = next(p for p in metadata["match_periods"] if p["period"] == period)
    t = (period - 1) * 2700 + (frame - p["start_frame"]) / 10
    return f"{int(t // 60):02d}:{t % 60:04.1f}"


def load_match(raw: Path, mid: int):
    metadata = json.loads((raw / f"{mid}_match.json").read_text())
    if metadata["id"] != mid:
        raise ValueError("Metadata match id mismatch")
    ids = sorted(p["id"] for p in metadata["players"])
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate player metadata")
    players = {p["id"]: p for p in metadata["players"]}
    index = {pid: i for i, pid in enumerate(ids)}
    # Source frame numbers are dense here; missing frames stay unknown.
    n = max(p["end_frame"] for p in metadata["match_periods"]) + 20
    xy = np.full((n, len(ids), 2), np.nan, dtype=np.float32)
    detected = np.zeros((n, len(ids)), dtype=bool)
    period = np.zeros(n, dtype=np.int8)
    present = np.zeros(n, dtype=bool)
    ball = np.full((n, 2), np.nan, dtype=np.float32)
    poss = np.full(n, -1, dtype=np.int32)
    carrier = np.full(n, -1, dtype=np.int32)
    audit = Counter()
    previous = -1
    source_keys, sample = None, None
    with (raw / f"{mid}_tracking_extrapolated.jsonl").open() as f:
        for line_number, line in enumerate(f, 1):
            record = json.loads(line)
            fr = record["frame"]
            if not isinstance(fr, int) or fr <= previous or fr >= n:
                raise ValueError(f"Duplicate, non-increasing or invalid frame at line {line_number}")
            previous = fr
            source_keys = list(record)
            present[fr] = True
            audit["source_frames"] += 1
            per = record["period"]
            if per is None:
                audit["null_period_frames"] += 1
                continue
            if per not in [1, 2]:
                raise ValueError("Unexpected period")
            period[fr] = per
            if record["player_data"] and sample is None:
                sample = record
            group = (record.get("possession") or {}).get("group")
            poss[fr] = {"home team": metadata["home_team"]["id"],
                        "away team": metadata["away_team"]["id"]}.get(group, -1)
            carrier[fr] = (record.get("possession") or {}).get("player_id") or -1
            b = record.get("ball_data") or {}
            if b.get("x") is not None and b.get("y") is not None:
                ball[fr] = b["x"], b["y"]
            seen = set()
            for p in record["player_data"]:
                pid = p["player_id"]
                if pid in seen:
                    raise ValueError(f"Duplicate player {pid} at {fr}")
                seen.add(pid)
                audit["player_rows"] += 1
                if pid not in index:
                    raise ValueError("Unknown player")
                if p.get("x") is None or p.get("y") is None or not np.isfinite([p["x"], p["y"]]).all():
                    audit["invalid_coordinates"] += 1
                    continue
                if abs(p["x"]) > metadata["pitch_length"] / 2 + 5 or abs(p["y"]) > metadata["pitch_width"] / 2 + 5:
                    audit["out_of_bounds_rows"] += 1
                    continue
                xy[fr, index[pid]] = p["x"], p["y"]
                detected[fr, index[pid]] = p.get("is_detected") is True
                audit["detected_rows"] += p.get("is_detected") is True
                audit["extrapolated_rows"] += p.get("is_detected") is not True
    n = previous + 1
    xy, detected, period, ball, poss, carrier, present = [a[:n] for a in [xy, detected, period, ball, poss, carrier, present]]
    finite = np.isfinite(xy).all(axis=2)
    speeds = np.linalg.norm(np.diff(xy, axis=0), axis=2) * 10
    contiguous = (period[1:] == period[:-1]) & (period[1:] > 0)
    jumps = (speeds > 12.5) & contiguous[:, None]
    audit["speed_steps_above_12_5_mps"] = int(jumps.sum())
    clean = finite.copy()
    clean[1:] &= ~jumps
    clean[:-1] &= ~jumps
    # Trailing 0.3s velocity, valid only across observed contiguous positions.
    velocity = np.full_like(xy, np.nan)
    valid = clean[3:] & clean[2:-1] & clean[1:-2] & clean[:-3]
    valid &= ((period[3:] == period[:-3]) & (period[3:] > 0))[:, None]
    delta = (xy[3:] - xy[:-3]) / 0.3
    velocity[3:] = np.where(valid[:, :, None], delta, np.nan)
    pt, phase, pp, phase_end, rows = phase_context(raw / f"{mid}_phases_of_play.csv", metadata, n)
    mismatch = (phase >= 0) & (pp != period)
    audit["phase_period_mismatch_frames"] = int(mismatch.sum())
    # Provider intervals can span null tracking periods; quarantine those frames.
    phase[mismatch], pt[mismatch], phase_end[mismatch] = -1, -1, 0
    audit.update(dict(match_id=mid, period_frames=int((period > 0).sum()),
                      missing_source_frames=int((~present).sum()), phase_frames=int((phase >= 0).sum()),
                      missing_ball_period_frames=int((~np.isfinite(ball).all(axis=1) & (period > 0)).sum()),
                      phase_possession_disagreements=int(((pt != poss) & (pt >= 0) & (poss >= 0)).sum()),
                      players=len(ids)))
    audit["detection_fraction"] = audit["detected_rows"] / max(1, audit["detected_rows"] + audit["extrapolated_rows"])
    audit["player_count_distribution"] = {str(k): int(v) for k, v in zip(*np.unique(finite[period > 0].sum(axis=1), return_counts=True))}
    audit["schema_keys"] = source_keys
    audit["sample_record"] = sample
    return dict(metadata=metadata, ids=np.array(ids), xy=xy, detected=detected, clean=clean,
                velocity=velocity, period=period, ball=ball, possession=poss, carrier=carrier,
                phase_team=pt, phase=phase, phase_end=phase_end, phase_rows=rows,
                teams=np.array([players[p]["team_id"] for p in ids]),
                gk=np.array([players[p]["player_role"]["acronym"] == "GK" for p in ids]), audit=dict(audit))
