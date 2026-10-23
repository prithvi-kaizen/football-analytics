"""Parse observations and create pre-pass features without endpoint access."""

from __future__ import annotations

import math
from collections import Counter

import pandas as pd

from .geometry import origin_context, pass_geometry, period_seconds, point_visible, xy

EVENT_FEATURES = ["start_x", "start_y", "period"]
ORIGIN_360 = ["opponents_visible", "teammates_visible", "nearest_passer", "pressure_5", "opponents_5"]
TARGET_GEOMETRY = ["distance", "angle_sin", "angle_cos", "target_x", "target_y", "forward_gain"]
TARGET_360 = ["lane_clearance", "lane_defenders_3", "nearest_target", "lane_defenders_observed"]
KNOWN_FAILURES = {"Incomplete", "Out", "Pass Offside", "Injury Clearance"}


def eligible(event: dict) -> bool:
    p = event.get("pass", {})
    return (
        event.get("type", {}).get("name") == "Pass"
        and event.get("period") in (1, 2, 3, 4)
        and not p.get("type")
        and p.get("height", {}).get("name") == "Ground Pass"
        and p.get("body_part", {}).get("name") in ("Left Foot", "Right Foot")
    )


def outcome_label(event: dict) -> int | None:
    outcome = event["pass"].get("outcome")
    if outcome is None:
        return 1
    return 0 if outcome.get("name") in KNOWN_FAILURES else None


def frame_players(frame: dict, audit: Counter | None = None):
    teammates, opponents = [], []
    for i, p in enumerate(frame.get("freeze_frame", [])):
        try:
            loc = xy(p.get("location"), bounded=False)
            if not isinstance(p.get("teammate"), bool) or not isinstance(p.get("actor"), bool):
                raise ValueError("Missing team or actor flag")
        except (ValueError, TypeError):
            if audit is not None:
                audit["invalid_frame_players"] += 1
            continue
        on_pitch = 0 <= loc[0] <= 120 and 0 <= loc[1] <= 80
        if not on_pitch and audit is not None:
            audit["off_pitch_frame_players"] += 1
        if p["teammate"] and not p["actor"]:
            teammates.append(
                {
                    "candidate_id": f"T{i + 1:02d}",
                    "location": list(loc),
                    "keeper": bool(p.get("keeper", False)),
                    "on_pitch": on_pitch,
                    "inside_visible_area": point_visible(loc, frame.get("visible_area")),
                }
            )
        elif not p["teammate"] and not p["actor"]:
            opponents.append(list(loc))
    return teammates, opponents


def infer_target(
    event: dict,
    teammates: list[dict],
    history: dict,
    max_age: float = 5.0,
    max_distance: float = 3.0,
    min_margin: float = 2.0,
):
    """Match annotated recipient to past actor origin, never to pass end/receipt.

    Anonymous identity remains a proxy even when these conservative gates pass.
    """
    recipient = event.get("pass", {}).get("recipient", {}).get("id")
    if recipient is None or not teammates:
        return None
    key = (event["team"]["id"], event["period"], recipient)
    previous = history.get(key)
    if previous is None:
        return None
    age = period_seconds(event["timestamp"]) - previous["seconds"]
    if not 0 < age <= max_age:
        return None
    ranked = sorted((math.dist(previous["location"], p["location"]), p["candidate_id"], p) for p in teammates)
    if not ranked[0][2].get("on_pitch", True):
        return None
    if ranked[0][0] > max_distance or (len(ranked) > 1 and ranked[1][0] - ranked[0][0] < min_margin):
        return None
    return {**ranked[0][2], "history_age": age, "history_distance": ranked[0][0]}


def event_context(event: dict) -> dict:
    x, y = xy(event["location"])
    return {
        "start_x": x,
        "start_y": y,
        "period": event["period"],
        "under_pressure": int(event.get("under_pressure", False)),
    }


def extract_match(match: dict, events: list[dict], frames: list[dict]):
    audit = Counter(events=len(events), frames=len(frames), raw_passes=0)
    event_ids = [e["id"] for e in events]
    if len(event_ids) != len(set(event_ids)):
        raise ValueError("Duplicate event IDs")
    frame_ids = [f["event_uuid"] for f in frames]
    if len(frame_ids) != len(set(frame_ids)):
        raise ValueError("Duplicate frame event_uuid values")
    if len({e["index"] for e in events}) != len(events):
        raise ValueError("Duplicate event indices")
    by_frame = {f["event_uuid"]: f for f in frames}
    audit["orphan_frames"] = len(set(by_frame) - set(event_ids))
    history, rows, scenes = {}, [], {}
    for event in sorted(events, key=lambda e: e["index"]):
        audit["raw_passes"] += event.get("type", {}).get("name") == "Pass"
        if eligible(event):
            audit["eligible_passes"] += 1
            try:
                base = event_context(event)
                sec = period_seconds(event["timestamp"])
            except (ValueError, TypeError, KeyError):
                audit["invalid_pass_origin_or_time"] += 1
                continue
            label = outcome_label(event)
            if label is None:
                audit["unknown_outcome"] += 1
                continue
            row = {
                **match,
                **base,
                "event_id": event["id"],
                "event_index": event["index"],
                "possession": event["possession"],
                "seconds": sec,
                "minute": event["minute"],
                "second": event["second"],
                "player": event["player"]["name"],
                "team": event["team"]["name"],
                "complete": label,
                "has_frame": False,
                "has_target": False,
                "has_opponents": False,
            }
            frame = by_frame.get(event["id"])
            if frame:
                teammates, opponents = frame_players(frame, audit)
                # A frame with no defenders cannot establish an unopposed pass.
                row.update(origin_context((base["start_x"], base["start_y"]), opponents))
                row["teammates_visible"] = len(teammates)
                row["has_frame"] = True
                row["has_opponents"] = bool(opponents)
                audit["passes_with_frame"] += 1
                audit["frames_without_opponents"] += not opponents
                audit["frames_without_visible_area"] += not bool(frame.get("visible_area"))
                target = infer_target(event, teammates, history)
                if target and opponents:
                    row.update(pass_geometry(event["location"], target["location"], opponents))
                    row.update({k: target[k] for k in ("history_age", "history_distance")})
                    row["target_candidate_id"] = target["candidate_id"]
                    row["has_target"] = True
                    audit["target_proxy_passes"] += 1
                    audit["target_proxy_failures"] += not label
                # These fields are for scene display only. No model reads them.
                scenes[event["id"]] = {
                    "origin": event["location"],
                    "actual_end": event["pass"].get("end_location"),
                    "teammates": teammates,
                    "opponents": opponents,
                    "visible_area": frame.get("visible_area", []),
                    "target_candidate_id": row.get("target_candidate_id"),
                    "match_id": match["match_id"],
                }
            else:
                audit["passes_without_frame"] += 1
            rows.append(row)
        if "player" in event and "location" in event and event.get("period") in (1, 2, 3, 4):
            try:
                key = (event["team"]["id"], event["period"], event["player"]["id"])
                history[key] = {
                    "seconds": period_seconds(event["timestamp"]),
                    "location": xy(event["location"]),
                }
            except (KeyError, ValueError, TypeError):
                audit["invalid_history_event"] += 1
    audit["retained_passes"] = len(rows)
    return rows, scenes, dict(audit)


def extract_dataset(payloads: list[dict]):
    rows, scenes, audits = [], {}, []
    for payload in payloads:
        r, s, a = extract_match(payload["match"], payload["events"], payload["frames"])
        rows.extend(r)
        scenes.update(s)
        audits.append({**payload["match"], **a})
    df = pd.DataFrame(rows)
    if df.empty:
        raise ValueError("No eligible passes found")
    for name in ORIGIN_360 + TARGET_GEOMETRY + TARGET_360:
        if name not in df:
            df[name] = float("nan")
    return df, scenes, audits
