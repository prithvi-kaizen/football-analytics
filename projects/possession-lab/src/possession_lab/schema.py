from dataclasses import dataclass, field
from typing import Protocol

import numpy as np

LABELS = ("H", "A", "D", "X")


def periods_from_inclusive(n_frames, ranges):
    """Translate published inclusive period ranges without inferring when play restarts."""
    if not isinstance(n_frames, int) or n_frames <= 0:
        raise ValueError("positive integer frame count required")
    period = np.zeros(n_frames, dtype=int)
    used = set()
    for identity, start, last in ranges:
        if (not all(isinstance(x, int) for x in (identity, start, last))
                or identity <= 0 or identity in used or not 0 <= start <= last < n_frames
                or period[start:last + 1].any()):
            raise ValueError("invalid, repeated or overlapping period ranges")
        period[start:last + 1] = identity
        used.add(identity)
    return period


def to_metres(xy, pitch, convention="unit"):
    """Preserve off-pitch positions and NaNs; never infer scale from observed extrema."""
    xy = np.asarray(xy, dtype=float)
    if xy.shape[-1:] != (2,) or not np.all(np.isfinite(pitch)) or min(pitch) <= 0:
        raise ValueError("coordinates need an xy axis and positive finite pitch dimensions")
    if convention == "unit":
        return xy * np.asarray(pitch)
    if convention == "metres":
        return xy.copy()
    raise ValueError("unsupported coordinate convention")


def blocks(period):
    """Half-open blocks. Period 0 is outside play; even adjacent halves reset inference."""
    period = np.asarray(period)
    edges = np.r_[0, np.flatnonzero(period[1:] != period[:-1]) + 1, len(period)]
    return [(int(a), int(b)) for a, b in zip(edges[:-1], edges[1:]) if period[a] > 0]


@dataclass(frozen=True)
class TrackingBatch:
    frame: np.ndarray
    time_s: np.ndarray
    period: np.ndarray
    ball: np.ndarray
    home: np.ndarray
    away: np.ndarray
    pitch: tuple[float, float] = (105.0, 68.0)
    fps: float = 25.0
    provenance: dict = field(default_factory=dict)

    def __post_init__(self):
        n = len(self.frame)
        if not n or not np.issubdtype(self.frame.dtype, np.integer):
            raise ValueError("nonempty integer frame axis required")
        if not np.array_equal(self.frame, np.arange(n)):
            raise ValueError("canonical frames must be exactly 0..n-1")
        if self.time_s.shape != (n,) or not np.isfinite(self.time_s).all():
            raise ValueError("finite timestamps required")
        if n > 1 and not np.all(np.diff(self.time_s) > 0):
            raise ValueError("timestamps must increase strictly")
        if (self.period.shape != (n,) or not np.issubdtype(self.period.dtype, np.integer)
                or (self.period < 0).any()):
            raise ValueError("period must be nonnegative integers; 0 means outside play")
        for value in np.unique(self.period[self.period > 0]):
            ids = np.flatnonzero(self.period == value)
            if len(ids) != ids[-1] - ids[0] + 1:
                raise ValueError("each period must occupy a single contiguous block")
        if self.ball.shape != (n, 2):
            raise ValueError("ball must have shape (frames, 2)")
        for team in (self.home, self.away):
            if team.ndim != 3 or team.shape[0] != n or team.shape[2] != 2 or team.shape[1] < 1:
                raise ValueError("teams need shape (frames, slots, 2), with at least one slot")
        if any(np.isinf(x).any() for x in (self.ball, self.home, self.away)):
            raise ValueError("use NaN for missing coordinates, never infinity")
        if not np.isfinite(self.fps) or self.fps <= 0:
            raise ValueError("positive finite fps required")
        to_metres(self.ball, self.pitch, "metres")
        if self.provenance.get("kind") not in ("synthetic", "public_sample"):
            raise ValueError("this preparation package accepts only synthetic or public_sample data")


class TrackingAdapter(Protocol):
    def load(self) -> TrackingBatch: ...
