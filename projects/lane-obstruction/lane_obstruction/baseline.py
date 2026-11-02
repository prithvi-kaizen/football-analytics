"""Finite-corridor baseline; no arrival time assumptions."""
import numpy as np


def corridor_obstruction(ball, targets, defenders, halfwidth=1.0, endpoint_buffer=2.0):
    """Return a target-by-defender binary matrix using finite interior segments."""
    ball, targets, defenders = map(lambda a: np.asarray(a, dtype=float), (ball, targets, defenders))
    if halfwidth <= 0 or endpoint_buffer < 0:
        raise ValueError('Invalid corridor parameters')
    if targets.ndim != 2 or defenders.ndim != 2 or targets.shape[1:] != (2,) or defenders.shape[1:] != (2,):
        raise ValueError('Expected planar positions')
    delta = targets-ball
    lengths = np.linalg.norm(delta, axis=1)
    if not np.isfinite(ball).all() or not np.isfinite(targets).all() or not np.isfinite(defenders).all() or np.any(lengths <= 2*endpoint_buffer):
        raise ValueError('Non-finite coordinates or degenerate corridor')
    unit = delta/lengths[:, None]
    along = np.einsum('di,ti->td', defenders-ball, unit)
    closest = ball + unit[:, None, :]*np.clip(along, endpoint_buffer, lengths[:, None]-endpoint_buffer)[:, :, None]
    # Distance to a flat-ended corridor, not circular caps around the endpoints.
    interior = (along >= endpoint_buffer) & (along <= lengths[:, None]-endpoint_buffer)
    return interior & (np.linalg.norm(defenders[None, :, :]-closest, axis=2) <= halfwidth)


def marginal_obstruction(matrix):
    """Team lane obstruction and each defender's exclusive removal effect."""
    m = np.asarray(matrix, dtype=float)
    if m.ndim != 2 or not len(m) or not m.shape[1] or not np.isfinite(m).all() or (m < 0).any() or (m > 1).any():
        raise ValueError('Expected nonempty bounded target-by-defender scores')
    team = m.max(axis=1)
    without = np.column_stack([np.delete(m, d, axis=1).max(axis=1) if m.shape[1] > 1 else np.zeros(len(m)) for d in range(m.shape[1])])
    return team, (team[:, None]-without).mean(axis=0)
