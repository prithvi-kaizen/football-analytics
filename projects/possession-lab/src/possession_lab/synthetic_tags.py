"""Noisy observation channel. This module never imports world truth or private rule objects."""
from dataclasses import dataclass, replace

import numpy as np

from .schema import blocks
from .tagging_interface import PhaseInterval

CATEGORIES = ("set pieces", "stoppage signal", "phase", "other")


@dataclass(frozen=True)
class AnnotationConfig:
    missing_rate: float = 0.2
    false_events_per_s: float = 0.025
    category_error: float = 0.12
    unknown_team: float = 0.25
    wrong_team: float = 0.15
    offset_s: float = 0.5
    delay_s: float = 0.0
    width_s: float = 1.8
    duplicate_rate: float = 0.15
    conflict_rate: float = 0.1
    shared_view_loss: float = 0.0

    def __post_init__(self):
        for x in (self.missing_rate, self.category_error, self.unknown_team, self.wrong_team,
                  self.duplicate_rate, self.conflict_rate, self.shared_view_loss):
            if not np.isfinite(x) or not 0 <= x <= 1:
                raise ValueError("invalid annotation probability")
        for x in (self.false_events_per_s, self.offset_s, self.width_s):
            if not np.isfinite(x) or x < 0:
                raise ValueError("invalid annotation rate or timing uncertainty")
        if not np.isfinite(self.delay_s) or self.width_s == 0:
            raise ValueError("invalid annotation timing")


def _interval(frame, category, team, a, b, half, rng, cfg, fps):
    centre = frame + (cfg.delay_s + rng.normal(0, cfg.offset_s)) * fps
    width = max(2, round(cfg.width_s * fps * rng.uniform(0.6, 1.5)))
    start = int(np.clip(round(centre - width / 2), a, b - 1))
    stop = int(np.clip(round(centre + width / 2), start + 1, b))
    event_type = str(rng.choice(["throw-in", "free kick", "corner kick", "goal kick"])) if category == "set pieces" else "synthetic cue"
    if team is not None:
        if rng.random() < cfg.unknown_team or event_type == "throw-in":
            team = None
        elif rng.random() < cfg.wrong_team:
            team = "A" if team == "H" else "H"
    return PhaseInterval(start, stop, category, team, half, (("type", event_type),), None)


def observe_actions(cues, period, seed, cfg=AnnotationConfig(), ball_observed=None, fps=25):
    """Only public action projections, timeline and optional shared-view visibility are accepted.

    No label, true dead duration, event correctness flag, private ruling or origin score is used.
    """
    rng = np.random.default_rng(seed)
    out = []
    mapping = {"restart_attempt": [0.8, 0.02, 0.12, 0.06], "pass": [0.1, 0.01, 0.7, 0.19],
               "stop_gesture": [0.08, 0.8, 0.06, 0.06], "advisory_gesture": [0.04, 0.15, 0.5, 0.31],
               "controlled_touch": [0.04, 0.01, 0.8, 0.15]}
    for a, b in blocks(period):
        half = int(period[a])
        for cue in cues:
            if not a <= cue.frame < b:
                continue
            if cue.kind not in mapping:
                raise ValueError("unknown visible action cue")
            miss = cfg.missing_rate
            if ball_observed is not None and not ball_observed[cue.frame]:
                miss = 1 - (1 - miss) * (1 - cfg.shared_view_loss)
            if rng.random() < miss:
                continue
            category = str(rng.choice(CATEGORIES, p=mapping[cue.kind]))
            if rng.random() < cfg.category_error:
                category = str(rng.choice([c for c in CATEGORIES if c != category]))
            event = _interval(cue.frame, category, cue.team, a, b, half, rng, cfg, fps)
            out.append(event)
            if rng.random() < cfg.duplicate_rate:
                out.append(event)  # No hidden duplicate ID is provided to the decoder.
            if rng.random() < cfg.conflict_rate:
                opposite = "stoppage signal" if category == "set pieces" else "set pieces"
                out.append(replace(event, code=opposite, team_hint="A" if event.team_hint == "H" else "H"))
        for _ in range(rng.poisson((b - a) / fps * cfg.false_events_per_s)):
            # Same unknown confidence and window mechanism for detections and false positives.
            out.append(_interval(int(rng.integers(a, b)), str(rng.choice(CATEGORIES)),
                                 str(rng.choice(["H", "A"])), a, b, half, rng, cfg, fps))
    return tuple(sorted(out, key=lambda e: (e.start, e.stop, e.code, e.team_hint or "")))


def uninformative_tags(period, seed, events_per_s=0.12, fps=25):
    """Drawn independently of actions/truth; shared exactly across opposing twin worlds."""
    cfg = AnnotationConfig(false_events_per_s=events_per_s)
    return observe_actions((), period, seed, cfg, fps=fps)


def relocate_tags(tags, period, seed, mode="shuffle"):
    """Preserve tag contents/counts/widths, but destroy within-period temporal alignment."""
    if mode not in ("shuffle", "shift"):
        raise ValueError("unknown tag control")
    rng = np.random.default_rng(seed)
    out = []
    for a, b in blocks(period):
        for event in tags:
            if not a <= event.start < b:
                continue
            width = min(event.stop - event.start, b - a)
            if mode == "shuffle":
                start = int(rng.integers(a, b - width + 1))
            else:
                start = a + ((event.start - a + (b - a) // 2) % max(1, b - a - width + 1))
            out.append(replace(event, start=start, stop=start + width))
    return tuple(sorted(out, key=lambda e: (e.start, e.stop, e.code, e.team_hint or "")))
