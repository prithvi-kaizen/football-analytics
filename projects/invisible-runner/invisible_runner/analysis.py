"""Transparent thresholds and geometric associations; no fitted model."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist

from .data import FPS, attack_sign, clock_seconds


@dataclass(frozen=True)
class RunConfig:
    speed_mps: float = 5.0
    min_duration_s: float = 1.0
    min_distance_m: float = 5.0
    min_progress_m: float = 3.0
    ball_buffer_m: float = 3.0
    smoothing_window: int = 7
    max_speed_mps: float = 12.5
    patch_radius_m: float = 6.0
    control_radius_m: float = 3.0
    grid_m: float = 1.0

    def __post_init__(self):
        if any(value <= 0 for value in asdict(self).values()):
            raise ValueError("All thresholds must be positive")
        if self.speed_mps >= self.max_speed_mps:
            raise ValueError("Run speed must be below maximum plausible speed")
        if self.smoothing_window < 3 or self.smoothing_window % 2 == 0:
            raise ValueError("Smoothing window must be odd and >=3")


def nearest_distance(point: np.ndarray, opponents: np.ndarray) -> float:
    return float(np.linalg.norm(opponents - point, axis=1).min()) if len(opponents) else np.nan


def defensive_line(opponents: pd.DataFrame, sign: int) -> float:
    """Second deepest *outfield* opponent in the attacker's coordinate frame."""
    x = opponents.loc[~opponents.is_gk, "sx"].to_numpy() * sign
    return float(np.sort(x)[-2]) if len(x) >= 7 else np.nan


def receiving_patch(center: np.ndarray, length: float, width: float,
                    config: RunConfig) -> np.ndarray:
    # Cell centres approximate area, with the *same* start-anchored cells at both times.
    offsets = np.arange(-config.patch_radius_m + config.grid_m / 2,
                        config.patch_radius_m, config.grid_m)
    xx, yy = np.meshgrid(offsets, offsets)
    offsets_xy = np.c_[xx.ravel(), yy.ravel()]
    points = center + offsets_xy
    mask = ((np.linalg.norm(offsets_xy, axis=1) <= config.patch_radius_m)
            & (np.abs(points[:, 0]) <= length / 2) & (np.abs(points[:, 1]) <= width / 2))
    return points[mask]


def free_area(points: np.ndarray, opponents: np.ndarray, config: RunConfig) -> float:
    if not len(points) or not len(opponents):
        return np.nan
    return float((cdist(points, opponents).min(axis=1) >= config.control_radius_m).sum()
                 * config.grid_m ** 2)


def choose_teammate(start: pd.DataFrame, runner: pd.Series, sign: int) -> int | None:
    """Preselect using start-state only to avoid choosing the largest later gain."""
    teammates = start[(start.team_id == runner.team_id) & ~start.is_gk
                      & (start.player_id != runner.player_id)
                      & (start.sx * sign >= runner.sx * sign - 10)]
    if teammates.empty:
        return None
    distances = (teammates.sx - runner.sx) ** 2 + (teammates.sy - runner.sy) ** 2
    return int(teammates.loc[distances.idxmin(), "player_id"])


def expected_opponents(metadata: dict, team_id: int, period: int, frame: int) -> set[int] | None:
    """Use published playing intervals, including substitutions, to audit completeness."""
    known = False
    expected = set()
    for player in metadata["players"]:
        if player["team_id"] == team_id:
            continue
        intervals = (player.get("playing_time") or {}).get("by_period")
        if intervals is None:
            continue
        known = True
        for interval in intervals:
            if (interval["name"] == f"period_{period}"
                    and interval["start_frame"] <= frame <= interval["end_frame"]):
                expected.add(int(player["id"]))
    return expected if known else None


RUN_COLUMNS = ["run_id", "match_id", "player_id", "player_name", "team_id", "period",
               "start_frame", "end_frame", "start_clock_s", "duration_s", "distance_m",
               "progress_m", "peak_speed_mps", "start_x", "start_y", "end_x", "end_y",
               "runner_detected_fraction", "known_carrier_fraction", "behind_line", "wide_channel",
               "toward_space", "runner_separation_delta_m", "nearby_defender_count",
               "defender_displacement_m", "defender_toward_endpoint_m", "teammate_id", "teammate_name",
               "teammate_clearance_delta_m", "free_area_start_m2", "free_area_end_m2", "free_area_delta_m2",
               "context_endpoint_detected_fraction", "ball_endpoint_detected", "context_valid"]


def measure_run(run: pd.DataFrame, snapshots: dict, metadata: dict, config: RunConfig) -> dict:
    first, last = run.iloc[0], run.iloc[-1]
    sign = attack_sign(metadata, int(first.team_id), int(first.period))
    start = snapshots[int(first.frame)]
    end = snapshots[int(last.frame)]
    start = start.dropna(subset=["sx", "sy"])
    end = end.dropna(subset=["sx", "sy"])
    opp0 = start[start.team_id.ne(first.team_id)].sort_values("player_id")
    opp1 = end[end.team_id.ne(first.team_id)].sort_values("player_id")
    same_opponents = (len(opp0) >= 8 and opp0.player_id.tolist() == opp1.player_id.tolist()
                      and opp0.segment.tolist() == opp1.segment.tolist())
    for frame, opponents in [(int(first.frame), opp0), (int(last.frame), opp1)]:
        expected = expected_opponents(metadata, int(first.team_id), int(first.period), frame)
        if expected is not None and set(opponents.player_id) != expected:
            same_opponents = False
    xy0, xy1 = opp0[["sx", "sy"]].to_numpy(), opp1[["sx", "sy"]].to_numpy()
    runner0 = np.array([first.sx, first.sy])
    runner1 = np.array([last.sx, last.sy])
    result = {key: np.nan for key in RUN_COLUMNS}
    result.update(run_id=f"{metadata['id']}-{int(first.player_id)}-{int(first.frame)}",
                  match_id=metadata["id"], player_id=int(first.player_id), player_name=first.player_name,
                  team_id=int(first.team_id), period=int(first.period), start_frame=int(first.frame),
                  end_frame=int(last.frame), start_clock_s=clock_seconds(int(first.frame), int(first.period), metadata),
                  duration_s=(last.frame - first.frame) / FPS,
                  distance_m=float(np.linalg.norm(np.diff(run[["sx", "sy"]].to_numpy(), axis=0), axis=1).sum()),
                  progress_m=float((last.sx - first.sx) * sign), peak_speed_mps=float(run.speed.max()),
                  start_x=first.sx, start_y=first.sy, end_x=last.sx, end_y=last.sy,
                  runner_detected_fraction=float(run.detected.mean()),
                  known_carrier_fraction=float(run.carrier_id.notna().mean()),
                  wide_channel=bool(abs(last.sy) >= metadata["pitch_width"] * .3
                                                       and abs(last.sy) - abs(first.sy) >= 2),
                  context_valid=bool(same_opponents),
                  ball_endpoint_detected=bool(first.ball_detected and last.ball_detected))
    if not same_opponents:
        return result
    line0, line1 = defensive_line(opp0, sign), defensive_line(opp1, sign)
    result["behind_line"] = bool(first.sx * sign <= line0 - .5 and last.sx * sign > line1 + .5)
    separation0, separation1 = nearest_distance(runner0, xy0), nearest_distance(runner1, xy1)
    result["runner_separation_delta_m"] = separation1 - separation0
    result["toward_space"] = bool(separation1 - separation0 >= 2)
    nearby = np.linalg.norm(xy0 - runner0, axis=1) <= 10
    result["nearby_defender_count"] = int(nearby.sum())
    if nearby.any():
        movement = xy1[nearby] - xy0[nearby]
        vectors = runner1 - xy0[nearby]
        unit = vectors / np.maximum(np.linalg.norm(vectors, axis=1)[:, None], 1e-9)
        result["defender_displacement_m"] = float(np.linalg.norm(movement, axis=1).mean())
        result["defender_toward_endpoint_m"] = float((movement * unit).sum(axis=1).mean())
    teammate_id = choose_teammate(start, first, sign)
    if teammate_id is None or teammate_id not in end.player_id.values:
        return result
    teammate0 = start[start.player_id.eq(teammate_id)].iloc[0]
    teammate1 = end[end.player_id.eq(teammate_id)].iloc[0]
    if teammate0.segment != teammate1.segment:
        return result
    points = receiving_patch(teammate0[["sx", "sy"]].to_numpy(dtype=float),
                             metadata["pitch_length"], metadata["pitch_width"], config)
    area0, area1 = free_area(points, xy0, config), free_area(points, xy1, config)
    result.update(teammate_id=teammate_id, teammate_name=teammate0.player_name,
                  teammate_clearance_delta_m=nearest_distance(teammate1[["sx", "sy"]].to_numpy(dtype=float), xy1)
                  - nearest_distance(teammate0[["sx", "sy"]].to_numpy(dtype=float), xy0),
                  free_area_start_m2=area0, free_area_end_m2=area1, free_area_delta_m2=area1 - area0,
                  context_endpoint_detected_fraction=float(np.mean(
                      list(opp0.detected) + list(opp1.detected) + [teammate0.detected, teammate1.detected])))
    return result


def detect_runs(tracking: pd.DataFrame, metadata: dict, config: RunConfig) -> pd.DataFrame:
    """Contiguous high-speed movement in possession, clear of the tracked ball."""
    snapshots = {int(frame): group for frame, group in tracking.groupby("frame", sort=False)}
    results = []
    for _, player in tracking.groupby(["player_id", "period", "segment"], sort=False):
        player = player.sort_values("frame")
        if player.iloc[0].segment < 0 or player.iloc[0].is_gk:
            continue
        ball_distance = np.hypot(player.sx - player.ball_x, player.sy - player.ball_y)
        eligible = (player.speed.ge(config.speed_mps) & player.speed.le(config.max_speed_mps)
                    & ~player.edge & player.phase_team.eq(player.team_id)
                    & (player.possession_team.isna() | player.possession_team.eq(player.team_id))
                    & ~player.carrier_id.eq(player.player_id) & ~player.provider_on_ball
                    & ball_distance.ge(config.ball_buffer_m)
                    & player.sx.abs().le(metadata["pitch_length"] / 2)
                    & player.sy.abs().le(metadata["pitch_width"] / 2))
        labels = eligible.ne(eligible.shift(fill_value=False)).cumsum()
        for _, run in player[eligible].groupby(labels[eligible]):
            a, b = player.index.get_loc(run.index[0]), player.index.get_loc(run.index[-1])
            # Reject a speed interval cut by source/gap/smoothing boundaries.
            if a == 0 or b == len(player) - 1 or player.iloc[a - 1].edge or player.iloc[b + 1].edge:
                continue
            duration = (run.frame.iloc[-1] - run.frame.iloc[0]) / FPS
            coords = run[["sx", "sy"]].to_numpy()
            distance = float(np.linalg.norm(np.diff(coords, axis=0), axis=1).sum())
            sign = attack_sign(metadata, int(run.team_id.iloc[0]), int(run.period.iloc[0]))
            progress = (coords[-1, 0] - coords[0, 0]) * sign
            if (duration < config.min_duration_s or distance < config.min_distance_m
                    or progress < config.min_progress_m):
                continue
            results.append(measure_run(run, snapshots, metadata, config))
    return pd.DataFrame(results, columns=RUN_COLUMNS)


def compare_provider(runs: pd.DataFrame, events: pd.DataFrame, tracking: pd.DataFrame) -> dict:
    """Descriptive temporal overlap, not accuracy against independent truth."""
    provider = events[events.event_type.eq("off_ball_run")].copy()
    lo, hi = int(tracking.frame.min()), int(tracking.frame.max())
    provider = provider[(provider.frame_start >= lo) & (provider.frame_end <= hi)]
    overlaps, provider_matches = 0, set()
    for run in runs.itertuples():
        candidates = provider[(provider.player_id == run.player_id) & (provider.period == run.period)]
        matched = False
        for event in candidates.itertuples():
            overlap = max(0, min(run.end_frame, event.frame_end) - max(run.start_frame, event.frame_start))
            union = max(run.end_frame, event.frame_end) - min(run.start_frame, event.frame_start)
            if union > 0 and overlap / union >= .3:
                matched = True
                provider_matches.add(event.event_id)
        overlaps += matched
    return dict(provider_runs_fully_in_scope=len(provider), baseline_runs=len(runs),
                baseline_runs_overlapping_provider=overlaps, provider_runs_overlapping_baseline=len(provider_matches),
                rule="same player and period, temporal intersection/union >=0.3; different definitions, not ground truth")
