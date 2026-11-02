"""Fixed engineering priors. No fitting and no access to any labels or ground-truth files."""
from dataclasses import dataclass

import numpy as np

from .features import Features
from .schema import blocks


@dataclass(frozen=True)
class ModelConfig:
    control_distance_m: float = 2.5
    distance_margin_m: float = 0.7
    confirm_seconds: float = 0.32
    stationary_seconds: float = 1.2
    hold_seconds: float = 3.0
    min_reliability: float = 0.45
    hmm_stay_probability: float = 0.985

    def __post_init__(self):
        values = (self.control_distance_m, self.distance_margin_m, self.confirm_seconds,
                  self.stationary_seconds, self.hold_seconds)
        if not all(np.isfinite(x) and x > 0 for x in values):
            raise ValueError("model distances and durations must be finite and positive")
        if not 0 <= self.min_reliability <= 1 or not 0 < self.hmm_stay_probability < 1:
            raise ValueError("invalid probability")


def evidence(f: Features, cfg: ModelConfig):
    candidate = np.full(len(f.period), "X")
    reliable = f.reliability >= cfg.min_reliability
    h = reliable & (f.nearest_home_m < cfg.control_distance_m) & (
        f.nearest_away_m - f.nearest_home_m > cfg.distance_margin_m)
    a = reliable & (f.nearest_away_m < cfg.control_distance_m) & (
        f.nearest_home_m - f.nearest_away_m > cfg.distance_margin_m)
    candidate[h] = "H"
    candidate[a] = "A"
    dead = reliable & (f.out_of_bounds | (f.stationary_seconds >= cfg.stationary_seconds))
    candidate[dead] = "D"
    candidate[f.period == 0] = "X"
    return candidate


def state_machine(f: Features, cfg=ModelConfig()):
    candidate = evidence(f, cfg)
    out = np.full(len(candidate), "X")
    required = max(1, round(cfg.confirm_seconds * f.fps))
    for start, stop in blocks(f.period):
        state, pending, count = "X", "X", 0
        age = 0
        for i in range(start, stop):
            value = candidate[i]
            if value != "X":
                age = 0
                count = count + 1 if value == pending else 1
                pending = value
                if count >= required:
                    state = value
            else:
                age += 1
                pending, count = "X", 0
            # A short gap carries the last controlled state. A long gap abstains, never becomes D.
            out[i] = state if age <= round(cfg.hold_seconds * f.fps) else "X"
    return out


def hmm(f: Features, cfg=ModelConfig()):
    """Three hidden states H/A/D, fixed categorical emissions, log-space Viterbi per period.

    X is an output abstention mask, not a fourth physical state. This is offline inference.
    """
    candidate = evidence(f, cfg)
    out = np.full(len(candidate), "X")
    alphabet = np.array(["H", "A", "D"])
    trans = np.full((3, 3), (1 - cfg.hmm_stay_probability) / 2)
    np.fill_diagonal(trans, cfg.hmm_stay_probability)
    log_trans = np.log(trans)
    for start, stop in blocks(f.period):
        obs = candidate[start:stop]
        emission = np.full((len(obs), 3), 1 / 3)
        for state, label in enumerate(alphabet):
            emission[obs == label] = 0.05
            emission[obs == label, state] = 0.9
        score = np.empty_like(emission)
        back = np.zeros(emission.shape, dtype=np.int8)
        score[0] = np.log(emission[0]) - np.log(3)
        for i in range(1, len(obs)):
            options = score[i - 1, :, None] + log_trans
            back[i] = np.argmax(options, axis=0)
            score[i] = options[back[i], np.arange(3)] + np.log(emission[i])
        path = np.zeros(len(obs), dtype=np.int8)
        path[-1] = np.argmax(score[-1])
        for i in range(len(obs) - 1, 0, -1):
            path[i - 1] = back[i, path[i]]
        labels = alphabet[path]
        # Never turn a wholly unobserved period into a confident arbitrary H.
        age = 0
        for i, value in enumerate(obs):
            age = age + 1 if value == "X" else 0
            if age > round(cfg.hold_seconds * f.fps):
                labels[i] = "X"
        if np.all(obs == "X"):
            labels[:] = "X"
        out[start:stop] = labels
    return out
