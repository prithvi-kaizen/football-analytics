"""New trial families with random schedules and distinct observation mechanisms.

This is a stress generator, not a physical football simulator. Carrier assignments and resumes
can jump; missingness/camera processes are explicit idealizations. Truth never enters inference.
"""
from dataclasses import dataclass

import numpy as np

from .schema import TrackingBatch

SCENARIOS = ("iid", "bursty", "state_dependent", "camera_window", "moving_dead",
             "stationary_live", "invisible_stoppages", "identity_switches", "outliers", "short_spells",
             "twin_static_live", "twin_static_dead", "twin_invisible_live", "twin_invisible_dead")


@dataclass(frozen=True)
class Trial:
    tracking: TrackingBatch
    truth: np.ndarray
    target: np.ndarray
    description: dict


def _assemble(ball, home, away, period, seed, scenario):
    n = len(period)
    return TrackingBatch(np.arange(n), np.arange(n) / 25, period, ball, home, away,
                         (105.0, 68.0), 25, {"kind": "synthetic", "seed": seed,
                                               "generator": "independent_trials_v1", "scenario": scenario})


def ambiguous_pair(kind="static", seed=8001):
    """Bit-identical whole tracking sequences, opposing truth in an isolated interval."""
    if kind not in ("static", "invisible"):
        raise ValueError("unknown ambiguity family")
    rng = np.random.default_rng(seed)
    # Durations and spatial locations vary between independent pairs.
    before, middle, after = rng.integers([100, 100, 100], [180, 230, 180])
    n = int(before + middle + after)
    t = np.arange(n) / 25
    x, y = rng.uniform(35, 65), rng.uniform(20, 45)
    ball = np.tile([x, y], (n, 1))
    # Common moving context establishes a controller. The same motion after the target can
    # be a live pass in one world and a restart in the other; no whistle channel is observed.
    progress = np.where(np.arange(n) < before, (np.arange(n) - before) / 25,
                        np.where(np.arange(n) >= before + middle,
                                 (np.arange(n) - before - middle) / 25, 0.0))
    ball[:, 0] += 2.0 * progress
    home = np.tile(rng.uniform([5, 5], [100, 63], (11, 2)), (n, 1, 1))
    away = np.tile(rng.uniform([5, 5], [100, 63], (11, 2)), (n, 1, 1))
    home[:, 0] = ball + [0.4, 0.1]
    target = np.zeros(n, bool)
    target[before:before + middle] = True
    if kind == "invisible":
        motion = np.c_[0.7 * np.sin(t * 1.8), 0.9 * np.cos(t * 1.3)]
        home += motion[:, None]
        away -= motion[:, None]
        ball += motion
        ball[target] = np.nan
    # Same observation noise in both worlds, including all history and future.
    for value in (ball, home, away):
        value += rng.normal(0, 0.05, value.shape)
    batch = _assemble(ball, home, away, np.ones(n, int), seed, f"twin_{kind}")
    live = np.full(n, "H")
    dead = live.copy()
    dead[target] = "D"
    meta = {"family": kind, "ambiguity": "identical whole observations; target H versus D",
            "target_start": int(before), "target_stop": int(before + middle)}
    return Trial(batch, live, target, meta), Trial(batch, dead, target, meta)


def generate_trial(scenario, seed):
    if scenario not in SCENARIOS:
        raise ValueError(f"unknown trial scenario {scenario!r}")
    if scenario.startswith("twin_"):
        _, kind, state = scenario.split("_")
        return ambiguous_pair(kind, seed)[int(state == "dead")]
    # Independent random streams preserve common latent matches across observation mechanisms.
    latent_rng, obs_rng = [np.random.default_rng(s) for s in np.random.SeedSequence(seed).spawn(2)]
    schedule = [(0, "X", 25)]
    for half in (1, 2):
        if half == 2:
            schedule.append((half, "D", int(latent_rng.integers(40, 100))))
        team = str(latent_rng.choice(["H", "A"]))
        for j in range(int(latent_rng.integers(4, 7))):
            duration = latent_rng.integers(25, 100) if scenario == "short_spells" else latent_rng.integers(80, 300)
            schedule.append((half, team, int(duration)))
            if j % 2 == 1 or latent_rng.random() < 0.35:
                schedule.append((half, "D", int(latent_rng.integers(35, 160))))
            if latent_rng.random() < 0.8:
                team = "A" if team == "H" else "H"
        schedule.append((0, "X", 75 if half == 1 else 25))
    truth = np.concatenate([np.full(d, s) for _, s, d in schedule])
    period = np.concatenate([np.full(d, p, dtype=int) for p, _, d in schedule])
    n = len(truth)
    t = np.arange(n) / 25
    # Multi-frequency paths and spatial layouts vary across trials, unlike the old fixed schedule.
    phase = latent_rng.uniform(0, 2 * np.pi, 4)
    frequency = latent_rng.uniform(0.1, 0.4, 4)
    ball = np.c_[52 + 27 * np.sin(frequency[0] * t + phase[0]) + 6 * np.sin(frequency[1] * t),
                 34 + 18 * np.sin(frequency[2] * t + phase[2])]
    anchors = [latent_rng.uniform([5, 5], [100, 63], (11, 2)) for _ in range(2)]
    teams = []
    for anchor in anchors:
        walking = np.c_[1.0 * np.sin(1.4 * t + phase[1]), 1.1 * np.cos(1.2 * t + phase[3])]
        teams.append(anchor[None] + walking[:, None])
    home, away = teams
    target = np.zeros(n, bool)
    start = 0
    for p, state, duration in schedule:
        stop = start + duration
        if state == "D":
            ball[start:stop] = ball[start]
            if scenario != "moving_dead" and latent_rng.random() < 0.55:
                home[start:stop] = home[start]
                away[start:stop] = away[start]
            if scenario != "moving_dead" and latent_rng.random() < 0.5:
                ball[start:stop, 1] = -1.5 if latent_rng.random() < 0.5 else 69.5
        elif state in ("H", "A"):
            if scenario == "stationary_live":
                # A ball held still remains live: the referee decision is not in tracking.
                ball[start:stop] = ball[start]
                home[start:stop] = home[start]
                away[start:stop] = away[start]
                target[start:stop] = True
            for team in teams:
                near = np.linalg.norm(team[start:stop] - ball[start:stop, None], axis=2) < 5
                team[start:stop, :, 1] += near * 8
            owning, opposing = (home, away) if state == "H" else (away, home)
            owning[start:stop, 0] = ball[start:stop] + [0.4, 0.2]
            # Short duels: a touch does not change the known latent controller.
            ids = np.arange(start + 30, stop, 63)
            for i in ids:
                opposing[i:min(i + 4, stop), 0] = ball[i:min(i + 4, stop)] + [0.1, 0.1]
        start = stop
    for value in (ball, home, away):
        value += obs_rng.normal(0, 0.10, value.shape)
    missing = obs_rng.random(n) < 0.08
    if scenario == "bursty":
        hidden = False
        for i in range(n):
            hidden = obs_rng.random() >= 0.035 if hidden else obs_rng.random() < 0.02
            missing[i] = hidden
    elif scenario == "state_dependent":
        transition = np.r_[False, truth[1:] != truth[:-1]]
        near_boundary = np.convolve(transition.astype(int), np.ones(31, int), mode="same") > 0
        missing |= (obs_rng.random(n) < np.where(near_boundary, 0.7, 0.05))
    elif scenario == "camera_window":
        camera_x = 52 + 14 * np.sin(t * 0.16 + phase[0])
        missing |= (np.abs(ball[:, 0] - camera_x) > 20) | (np.abs(ball[:, 1] - 34) > 20)
        for team in teams:
            off_camera = np.abs(team[:, :, 0] - camera_x[:, None]) > 23
            team[off_camera] = np.nan
    elif scenario == "invisible_stoppages":
        missing |= truth == "D"
    elif scenario == "identity_switches":
        for team in teams:
            for i in range(50, n, 71):
                team[i:] = team[i:, obs_rng.permutation(11)]
    elif scenario == "outliers":
        ids = obs_rng.choice(n, max(1, n // 80), replace=False)
        ball[ids] += obs_rng.normal(0, 30, (len(ids), 2))
    ball[missing | (period == 0)] = np.nan
    for team in teams:
        team[obs_rng.random(team.shape[:2]) < 0.025] = np.nan
        team[period == 0] = np.nan
    batch = _assemble(ball, home, away, period, seed, scenario)
    return Trial(batch, truth, target, {"schedule": schedule, "mechanism": scenario,
                                       "scope": "independent synthetic stress trial; no real-match labels"})
