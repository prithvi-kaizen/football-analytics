"""All distances use StatsBomb normalized units, not metres."""

from __future__ import annotations

import math

import numpy as np


def xy(value, bounded: bool = True) -> tuple[float, float]:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ValueError("Expected [x,y]")
    x, y = map(float, value)
    if not math.isfinite(x) or not math.isfinite(y):
        raise ValueError("Non-finite coordinate")
    if bounded and (not 0 <= x <= 120 or not 0 <= y <= 80):
        raise ValueError("Coordinate outside the 120 x 80 pitch")
    return x, y


def period_seconds(timestamp: str) -> float:
    parts = timestamp.split(":")
    if len(parts) != 3:
        raise ValueError("Expected HH:MM:SS.sss period-relative timestamp")
    h, m, s = map(float, parts)
    if not all(math.isfinite(v) for v in (h, m, s)):
        raise ValueError("Invalid timestamp")
    if h < 0 or h != int(h) or not 0 <= m < 60 or m != int(m) or not 0 <= s < 60:
        raise ValueError("Invalid timestamp")
    return h * 3600 + m * 60 + s


def nominal_match_seconds(period: int, timestamp: str) -> float:
    """Nominal display clock only: stoppage can overlap the next period."""
    return {1: 0, 2: 2700, 3: 5400, 4: 6300}[period] + period_seconds(timestamp)


def point_segment_distance(point, start, end) -> tuple[float, float]:
    p, a, b = np.asarray(point), np.asarray(start), np.asarray(end)
    v = b - a
    raw = float(np.dot(p - a, v) / np.dot(v, v)) if np.dot(v, v) else 0.0
    return float(np.linalg.norm(p - (a + np.clip(raw, 0, 1) * v))), raw


def origin_context(origin, opponents) -> dict:
    distances = np.array([math.dist(origin, o) for o in opponents])
    return {
        "opponents_visible": len(opponents),
        "nearest_passer": float(distances.min()) if len(distances) else np.nan,
        "pressure_5": float(np.exp(-0.5 * (distances / 5) ** 2).sum()) if len(distances) else np.nan,
        "opponents_5": int((distances <= 5).sum()) if len(distances) else np.nan,
    }


def pass_geometry(origin, target, opponents) -> dict:
    dx, dy = target[0] - origin[0], target[1] - origin[1]
    angle = math.atan2(dy, dx)
    along = [point_segment_distance(o, origin, target) for o in opponents]
    interior = [d for d, t in along if 0 < t < 1]
    return {
        "distance": math.hypot(dx, dy),
        "angle_sin": math.sin(angle),
        "angle_cos": math.cos(angle),
        "target_x": target[0],
        "target_y": target[1],
        "forward_gain": dx,
        "lane_clearance": min(interior) if interior else np.nan,
        "lane_defenders_3": sum(d <= 3 for d in interior) if opponents else np.nan,
        "nearest_target": min((math.dist(target, o) for o in opponents), default=np.nan),
        "lane_defenders_observed": len(interior),
    }


def territorial_value(probability: float, forward_gain: float) -> float:
    """Expected positive forward gain; failure assigned zero, no turnover cost."""
    return probability * max(0.0, forward_gain)


def point_visible(point, polygon) -> bool | None:
    if not polygon or len(polygon) < 6 or len(polygon) % 2:
        return None
    pts = np.asarray(polygon, dtype=float).reshape(-1, 2)
    if not np.isfinite(pts).all():
        return None
    # Explicit boundary inclusion avoids ray-cast inconsistencies at pitch edges.
    for a, b in zip(pts, np.roll(pts, -1, axis=0)):
        if point_segment_distance(point, a, b)[0] <= 1e-7:
            return True
    inside = False
    x, y = point
    for (ax, ay), (bx, by) in zip(pts, np.roll(pts, -1, axis=0)):
        if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay) + ax:
            inside = not inside
    return inside
