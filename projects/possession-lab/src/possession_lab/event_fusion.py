"""Optional uncertain phase evidence; all Phase 1 functions remain untouched.

These are declared probabilistic potentials, not calibrated real Smart Tagging likelihoods.
No event is copied to a hard possession-label interval.
"""
from dataclasses import dataclass

import numpy as np

from .features import extract
from .hierarchical import HierarchicalConfig, decode_chain, hierarchical, observation_heads, transition_matrix
from .schema import blocks


@dataclass(frozen=True)
class FusionConfig:
    stop_probability: float = 0.85
    restart_probability: float = 0.8
    team_probability: float = 0.65
    context_s: float = 6.0
    pre_restart_s: float = 3.0
    power: float = 0.35
    max_log_odds: float = 2.0
    event_coverage: bool = True

    def __post_init__(self):
        for p in (self.stop_probability, self.restart_probability, self.team_probability):
            if not np.isfinite(p) or not 0.5 <= p < 1:
                raise ValueError("semantic probabilities must be finite in [0.5,1)")
        for p in (self.context_s, self.pre_restart_s, self.max_log_odds):
            if not np.isfinite(p) or p <= 0:
                raise ValueError("positive context lengths and evidence cap required")
        if not np.isfinite(self.power) or self.power < 0 or not isinstance(self.event_coverage, bool):
            raise ValueError("invalid fusion power/coverage policy")


@dataclass(frozen=True)
class EventFusionResult:
    labels: np.ndarray
    posterior: np.ndarray
    live_probability: np.ndarray
    tag_live_log_odds: np.ndarray
    tag_home_log_odds: np.ndarray
    event_support: np.ndarray


def _logit(p):
    return np.log(p / (1 - p))


def _cdf(t, event):
    return np.clip((t - event.start) / (event.stop - event.start), 0, 1)


def _context(t, event, tau, after=True):
    """Integrate an exponential context over a uniform uncertain event time in [start,stop)."""
    if after:
        lo, hi = np.maximum(0, t - event.stop), np.maximum(0, t - event.start)
    else:
        lo, hi = np.maximum(0, event.start - t), np.maximum(0, event.stop - t)
    return tau / (event.stop - event.start) * (np.exp(-lo / tau) - np.exp(-hi / tau))


def _validated_unique(tags, period):
    out, seen = [], set()
    for event in tags:
        if (not isinstance(event.start, int) or not isinstance(event.stop, int)
                or not 0 <= event.start < event.stop <= len(period)
                or event.team_hint not in ("H", "A", None)):
            raise ValueError("invalid phase evidence interval/team")
        active = period[event.start:event.stop]
        if not len(active) or active[0] <= 0 or not np.all(active == active[0]):
            raise ValueError("event cannot cross a period/outside-play boundary")
        if event.half is not None and event.half != active[0]:
            raise ValueError("event half disagrees with tracking")
        # No hidden event correctness/identity is consulted. Exact repeats count once.
        key = (event.start, event.stop, event.code, event.team_hint)
        if key not in seen:
            out.append(event)
            seen.add(key)
    return tuple(out)


def event_evidence(f, tags, mode="probabilistic", cfg=FusionConfig()):
    if mode not in ("conservative", "probabilistic"):
        raise ValueError("unknown event fusion mode")
    tags = _validated_unique(tags, f.period)
    n = len(f.period)
    live, home, mass = np.zeros(n), np.zeros(n), np.zeros(n)
    for a, b in blocks(f.period):
        t = np.arange(a, b, dtype=float)
        events = [e for e in tags if a <= e.start < b]
        stops = [e for e in events if e.code == "stoppage signal"]
        restarts = [e for e in events if e.code == "set pieces"]
        if mode == "conservative":
            for stop in stops:
                candidates = [e for e in restarts if stop.stop < e.start
                              and (e.start + e.stop - stop.start - stop.stop) / 2 <= 18 * f.fps]
                if not candidates:
                    continue
                restart = min(candidates, key=lambda e: e.start)
                support = _cdf(t, stop) * (1 - _cdf(t, restart))
                live[a:b] -= min(_logit(cfg.stop_probability), _logit(cfg.restart_probability)) * support
                mass[a:b] += support
        else:
            for event in events:
                if event.code not in ("stoppage signal", "set pieces"):
                    continue  # Team of a generic phase may be the defending team.
                after = _context(t, event, cfg.context_s * f.fps)
                if event.code == "stoppage signal":
                    live[a:b] -= _logit(cfg.stop_probability) * after
                    mass[a:b] += after
                else:
                    before = _context(t, event, cfg.pre_restart_s * f.fps, after=False)
                    live[a:b] += _logit(cfg.restart_probability) * (after - before)
                    mass[a:b] += after + before
                    if event.team_hint is not None:
                        home[a:b] += (1 if event.team_hint == "H" else -1) * _logit(cfg.team_probability) * after
    # Average overlapping reports and cap the evidence budget. Copies cannot create certainty.
    normalizer = np.maximum(1, mass)
    live = np.clip(live / normalizer, -cfg.max_log_odds, cfg.max_log_odds)
    home = np.clip(home / normalizer, -cfg.max_log_odds, cfg.max_log_odds)
    support = np.maximum(np.abs(live), np.abs(home)) * cfg.power > 0.15
    return live, home, support


def fuse_events(f, tags=(), mode="probabilistic", cfg=FusionConfig(), hierarchy_cfg=HierarchicalConfig(), enabled=True):
    if not enabled or not tags or cfg.power == 0:
        original = hierarchical(f, hierarchy_cfg)
        zeros = np.zeros(len(f.period))
        return EventFusionResult(original.labels, original.posterior, original.live_probability,
                                 zeros, zeros.copy(), zeros.astype(bool))
    live_odds, home_odds, support = event_evidence(f, tags, mode, cfg)
    _, _, tracking_potential = observation_heads(f, hierarchy_cfg)
    q = 1 / (1 + np.exp(-live_odds))
    r = 1 / (1 + np.exp(-home_odds))
    potential = np.c_[4 * q * r, 4 * q * (1 - r), 2 * (1 - q), 2 * (1 - q)]
    joint = tracking_potential + cfg.power * np.log(potential)
    labels = np.full(len(f.period), "X")
    posterior = np.full((len(labels), 4), np.nan)
    reliable = f.ball_observed & (f.reliability >= 0.45)
    if cfg.event_coverage:
        reliable = reliable | support
    for a, b in blocks(f.period):
        path, posterior[a:b] = decode_chain(joint[a:b], transition_matrix(f.fps, hierarchy_cfg))
        values = np.array(["H", "A", "D", "D"])[path]
        age = 0
        for i in range(a, b):
            age = 0 if reliable[i] else age + 1
            if age > round(hierarchy_cfg.abstain_after_s * f.fps):
                values[i - a] = "X"
        if not reliable[a:b].any():
            values[:] = "X"
        labels[a:b] = values
    return EventFusionResult(labels, posterior, posterior[:, :2].sum(axis=1), live_odds, home_odds, support)


def infer_events(batch, tags=(), **kwargs):
    """Additive pipeline entry point; original infer(batch, 'hierarchical') is unchanged."""
    return fuse_events(extract(batch), tags, **kwargs)
