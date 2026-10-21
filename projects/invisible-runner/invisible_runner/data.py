"""Pinned public downloads, strict parsing, period-aware timing and cleaning."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd
from scipy.signal import savgol_filter

REVISION = "4340d274572876239c154c90bc507a9b3250a656"
RAW = f"https://raw.githubusercontent.com/SkillCorner/opendata/{REVISION}"
MEDIA = f"https://media.githubusercontent.com/media/SkillCorner/opendata/{REVISION}"
DEFAULT_MATCH = 1886347
FPS = 10


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, destination: Path, max_lines: int | None = None) -> dict:
    """Atomically cache a full file or bounded prefix; verify hashes on cache hits."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    receipt = destination.with_suffix(destination.suffix + ".source.json")
    if destination.exists() and receipt.exists():
        prior = json.loads(receipt.read_text())
        if (prior["url"] == url and prior["max_lines"] == max_lines
                and prior["sha256"] == sha256(destination)):
            return prior
    temporary = destination.with_name(destination.name + f".{os.getpid()}.part")
    lines = 0
    complete = True
    try:
        with urlopen(Request(url, headers={"User-Agent": "invisible-runner/0.1"}), timeout=120) as response:
            with temporary.open("wb") as target:
                if max_lines is not None:
                    if max_lines < 1:
                        raise ValueError("max_lines must be positive")
                    for line in response:
                        target.write(line)
                        lines += 1
                        if lines >= max_lines:
                            complete = False  # A prefix is never silently labelled a full match.
                            break
                else:
                    while chunk := response.read(1024 * 1024):
                        target.write(chunk)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)
    result = dict(url=url, revision=REVISION, max_lines=max_lines,
                  complete=complete, sha256=sha256(destination), bytes=destination.stat().st_size)
    receipt.write_text(json.dumps(result, indent=2) + "\n")
    return result


def fetch_match(cache: Path, match_id: int = DEFAULT_MATCH, seconds: int | None = 300) -> dict:
    """seconds=None downloads a full match; prefixes stop the network stream early."""
    if seconds is not None and seconds <= 0:
        raise ValueError("seconds must be positive")
    cache = cache / REVISION / str(int(match_id))
    prefix = f"data/matches/{int(match_id)}/{int(match_id)}"
    receipts, paths = {}, {}
    for key, suffix in [("metadata", "match.json"), ("events", "dynamic_events.csv"),
                        ("phases", "phases_of_play.csv"), ("tracking", "tracking_extrapolated.jsonl")]:
        limit = seconds * FPS if key == "tracking" and seconds is not None else None
        filename = f"{match_id}_{suffix}"
        if limit:
            filename = f"{match_id}_tracking_first_{seconds}s.jsonl"
        path = cache / filename
        receipts[key] = download(f"{MEDIA if key == 'tracking' else RAW}/{prefix}_{suffix}", path, limit)
        paths[key] = str(path.resolve())
    return dict(match_id=match_id, revision=REVISION, paths=paths, sources=receipts,
                scope="full match" if seconds is None else f"first {seconds}s of source frames")


def attack_sign(metadata: dict, team_id: int, period: int) -> int:
    side = metadata["home_team_side"][int(period) - 1]
    if side not in {"left_to_right", "right_to_left"}:
        raise ValueError(f"Unknown direction: {side}")
    sign = 1 if side == "left_to_right" else -1
    if team_id not in {metadata["home_team"]["id"], metadata["away_team"]["id"]}:
        raise ValueError("Team is not in this match")
    return sign if team_id == metadata["home_team"]["id"] else -sign


def clock_seconds(frame: int, period: int, metadata: dict) -> float:
    start = next(p["start_frame"] for p in metadata["match_periods"] if p["period"] == period)
    return (period - 1) * 45 * 60 + (frame - start) / FPS


def parse_tracking(path: Path, metadata: dict) -> tuple[pd.DataFrame, dict]:
    players = {int(p["id"]): p for p in metadata["players"]}
    rows = []
    audit = dict(source_frames=0, null_period_frames=0, invalid_positions=0,
                 unknown_players=0, player_rows=0, extrapolated_rows=0)
    previous_frame = -1
    with path.open() as f:
        for line_number, line in enumerate(f, 1):
            try:
                record = json.loads(line)
                frame = int(record["frame"])
            except (ValueError, KeyError, TypeError) as exc:
                raise ValueError(f"Malformed tracking line {line_number}") from exc
            if frame <= previous_frame:
                raise ValueError(f"Non-increasing or duplicate frame at line {line_number}")
            previous_frame = frame
            audit["source_frames"] += 1
            period = record["period"]
            if period is None:
                audit["null_period_frames"] += 1
                continue
            if period not in (1, 2):
                raise ValueError(f"Unsupported period {period}")
            possession = record.get("possession") or {}
            group = possession.get("group")
            possession_team = {"home team": metadata["home_team"]["id"],
                               "away team": metadata["away_team"]["id"]}.get(group)
            ball = record.get("ball_data") or {}
            seen = set()
            for player in record["player_data"]:
                pid = int(player["player_id"])
                if pid in seen:
                    raise ValueError(f"Duplicate player {pid} at frame {frame}")
                seen.add(pid)
                if pid not in players:
                    audit["unknown_players"] += 1
                    continue
                x, y = player.get("x"), player.get("y")
                if (x is None or y is None or not np.isfinite([x, y]).all()
                        or abs(x) > metadata["pitch_length"] / 2 + 5
                        or abs(y) > metadata["pitch_width"] / 2 + 5):
                    audit["invalid_positions"] += 1
                    continue
                p = players[pid]
                detected = player.get("is_detected") is True
                rows.append((frame, period, pid, p["team_id"], p["short_name"],
                             p["player_role"]["acronym"] == "GK", float(x), float(y), detected,
                             possession.get("player_id"), possession_team,
                             ball.get("x"), ball.get("y"), ball.get("is_detected") is True))
                audit["extrapolated_rows"] += not detected
    columns = ["frame", "period", "player_id", "team_id", "player_name", "is_gk", "x", "y",
               "detected", "carrier_id", "possession_team", "ball_x", "ball_y", "ball_detected"]
    df = pd.DataFrame(rows, columns=columns)
    if df.empty:
        raise ValueError("No valid player positions in tracking input")
    audit["player_rows"] = len(df)
    return df, audit


def validate_intervals(df: pd.DataFrame, match_id: int) -> None:
    required = {"match_id", "frame_start", "frame_end", "period"}
    if not required <= set(df):
        raise ValueError(f"Missing interval columns: {required - set(df)}")
    if not df.match_id.eq(match_id).all() or not df.period.isin([1, 2]).all():
        raise ValueError("Wrong match or unsupported period in interval data")
    if df[["frame_start", "frame_end"]].isna().any().any() or (df.frame_end < df.frame_start).any():
        raise ValueError("Invalid event/phase interval")


def annotate_context(df: pd.DataFrame, phases: pd.DataFrame, events: pd.DataFrame,
                     metadata: dict) -> pd.DataFrame:
    """Join phases by frame/period; never use derived run or outcome labels."""
    for intervals in [phases, events]:
        validate_intervals(intervals, metadata["id"])
    result = df.copy()
    result["phase_team"] = np.nan
    for period, group in phases.groupby("period"):
        group = group.sort_values("frame_start")
        if (group.frame_start.to_numpy()[1:] < group.frame_end.to_numpy()[:-1]).any():
            raise ValueError("Overlapping phases within a period")
        starts, ends = group.frame_start.to_numpy(), group.frame_end.to_numpy()
        indices = result.index[result.period.eq(period)]
        frames = result.loc[indices, "frame"].to_numpy()
        locs = np.searchsorted(starts, frames, side="right") - 1
        valid = (locs >= 0) & (frames < ends[np.maximum(locs, 0)])
        result.loc[indices[valid], "phase_team"] = group.team_in_possession_id.to_numpy()[locs[valid]]
        for phase in group.itertuples():
            expected = 1 if phase.attacking_side == "left_to_right" else -1
            if phase.attacking_side not in {"left_to_right", "right_to_left"} or expected != attack_sign(metadata, phase.team_in_possession_id, period):
                raise ValueError("Phase and match directions disagree")
    result["provider_on_ball"] = False
    for event in events[events.event_type.eq("player_possession")].itertuples():
        # Inclusive endpoint excludes reception/last-touch frames conservatively.
        mask = (result.period.eq(event.period) & result.player_id.eq(event.player_id)
                & result.frame.between(event.frame_start, event.frame_end))
        result.loc[mask, "provider_on_ball"] = True
    return result


def smooth_tracking(df: pd.DataFrame, window: int = 7, max_speed: float = 12.5) -> pd.DataFrame:
    if window < 3 or window % 2 == 0:
        raise ValueError("Smoothing window must be odd and >=3")
    result = df.sort_values(["player_id", "period", "frame"]).copy()
    result["sx"], result["sy"] = np.nan, np.nan
    result["speed"], result["step_m"] = np.nan, np.nan
    result["segment"] = -1
    result["edge"] = True
    result["raw_jump"] = False
    next_segment = 0
    for _, group in result.groupby(["player_id", "period"], sort=False):
        frames = group.frame.to_numpy()
        xy = group[["x", "y"]].to_numpy()
        delta = np.diff(frames)
        velocity = np.linalg.norm(np.diff(xy, axis=0), axis=1) * FPS / delta
        jump = (delta == 1) & (velocity > max_speed)
        bad = np.r_[False, jump] | np.r_[jump, False]
        result.loc[group.index, "raw_jump"] = bad
        breaks = np.r_[True, delta != 1] | bad | np.r_[False, bad[:-1]]
        labels = np.cumsum(breaks)
        for label in np.unique(labels):
            positions = np.flatnonzero((labels == label) & ~bad)
            if not len(positions):
                continue
            ids = group.index[positions]
            coords = xy[positions]
            if len(coords) >= window:
                coords = savgol_filter(coords, window, 2, axis=0, mode="interp")
            result.loc[ids, ["sx", "sy"]] = coords
            result.loc[ids, "segment"] = next_segment
            next_segment += 1
            if len(coords) < 3:
                continue
            speeds = np.linalg.norm(np.gradient(coords, 1 / FPS, axis=0), axis=1)
            result.loc[ids, "speed"] = speeds
            result.loc[ids, "step_m"] = np.r_[np.nan, np.linalg.norm(np.diff(coords, axis=0), axis=1)]
            margin = window // 2
            if len(ids) > 2 * margin:
                result.loc[ids[margin:-margin], "edge"] = False
    return result.sort_values(["frame", "player_id"]).reset_index(drop=True)
