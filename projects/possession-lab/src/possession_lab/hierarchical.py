"""Fixed, uncalibrated probabilistic evidence with joint live/dead and owner decoding.

States LH/LA/DH/DA retain an unobserved owner memory while dead; both D states output D.
No claim of dead-ball ownership is made. The owner process is a continuity prior, not evidence.
"""
from dataclasses import dataclass

import numpy as np

from .features import Features
from .schema import blocks


@dataclass(frozen=True)
class HierarchicalConfig:
    stationarity_weight: float = 0.35
    missing_masks: bool = True
    duration_priors: bool = True
    possession_continuity: bool = True
    live_mean_s: float = 18.0
    dead_mean_s: float = 6.0
    owner_mean_s: float = 12.0
    evidence_power: float = 0.2
    abstain_after_s: float = 3.0

    def __post_init__(self):
        if not np.isfinite(self.stationarity_weight) or self.stationarity_weight < 0:
            raise ValueError("stationarity weight must be finite and nonnegative")
        for value in (self.live_mean_s, self.dead_mean_s, self.owner_mean_s,
                      self.evidence_power, self.abstain_after_s):
            if not np.isfinite(value) or value <= 0:
                raise ValueError("durations and evidence power must be finite and positive")
        for flag in (self.missing_masks, self.duration_priors, self.possession_continuity):
            if not isinstance(flag, bool):
                raise ValueError("ablation switches must be booleans")


@dataclass(frozen=True)
class HierarchicalResult:
    labels: np.ndarray
    local_live_probability: np.ndarray
    local_home_given_live: np.ndarray
    posterior: np.ndarray
    live_probability: np.ndarray
    home_given_live: np.ndarray
    log_potential: np.ndarray


def _sigmoid(x):
    return 1 / (1 + np.exp(-np.clip(x, -30, 30)))


def observation_heads(f: Features, cfg=HierarchicalConfig()):
    """Absent quantities contribute zero log evidence, rather than invented static observations."""
    both = np.isfinite(f.nearest_home_m) & np.isfinite(f.nearest_away_m)
    geometry = both & f.ball_observed
    ball_speed = np.nan_to_num(f.ball_speed_mps, nan=0.0)
    players = np.nan_to_num(f.player_speed_mps, nan=0.0)
    nearest = np.minimum(f.nearest_home_m, f.nearest_away_m)
    proximity = np.clip(1 - np.nan_to_num(nearest, nan=3.0) / 3, 0, 1)
    coverage = np.minimum(f.home_observed.mean(axis=1), f.away_observed.mean(axis=1))
    live_logit = 1.5 * np.clip(ball_speed / 3, 0, 1) * f.ball_observed
    live_logit += 0.4 * np.clip(players, 0, 1) * coverage
    live_logit += 0.8 * proximity * geometry * f.reliability
    still = (f.stationary_seconds >= 1.2) & f.ball_observed
    if not cfg.missing_masks:
        # Deliberately unsafe ablation: treat absent ball measurements as stationary samples.
        # The output abstention policy and every other input remain identical to the full model.
        still = still | ~f.ball_observed
    live_logit -= cfg.stationarity_weight * still
    live_logit -= 4.0 * f.out_of_bounds * f.reliability
    home_logit = np.zeros(len(f.period))
    home_logit[geometry] = np.clip((f.nearest_away_m[geometry] - f.nearest_home_m[geometry]) / 1.5,
                                   -4, 4) * f.reliability[geometry] * proximity[geometry]
    live, home = _sigmoid(live_logit), _sigmoid(home_logit)
    # Likelihood-ratio potentials relative to neutral hierarchical priors (L=.5, owner=.5).
    # This prevents an unknown team from doubling apparent evidence for D in a 3-state softmax.
    potential = np.c_[4 * live * home, 4 * live * (1 - home), 2 * (1 - live), 2 * (1 - live)]
    return live, home, np.log(np.clip(potential, 1e-12, None)) * cfg.evidence_power


def transition_matrix(fps, cfg=HierarchicalConfig()):
    if not np.isfinite(fps) or fps <= 0:
        raise ValueError("fps must be positive")
    dt = 1 / fps
    if cfg.duration_priors:
        a, b = 1 / cfg.live_mean_s, 1 / cfg.dead_mean_s
        change = 1 - np.exp(-(a + b) * dt)
        ld, dl = a / (a + b) * change, b / (a + b) * change
        live_dead = np.array([[1 - ld, ld], [dl, 1 - dl]])
    else:
        live_dead = np.full((2, 2), 0.5)
    stay = 0.5 + 0.5 * np.exp(-2 * dt / cfg.owner_mean_s) if cfg.possession_continuity else 0.5
    owner = np.array([[stay, 1 - stay], [1 - stay, stay]])
    return np.kron(live_dead, owner)


def decode_chain(log_potential, transition):
    """Joint MAP path plus scaled forward/backward marginals. No ground truth is accepted."""
    e = np.asarray(log_potential, float)
    t = np.asarray(transition, float)
    if (e.ndim != 2 or not len(e) or e.shape[1] != 4 or not np.isfinite(e).all()
            or t.shape != (4, 4) or not np.isfinite(t).all() or (t <= 0).any()
            or not np.allclose(t.sum(axis=1), 1)):
        raise ValueError("finite (n,4) potentials and positive stochastic (4,4) transitions required")
    log_t = np.log(t)
    score = e[0] - np.log(4)
    back = np.zeros((len(e), 4), np.int8)
    # Remove the row maximum so exponentiation and forward products stay bounded.
    weights = np.exp(e - e.max(axis=1, keepdims=True))
    forward = np.empty_like(e)
    forward[0] = weights[0] / weights[0].sum()
    for i in range(1, len(e)):
        options = score[:, None] + log_t
        back[i] = np.argmax(options, axis=0)
        score = options[back[i], np.arange(4)] + e[i]
        forward[i] = (forward[i - 1] @ t) * weights[i]
        forward[i] /= forward[i].sum()
    path = np.zeros(len(e), np.int8)
    path[-1] = np.argmax(score)
    backward = np.ones(4)
    posterior = np.empty_like(e)
    for i in range(len(e) - 1, -1, -1):
        posterior[i] = forward[i] * backward
        posterior[i] /= posterior[i].sum()
        if i:
            path[i - 1] = back[i, path[i]]
            backward = t @ (weights[i] * backward)
            backward /= backward.sum()
    return path, posterior


def hierarchical(f: Features, cfg=HierarchicalConfig()):
    live, home, log_potential = observation_heads(f, cfg)
    transition = transition_matrix(f.fps, cfg)
    labels = np.full(len(f.period), "X")
    posterior = np.full((len(f.period), 4), np.nan)
    alphabet = np.array(["H", "A", "D", "D"])
    reliable_ball = f.ball_observed & (f.reliability >= 0.45)
    for a, b in blocks(f.period):
        path, posterior[a:b] = decode_chain(log_potential[a:b], transition)
        values = alphabet[path]
        age = 0
        for i in range(a, b):
            age = 0 if reliable_ball[i] else age + 1
            if age > round(cfg.abstain_after_s * f.fps):
                values[i - a] = "X"
        if not reliable_ball[a:b].any():
            values[:] = "X"
        labels[a:b] = values
    live_probability = posterior[:, :2].sum(axis=1)
    home_given_live = np.divide(posterior[:, 0], live_probability,
                                out=np.full(len(labels), np.nan), where=live_probability > 0)
    return HierarchicalResult(labels, live, home, posterior, live_probability, home_given_live, log_potential)
