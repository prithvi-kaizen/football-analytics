"""Two synthetic action processes. Private referee rulings are never annotation inputs."""
from dataclasses import dataclass

import numpy as np

from .schema import TrackingBatch, blocks
from .synthetic_trials import ambiguous_pair


@dataclass(frozen=True)
class ActionCue:
    frame: int
    kind: str
    team: str | None
    period: int


@dataclass(frozen=True)
class PrivateAction:
    cue: ActionCue
    allowed: bool


@dataclass(frozen=True)
class EventWorld:
    tracking: TrackingBatch
    truth: np.ndarray
    actions: tuple[PrivateAction, ...]
    target: np.ndarray
    family: str

    def visible_cues(self):
        return tuple(action.cue for action in self.actions)


def rule_labels(period, actions, initial_team="H"):
    """A referee ruling gates signals/restarts; an attempt alone never guarantees a transition."""
    truth = np.full(len(period), "X")
    indexed = {}
    for action in actions:
        indexed.setdefault(action.cue.frame, []).append(action)
    for a, b in blocks(period):
        state = initial_team
        for i in range(a, b):
            for action in indexed.get(i, []):
                cue = action.cue
                if not action.allowed:
                    continue
                if cue.kind == "stop_gesture":
                    state = "D"
                elif cue.kind == "restart_attempt" and state == "D" and cue.team in ("H", "A"):
                    state = cue.team
                elif cue.kind == "controlled_touch" and state != "D" and cue.team in ("H", "A"):
                    state = cue.team
            truth[i] = state
    return truth


def _episode_actions(period, rng):
    actions = []
    for a, b in blocks(period):
        cursor = a + int(rng.integers(80, 160))
        while cursor + 80 < b:
            actions.append(PrivateAction(ActionCue(cursor, "stop_gesture", None, int(period[a])), rng.random() < 0.85))
            restart = min(b - 1, cursor + int(rng.integers(70, 190)))
            # A cancelled attempt and a later permitted attempt have the same public cue type.
            if restart - cursor > 100:
                actions.append(PrivateAction(ActionCue(cursor + 45, "restart_attempt", str(rng.choice(["H", "A"])), int(period[a])), False))
            actions.append(PrivateAction(ActionCue(restart, "restart_attempt", str(rng.choice(["H", "A"])), int(period[a])), True))
            cursor = restart + int(rng.integers(100, 260))
        for i in range(a + 35, b, 55):
            kind = str(rng.choice(["pass", "controlled_touch", "advisory_gesture"]))
            actions.append(PrivateAction(ActionCue(i, kind, str(rng.choice(["H", "A"])), int(period[a])), True))
    return tuple(sorted(actions, key=lambda x: x.cue.frame))


def _renewal_actions(period, rng):
    actions = []
    for a, b in blocks(period):
        cursor = a + 25
        while cursor < b:
            cursor += max(8, round(rng.exponential(1.6) * 25))
            if cursor >= b:
                break
            kind = str(rng.choice(["pass", "controlled_touch", "stop_gesture", "advisory_gesture", "restart_attempt"],
                                  p=[0.2, 0.2, 0.18, 0.12, 0.3]))
            allowed = rng.random() < (0.7 if kind in ("stop_gesture", "restart_attempt") else 0.9)
            actions.append(PrivateAction(ActionCue(cursor, kind, str(rng.choice(["H", "A"])), int(period[a])), bool(allowed)))
    return tuple(actions)


def _tracking(truth, period, family, seed, occluded):
    rng = np.random.default_rng(seed)
    n, fps = len(truth), 25
    t = np.arange(n) / fps
    if family == "episodes":
        phi = rng.uniform(0, 6.28, 3)
        ball = np.c_[52 + 26 * np.sin(t * 0.18 + phi[0]), 34 + 17 * np.cos(t * 0.23 + phi[1])]
        motion = np.c_[np.sin(t * 1.3), np.cos(t * 1.2)]
    else:
        # Independent correlated-velocity process, bounded by reflection, not sinusoidal paths.
        velocity = np.zeros((n, 2))
        for i in range(1, n):
            velocity[i] = 0.96 * velocity[i - 1] + rng.normal(0, 0.45, 2)
        raw = np.cumsum(velocity / fps, axis=0) + [52, 34]
        bounds = np.array([85, 48])
        ball = 10 + bounds - np.abs(raw % (2 * bounds) - bounds)
        motion = np.cumsum(rng.normal(0, 0.04, (n, 2)), axis=0)
    home = rng.uniform([5, 5], [100, 63], (11, 2))[None] + motion[:, None]
    away = rng.uniform([5, 5], [100, 63], (11, 2))[None] - motion[:, None]
    edges = np.r_[0, np.flatnonzero(truth[1:] != truth[:-1]) + 1, n]
    for a, b in zip(edges[:-1], edges[1:]):
        if truth[a] == "D":
            ball[a:b] = ball[a]  # Off-ball players continue moving during a stoppage.
        elif truth[a] in ("H", "A"):
            if rng.random() < 0.3:
                ball[a:b] = ball[a]
            for team in (home, away):
                near = np.linalg.norm(team[a:b] - ball[a:b, None], axis=2) < 5
                team[a:b, :, 1] += 8 * near
            (home if truth[a] == "H" else away)[a:b, 0] = ball[a:b] + [0.4, 0.2]
    for value in (ball, home, away):
        value += rng.normal(0, 0.1, value.shape)
    missing = rng.random(n) < (0.35 if occluded else 0.1)
    if occluded:
        hidden = False
        for i in range(n):
            hidden = rng.random() > 0.025 if hidden else rng.random() < 0.018
            missing[i] |= hidden
    ball[missing | (period == 0)] = np.nan
    for team in (home, away):
        team[rng.random(team.shape[:2]) < 0.03] = np.nan
        team[period == 0] = np.nan
    return TrackingBatch(np.arange(n), t, period, ball, home, away, fps=fps,
                         provenance={"kind": "synthetic", "generator": "action_world_v1", "seed": seed, "family": family})


def generate_world(family, seed, occluded=False):
    if family not in ("episodes", "renewal"):
        raise ValueError("unknown world family")
    rng = np.random.default_rng(seed)
    lengths = rng.integers(1000, 1500, 2)
    period = np.r_[np.zeros(25, int), np.ones(lengths[0], int), np.zeros(75, int),
                   np.full(lengths[1], 2, int), np.zeros(25, int)]
    actions = (_episode_actions if family == "episodes" else _renewal_actions)(period, rng)
    truth = rule_labels(period, actions, str(rng.choice(["H", "A"])))
    return EventWorld(_tracking(truth, period, family, seed + 700000, occluded), truth,
                      actions, np.zeros(len(truth), bool), family)


def generate_twins(kind, seed):
    live, dead = ambiguous_pair(kind, seed)
    start, stop = np.flatnonzero(live.target)[[0, -1]]
    stop += 1
    live_actions = (PrivateAction(ActionCue(int(start), "advisory_gesture", "H", 1), False),
                    PrivateAction(ActionCue(int(stop), "pass", "H", 1), True))
    dead_actions = (PrivateAction(ActionCue(int(start), "stop_gesture", "H", 1), True),
                    PrivateAction(ActionCue(int(stop), "restart_attempt", "H", 1), True))
    return (EventWorld(live.tracking, live.truth, live_actions, live.target, f"twins_{kind}"),
            EventWorld(dead.tracking, dead.truth, dead_actions, dead.target, f"twins_{kind}"))
