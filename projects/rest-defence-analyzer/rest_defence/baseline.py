"""Observable turnover anchors and outcomes, independent of any score."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .data import FPS


def detect_turnovers(ball: pd.DataFrame, stable_seconds=.4) -> pd.DataFrame:
    """First new-control frame, requiring persistent possession on both sides.

    Persistence confirms the anchor; feature snapshots must precede it. Unknown
    possession, dead balls and gaps break runs rather than being forward-filled.
    """
    if stable_seconds <= 0:
        raise ValueError("Persistence must be positive")
    minimum = int(np.ceil(stable_seconds * FPS))
    rows = []
    for period, group in ball.groupby("period", sort=False):
        g = group.sort_values("frame").reset_index(drop=True)
        breaks = (g.possession.ne(g.possession.shift()) | g.live.ne(g.live.shift()) |
                  g.frame.diff().ne(1) | g.valid.ne(g.valid.shift()))
        runs = [v for _, v in g.groupby(breaks.cumsum())]
        for previous, current in zip(runs, runs[1:]):
            a, z = previous.iloc[-1], current.iloc[0]
            if (len(previous) >= minimum and len(current) >= minimum and a.live == z.live == 1
                    and a.valid and z.valid and a.possession in (1, 2) and z.possession in (1, 2)
                    and a.possession != z.possession and z.frame == a.frame + 1):
                rows.append(dict(period=period, frame=int(z.frame), time=float(z.time),
                                 losing=int(a.possession), winning=int(z.possession),
                                 prior_control_s=len(previous) / FPS))
    return pd.DataFrame(rows, columns=["period", "frame", "time", "losing", "winning", "prior_control_s"])


def preloss_snapshot(players: pd.DataFrame, ball: pd.DataFrame, period: str, frame: int,
                     max_age=.2) -> tuple[pd.DataFrame, pd.Series]:
    p = players[(players.period == period) & (players.frame < frame)]
    if p.empty:
        raise ValueError("No pre-loss snapshot")
    n = int(p.frame.max())
    if (frame - n) / FPS > max_age + 1e-8:
        raise ValueError("Pre-loss snapshot too old")
    p = p[p.frame == n].copy()
    b = ball[(ball.period == period) & (ball.frame == n)]
    if len(b) != 1 or not bool(b.iloc[0].valid) or b.iloc[0].live != 1:
        raise ValueError("Invalid pre-loss ball")
    if p.player.duplicated().any() or p.groupby("team").size().ne(11).any() or p.team.nunique() != 2:
        raise ValueError("Incomplete or non-11v11 snapshot")
    if p.groupby("team").is_gk.sum().ne(1).any():
        raise ValueError("Snapshot must have one identified goalkeeper per team")
    if not np.allclose(p.time, b.iloc[0].time, atol=.002):
        raise ValueError("Player/ball timestamp mismatch")
    return p, b.iloc[0]


def transition_outcome(ball: pd.DataFrame, events: pd.DataFrame, period: str, frame: int,
                       winning: int, winning_team: str, losing_sign: int, horizon=10., length=105.) -> dict:
    """Observe only the first uninterrupted new possession, at most ten seconds."""
    if horizon <= 0 or losing_sign not in (-1, 1):
        raise ValueError("Invalid outcome configuration")
    g = ball[(ball.period == period) & (ball.frame >= frame)].sort_values("frame")
    if g.empty or int(g.iloc[0].frame) != frame:
        raise ValueError("Outcome anchor absent")
    start = g.iloc[0]
    last = start
    reason = "source_end"
    censored = True
    for row in g.iloc[1:].itertuples():
        dt = row.time - start.time
        if row.frame != last.frame + 1:
            reason = "tracking_gap"
            break
        if dt > horizon + 1e-6:
            reason, censored = "horizon", False
            break
        if not row.valid:
            reason = "invalid_ball"
            break
        if row.live != 1:
            reason, censored = "dead_ball", False
            break
        if row.possession not in (1, 2):
            reason = "unknown_control"
            break
        if row.possession != winning:
            reason, censored = "regain", False
            break
        last = row
        if dt >= horizon - 1e-6:
            reason, censored = "horizon", False
            break
    observed = g[g.frame.between(frame, last.frame)]
    # A half ending within the excerpt is an observed termination, not truncation.
    final = events[(events.period == period) & (events.kind == "FinalWhistle")]
    if reason == "source_end" and not final.empty and abs(final.iloc[0].time - last.time) <= .2:
        reason, censored = "half_end", False
    shot = events[(events.period == period) & (events.kind == "ShotAtGoal") & (events.team == winning_team)]
    shot = shot[(shot.aligned_time >= start.time) & (shot.aligned_time <= last.time + 1e-6)]
    progress = float(np.max(-losing_sign * (observed.x.to_numpy() - start.x)))
    max_depth = float(np.max(-losing_sign * observed.x.to_numpy()))
    return dict(observed_seconds=float(last.time - start.time), stop_reason=reason, censored=censored,
                progress_m=progress, progressed_10m=progress >= 10., shot=not shot.empty,
                shot_xg=float(shot.xg.sum()), approx_shots=int((shot.alignment == "utc_approximate").sum()),
                entered_final_third=bool(max_depth >= length/6 and -losing_sign * start.x < length/6),
                end_frame=int(last.frame))


def align_events(events: pd.DataFrame, ball: pd.DataFrame) -> pd.DataFrame:
    result = events.copy()
    result["aligned_time"] = result.time
    result["alignment"] = "utc_approximate"
    for i, row in result[result.corrected_frame.notna()].iterrows():
        found = ball[(ball.period == row.period) & (ball.frame == int(row.corrected_frame))]
        if len(found) == 1:
            result.loc[i, "aligned_time"] = found.iloc[0].time
            result.loc[i, "alignment"] = "corrected_frame"
    return result
