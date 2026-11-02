"""A deliberately simple 2D stress-test generator, not a simulator of the competition match."""
from dataclasses import dataclass

import numpy as np

from .schema import TrackingBatch


@dataclass(frozen=True)
class SyntheticConfig:
    fps: int = 25
    pitch: tuple = (105.0, 68.0)
    noise_m: float = 0.12
    occlusion_rate: float = 0.05
    gap_seconds: float = 0.0
    player_gap_rate: float = 0.01
    identity_switches: bool = False
    contested: bool = False
    stoppages: bool = True
    transition_blind_seconds: float = 0.0
    stationary_live: bool = False
    invisible_stoppages: bool = False

    def __post_init__(self):
        if self.fps != 25:
            raise ValueError("synthetic benchmark uses 25 fps to match official metric durations")
        for p in (self.occlusion_rate, self.player_gap_rate):
            if not np.isfinite(p) or not 0 <= p <= 1:
                raise ValueError("missingness rates must be probabilities")
        for p in (self.noise_m, self.gap_seconds, self.transition_blind_seconds):
            if not np.isfinite(p) or p < 0:
                raise ValueError("noise and gap lengths must be finite and nonnegative")


@dataclass(frozen=True)
class SyntheticMatch:
    tracking: TrackingBatch
    truth: np.ndarray
    diagnostics: dict


def generate(config=SyntheticConfig(), seed=101):
    rng = np.random.default_rng(seed)
    fps = config.fps
    schedule = [(0, "X", 2), (1, "H", 12), (1, "A", 10), (1, "D", 5),
                (1, "H", 14), (1, "A", 9), (1, "D", 6), (1, "A", 12),
                (0, "X", 3), (2, "D", 4), (2, "A", 13), (2, "H", 15),
                (2, "D", 4), (2, "H", 10), (0, "X", 2)]
    if not config.stoppages:
        schedule = [(p, "H" if s == "D" else s, d) for p, s, d in schedule]
    truth = np.concatenate([np.full(d * fps, s) for _, s, d in schedule])
    period = np.concatenate([np.full(d * fps, p) for p, _, d in schedule])
    n = len(truth)
    t = np.arange(n) / fps
    phase = rng.uniform(0, 2 * np.pi)
    ball = np.c_[52 + 14 * np.sin(t / 7 + phase), 34 + 12 * np.sin(t / 9 + phase)]
    base_h = np.c_[np.linspace(8, 90, 11), rng.uniform(5, 63, 11)]
    base_a = np.c_[np.linspace(15, 98, 11), rng.uniform(5, 63, 11)]
    motion = np.c_[2 * np.sin(t * 1.3), np.cos(t * 1.1)]
    home = base_h[None] + motion[:, None]
    away = base_a[None] - motion[:, None]
    contest = np.zeros(n, bool)
    gap = np.zeros(n, bool)
    blind = np.zeros(n, bool)
    start = 0
    for p, state, seconds in schedule:
        stop = start + seconds * fps
        if state in ("D", "X"):
            ball[start:stop] = ball[start]
            home[start:stop] = home[start]
            away[start:stop] = away[start]
        else:
            if config.stationary_live:
                ball[start:stop] = ball[start]
                home[start:stop] = home[start]
                away[start:stop] = away[start]
            owning, opposing = (home, away) if state == "H" else (away, home)
            # Keep formations away from the ball; one carrier is then placed nearby.
            for team in (owning, opposing):
                delta = team[start:stop] - ball[start:stop, None]
                near = np.linalg.norm(delta, axis=2) < 6
                team[start:stop, :, 1] += near * 9
            owning[start:stop, 0] = ball[start:stop] + [0.5, 0.2]
            if config.contested:
                local = np.arange(stop - start)
                mask = (local % (fps * 3) < 5) & (local > fps)
                ids = np.flatnonzero(mask) + start
                opposing[ids, 0] = ball[ids] + [0.15, 0.1]
                contest[ids] = True
            gstart = start + (stop - start) // 3
            gap[gstart:min(stop, gstart + round(config.gap_seconds * fps))] = True
            blind[max(0, start - fps // 2):min(stop, start + round(config.transition_blind_seconds * fps))] = (
                config.transition_blind_seconds > 0)
        start = stop
    if config.identity_switches:
        for team in (home, away):
            for start in range(fps * 2, n, fps * 3):
                team[start:] = team[start:, rng.permutation(11)]
    # Noise is observation error, not extra latent player motion.
    home += rng.normal(0, config.noise_m, home.shape)
    away += rng.normal(0, config.noise_m, away.shape)
    ball += rng.normal(0, config.noise_m, ball.shape)
    missing = (rng.random(n) < config.occlusion_rate) | gap | blind
    if config.invisible_stoppages:
        missing |= truth == "D"
    ball[missing] = np.nan
    home[rng.random(home.shape[:2]) < config.player_gap_rate] = np.nan
    away[rng.random(away.shape[:2]) < config.player_gap_rate] = np.nan
    home[period == 0] = np.nan
    away[period == 0] = np.nan
    ball[period == 0] = np.nan
    tracking = TrackingBatch(np.arange(n), t, period, ball, home, away,
                             tuple(config.pitch), fps, {"kind": "synthetic", "seed": seed})
    return SyntheticMatch(tracking, truth, {"occluded": missing, "burst_gap": gap,
                                           "contested": contest, "transition_blind": blind})
