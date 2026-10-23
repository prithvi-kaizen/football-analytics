"""Pre-turnover geometry. These functions never accept transition outcomes."""
from __future__ import annotations

import numpy as np
from scipy.spatial import ConvexHull, QhullError
from scipy.spatial.distance import cdist


def clear_lane(origin, target, defenders, radius=2.) -> bool:
    """Static segment corridor; endpoints themselves do not block the lane."""
    origin, target, defenders = map(lambda a: np.asarray(a, dtype=float), (origin,target,defenders))
    direction = target - origin
    norm = direction @ direction
    if norm == 0:
        return False
    if not len(defenders):
        return True
    projection = ((defenders - origin) @ direction) / norm
    nearest = origin + projection[:,None] * direction
    distances = np.linalg.norm(defenders - nearest,axis=1)
    return not bool(np.any((projection > 0) & (projection < 1) & (distances <= radius)))


def central_grid(ball, length=105., width=68., depth=30., half_width=10., spacing=2.):
    """Cell centres in the central, goal-side 30 x 20 m rectangle, pitch clipped."""
    x = float(ball[0]) - np.arange(spacing/2, depth, spacing)
    x = x[(x > -length/2) & (x < length/2)]
    y = np.arange(-min(half_width,width/2)+spacing/2, min(half_width,width/2),spacing)
    return np.array([(a,b) for a in x for b in y], dtype=float).reshape(-1,2)


def rest_geometry(defenders, opponents, ball, length=105., width=68.) -> dict:
    """All input coordinates are rotated so the losing team attacked +x.

    Inputs contain outfield players only. The losing team's own goal is -x.
    """
    d, o, ball = [np.asarray(a,dtype=float).reshape(-1,2) if i<2 else np.asarray(a,dtype=float)
                  for i,a in enumerate([defenders,opponents,ball])]
    if not np.isfinite(np.r_[d.ravel(),o.ravel(),ball]).all():
        raise ValueError("Geometry requires finite coordinates")
    rest = d[d[:,0] <= ball[0]]
    options = o[(o[:,0] <= ball[0]-3.) & (np.linalg.norm(o-ball,axis=1) <= 40.)]
    rms, depth, spread, area = np.nan, np.nan, np.nan, np.nan
    if len(rest) >= 2:
        rms = float(np.sqrt(np.mean(np.sum((rest-rest.mean(axis=0))**2,axis=1))))
        depth, spread = map(float,np.ptp(rest,axis=0))
    if len(rest) >= 3:
        try:
            area = float(ConvexHull(rest).volume)
        except QhullError:
            area = 0.
    grid = central_grid(ball,length,width)
    exposed = np.mean(cdist(grid,rest).min(axis=1) > 5.) if len(rest) and len(grid) else (1. if len(grid) else np.nan)
    lanes = [clear_lane(ball,target,d) for target in options]
    nearest = cdist(options,rest).min(axis=1) if len(options) and len(rest) else np.array([])
    result = dict(behind_ball=len(rest), counter_options=len(options), coverage_margin=len(rest)-len(options),
                  compactness_rms_m=rms, rest_depth_m=depth, rest_width_m=spread, hull_area_m2=area,
                  central_exposed_fraction=float(exposed), open_lanes=sum(lanes),
                  open_lane_fraction=float(np.mean(lanes)) if lanes else 0.,
                  nearest_option_mean_m=float(nearest.mean()) if len(nearest) else np.nan,
                  nearest_option_max_m=float(nearest.max()) if len(nearest) else np.nan)
    return result


def vulnerability_score(metrics: dict) -> float:
    """Fixed equal-weight diagnostic, 0..100; never a probability."""
    components = [1.-min(metrics["behind_ball"]/4.,1.),
                  min(metrics["compactness_rms_m"]/20.,1.) if metrics["behind_ball"]>=2 else 1.,
                  metrics["central_exposed_fraction"], metrics["open_lane_fraction"]]
    return float(100.*np.mean(components))
