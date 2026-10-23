from __future__ import annotations

import math
import re
import numpy as np
import pandas as pd

ON_BALL = {"Pass", "Carry", "Shot", "Dribble", "Miscontrol", "Dispossessed", "Ball Recovery",
           "Interception", "Clearance", "Goal Keeper", "50/50", "Shield", "Error"}
MOVES = {"Pass", "Carry"}
CONTROLLED = {"Pass", "Carry", "Shot", "Dribble", "Miscontrol", "Dispossessed", "Shield"}


def seconds(timestamp: str) -> float:
    if not re.fullmatch(r"\d{2}:\d{2}:\d{2}(?:\.\d+)?", timestamp):
        raise ValueError(f"Invalid timestamp: {timestamp}")
    h, m, s = map(float, timestamp.split(":"))
    if m >= 60 or s >= 60:
        raise ValueError(f"Invalid timestamp: {timestamp}")
    return h * 3600 + m * 60 + s


def coordinate(value) -> tuple[float, float]:
    if value is None:
        return math.nan, math.nan
    if not isinstance(value, (list, tuple)) or len(value) < 2:
        raise ValueError(f"Invalid coordinate: {value}")
    x, y = map(float, value[:2])
    if not (math.isfinite(x) and math.isfinite(y) and 0 <= x <= 120 and 0 <= y <= 80):
        raise ValueError(f"Out-of-range pitch coordinate: {value}")
    return x, y


def union_seconds(intervals) -> float:
    end = -math.inf
    total = 0.0
    for a, b in sorted(intervals):
        if b < a:
            raise ValueError("Negative interval")
        total += max(0.0, b - max(a, end))
        end = max(end, b)
    return total


def parse_events(raw: list[dict], match: dict) -> pd.DataFrame:
    """Preserve event order; state is the score *before* the indexed event."""
    mid = match["match_id"]
    home = match["home_team"]["home_team_id"]
    away = match["away_team"]["away_team_id"]
    scores = {home: 0, away: 0}
    ids, indices = set(), set()
    rows = []
    for event in sorted(raw, key=lambda e: e["index"]):
        if event["id"] in ids or event["index"] in indices:
            raise ValueError(f"Duplicate event id/index in match {mid}")
        ids.add(event["id"])
        indices.add(event["index"])
        if event["period"] == 5:
            continue
        if event["period"] not in (1, 2, 3, 4):
            raise ValueError("Unsupported period")
        kind = event["type"]["name"]
        team = event["team"]["id"]
        owner = event["possession_team"]["id"]
        if team not in scores or owner not in scores:
            raise ValueError("Event team does not match fixture")
        payload = event.get(kind.lower().replace(" ", "_"), {})
        x, y = coordinate(event.get("location"))
        # Shot endpoints can be outside the pitch or have a third (height) component.
        ex, ey = coordinate(payload.get("end_location")) if kind in MOVES else (math.nan, math.nan)
        raw_duration = float(event.get("duration") or 0)
        if not math.isfinite(raw_duration) or raw_duration < -0.1:
            raise ValueError("Invalid event duration")
        # Tiny vendor timing inconsistencies contribute zero active time, with a retained flag.
        duration = max(0.0, raw_duration)
        outcome = payload.get("outcome", {}).get("name", "")
        complete = kind == "Carry" or (kind == "Pass" and outcome == "")
        penalty = kind == "Shot" and payload.get("type", {}).get("name") == "Penalty"
        is_goal = kind == "Shot" and outcome == "Goal"
        diff = scores[team] - scores[away if team == home else home]
        t = seconds(event["timestamp"])
        row = {"match_id": mid, "event_id": event["id"], "index": event["index"],
               "period": event["period"], "t": t,
               "display_minute": {1: 0, 2: 45, 3: 90, 4: 105}[event["period"]] + t / 60,
               "possession": event["possession"], "team_id": team, "team": event["team"]["name"],
               "owner_id": owner, "owner": event["possession_team"]["name"], "type": kind,
               "player": event.get("player", {}).get("name", ""), "x": x, "y": y,
               "end_x": ex, "end_y": ey, "duration": duration, "raw_duration": raw_duration,
               "duration_repaired": raw_duration < 0, "complete": complete,
               "outcome": outcome, "penalty": penalty, "goal": is_goal,
               "xg": float(payload.get("statsbomb_xg", 0)) if kind == "Shot" else 0.0,
               "home_score_before": scores[home], "away_score_before": scores[away],
               "score_state": "winning" if diff > 0 else "losing" if diff < 0 else "drawing",
               "play_pattern": event.get("play_pattern", {}).get("name", "Unknown")}
        rows.append(row)
        if is_goal:
            scores[team] += 1
        elif kind == "Own Goal Against":
            scores[away if team == home else home] += 1
        # Own Goal For is the paired annotation; never count it a second time.
    frame = pd.DataFrame(rows)
    if frame.empty:
        raise ValueError("Empty match")
    if scores != {home: match["home_score"], away: match["away_score"]}:
        raise ValueError(f"Score reconciliation failed for {mid}: {scores}")
    if (frame["xg"].isna() | ~frame["xg"].between(0, 1)).any():
        raise ValueError("Invalid shot xG")
    for _, group in frame.groupby("period"):
        if (group.t.diff().dropna() < -0.001).any():
            raise ValueError(f"Non-monotonic timestamps in {mid}")
    # Continuous playback clock includes stoppage time, with no halftime gap.
    offset = 0.0
    frame["clock"] = 0.0
    for _, group in frame.groupby("period", sort=True):
        frame.loc[group.index, "clock"] = group.t + offset
        offset += group.t.max()
    return frame


def action_rows(events: pd.DataFrame) -> pd.DataFrame:
    loss = events.type.isin(["Miscontrol", "Dispossessed"]) | (events.type.eq("Dribble") & events.outcome.eq("Incomplete"))
    allowed = events.type.isin(["Pass", "Carry", "Shot"]) | loss
    valid = events.x.notna() & events.y.notna()
    result = events.loc[allowed & valid & ~events.penalty].copy()
    # Failed passes still enter the denominator even if the destination is unknown.
    missing = result.type.isin(MOVES) & result.complete & result.end_x.isna()
    if missing.any():
        raise ValueError("Completed move missing endpoint")
    return result


def possessions(events: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split provider chains on firm on-ball control changes, not defensive annotations."""
    events = events.copy()
    events["provider_owner_id"] = events.owner_id
    events["provider_owner"] = events.owner
    owner_id, owner_name, previous_key = None, None, None
    sequence = 0
    assignments, owners, owner_names, switches = [], [], [], []
    for row in events.itertuples():
        key = (row.period, row.possession)
        if key != previous_key:
            sequence += 1
            owner_id, owner_name = row.provider_owner_id, row.provider_owner
        switched = row.type in CONTROLLED and row.team_id != owner_id
        if switched:
            sequence += 1
            owner_id, owner_name = row.team_id, row.team
        assignments.append(sequence)
        owners.append(owner_id)
        owner_names.append(owner_name)
        switches.append(switched)
        previous_key = key
    events["sequence"] = assignments
    events["owner_id"] = owners
    events["owner"] = owner_names
    events["control_switch"] = switches
    rows = []
    events["active_seconds"] = 0.0
    events["sequence_key"] = events.match_id.astype(str) + ":" + events.sequence.astype(str)
    groups = list(events.groupby("sequence", sort=False))
    period_end = events.groupby("period").t.max().to_dict()
    for j, (_, group) in enumerate(groups):
        first = group.iloc[0]
        end = period_end[first.period]
        if j + 1 < len(groups) and groups[j+1][1].iloc[0].period == first.period:
            end = min(end, groups[j+1][1].iloc[0].t)
        own = group.loc[group.team_id.eq(group.owner_id) & group.type.isin(ON_BALL)]
        if own.empty or not own.type.isin(CONTROLLED).any():
            continue
        end = max(end, float(own.t.max()))
        covered = -math.inf
        for idx, event in own.iterrows():
            b = min(end, event.t + event.duration)
            active = max(0.0, b - max(event.t, covered))
            covered = max(covered, b)
            events.loc[idx, "active_seconds"] = active
        located = own.loc[own.x.notna()]
        if located.empty:
            start_x = end_x = peak = math.nan
        else:
            start_x = located.iloc[0].x
            last = located.iloc[-1]
            end_x = last.end_x if last.type in MOVES and last.complete else last.x
            peak = max(located.x.max(), located.loc[located.complete, "end_x"].max())
        passes = own.loc[own.type.eq("Pass")]
        shots = own.loc[own.type.eq("Shot")]
        state = own.iloc[0].score_state
        rows.append({"sequence_key": first.sequence_key, "match_id": first.match_id,
                     "possession": first.possession, "period": first.period,
                     "team_id": first.owner_id, "team": first.owner,
                     "start": own.t.min(), "clock": own.iloc[0].clock,
                     "elapsed_seconds": max(0.0, min(end, (own.t + own.duration).max()) - own.t.min()),
                     "active_seconds": events.loc[own.index, "active_seconds"].sum(),
                     "passes": len(passes), "completed_passes": int(passes.complete.sum()),
                     "final_third_passes": int((passes.complete & passes.x.ge(80)).sum()),
                     "start_x": start_x, "end_x": end_x, "peak_x": peak,
                     "progression": end_x - start_x, "shots": len(shots), "xg": shots.xg.sum(),
                     "goals": int(shots.goal.sum()), "score_state": state,
                     "home_score_before": own.iloc[0].home_score_before,
                     "away_score_before": own.iloc[0].away_score_before,
                     "provider_owner": first.provider_owner,
                     "control_switch": bool(group.control_switch.any()),
                     "play_pattern": own.iloc[0].play_pattern})
    return pd.DataFrame(rows), events
