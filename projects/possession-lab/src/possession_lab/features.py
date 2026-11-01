from dataclasses import dataclass

import numpy as np

from .schema import TrackingBatch, blocks


@dataclass(frozen=True)
class Features:
    nearest_home_m: np.ndarray
    nearest_away_m: np.ndarray
    nearest_team: np.ndarray
    ball_observed: np.ndarray
    home_observed: np.ndarray
    away_observed: np.ndarray
    ball_speed_mps: np.ndarray
    player_speed_mps: np.ndarray
    reliability: np.ndarray
    out_of_bounds: np.ndarray
    stationary_seconds: np.ndarray
    observation_age_s: np.ndarray
    period: np.ndarray
    fps: float


def _speed(xy, batch, lag_s=0.4):
    out = np.full(xy.shape[:-1], np.nan)
    lag = max(1, round(lag_s * batch.fps))
    for a, b in blocks(batch.period):
        if b - a <= lag:
            continue
        dt = batch.time_s[a + lag:b] - batch.time_s[a:b - lag]
        shape = (len(dt),) + (1,) * (out.ndim - 1)
        out[a + lag:b] = np.linalg.norm(xy[a + lag:b] - xy[a:b - lag], axis=-1) / dt.reshape(shape)
    return out


def extract(batch: TrackingBatch):
    visible = np.isfinite(batch.ball).all(axis=1)
    masks = [np.isfinite(team).all(axis=2) for team in (batch.home, batch.away)]
    distances = []
    for team, mask in zip((batch.home, batch.away), masks):
        delta = np.linalg.norm(team - batch.ball[:, None], axis=2)
        delta[~mask | ~visible[:, None]] = np.inf
        nearest = np.min(delta, axis=1)
        nearest[~np.isfinite(nearest)] = np.nan
        distances.append(nearest)
    dh, da = distances
    nearest = np.full(len(visible), "X")
    known = np.isfinite(dh) & np.isfinite(da)
    nearest[known & (dh < da)] = "H"
    nearest[known & (da < dh)] = "A"
    ball_speed = _speed(batch.ball, batch)
    speeds = np.concatenate([_speed(x, batch) for x in (batch.home, batch.away)], axis=1)
    # A track identity jump does not describe human motion. Collective median ignores a few jumps.
    speeds[speeds > 12] = np.nan
    player_speed = np.full(len(visible), np.nan)
    for i, row in enumerate(speeds):
        values = row[np.isfinite(row)]
        if len(values):
            player_speed[i] = np.median(values)
    coverage = np.minimum(masks[0].mean(axis=1), masks[1].mean(axis=1))
    reliability = visible * coverage * np.where(np.nan_to_num(ball_speed, nan=0) > 45, 0.1, 1)
    outside = visible & ((batch.ball[:, 0] < 0) | (batch.ball[:, 0] > batch.pitch[0])
                         | (batch.ball[:, 1] < 0) | (batch.ball[:, 1] > batch.pitch[1]))
    stationary = np.zeros(len(visible))
    age = np.zeros(len(visible))
    for a, b in blocks(batch.period):
        last = None
        duration = 0.0
        for i in range(a, b):
            last = batch.time_s[i] if visible[i] else last
            age[i] = batch.time_s[i] - last if last is not None else np.inf
            lo = max(a, i - round(batch.fps) + 1)
            bs = ball_speed[lo:i + 1]
            ps = player_speed[lo:i + 1]
            bs = bs[np.isfinite(bs)]
            ps = ps[np.isfinite(ps)]
            enough = min(len(bs), len(ps)) >= max(1, round(batch.fps / 2))
            still = enough and np.median(bs) < 0.8 and np.median(ps) < 0.8
            duration = duration + 1 / batch.fps if still else 0.0
            stationary[i] = duration
    return Features(dh, da, nearest, visible, masks[0], masks[1], ball_speed, player_speed,
                    reliability, outside, stationary, age, batch.period.copy(), batch.fps)
