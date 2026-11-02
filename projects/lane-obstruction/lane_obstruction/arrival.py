"""Approximate reachability along hypothetical straight, constant-speed ground passes."""
import numpy as np


def arrival_obstruction(ball, targets, defenders, velocity, config, use_velocity=True):
    """Return bounded scores and best interception margins, both target x defender.

    Scores are uncalibrated indices, never interception probabilities.
    """
    b, targets, defenders, velocity = [np.asarray(v, dtype=float) for v in (ball, targets, defenders, velocity)]
    if b.shape != (2,) or targets.ndim != 2 or defenders.ndim != 2 or targets.shape[1:] != (2,) or defenders.shape[1:] != (2,) or velocity.shape != defenders.shape:
        raise ValueError('Expected planar arrays with matching defender velocities')
    if not all(np.isfinite(v).all() for v in [b, targets, defenders, velocity]):
        raise ValueError('Non-finite model inputs')
    for key in ['ball_speed_mps', 'defender_speed_mps', 'transition_s', 'sample_spacing_m']:
        if config[key] <= 0:
            raise ValueError(f'{key} must be positive')
    if min(config['reaction_s'], config['control_radius_m'], config['endpoint_buffer_m']) < 0:
        raise ValueError('Negative arrival parameter')
    speed = np.linalg.norm(velocity, axis=1)
    capped = velocity*np.minimum(1, config['defender_speed_mps']/np.maximum(speed, 1e-12))[:, None]
    reaction_point = defenders + (capped*config['reaction_s'] if use_velocity else 0)
    all_margins = []
    for target in targets:
        delta = target-b
        length = np.linalg.norm(delta)
        start, end = config['endpoint_buffer_m'], length-config['endpoint_buffer_m']
        if end <= start:
            raise ValueError('Degenerate lane')
        distances = np.linspace(start, end, int(np.ceil((end-start)/config['sample_spacing_m']))+1)
        points = b+distances[:, None]*delta/length
        travel = distances/config['ball_speed_mps']
        remaining = np.maximum(0, np.linalg.norm(points[:, None, :]-reaction_point, axis=2)-config['control_radius_m'])
        tti = config['reaction_s']+remaining/config['defender_speed_mps']
        already_reachable = np.linalg.norm(points[:, None, :]-defenders, axis=2) <= config['control_radius_m']
        tti[already_reachable] = 0.0
        all_margins.append((travel[:, None]-tti).max(axis=0))
    margin = np.array(all_margins)
    score = 1/(1+np.exp(-np.clip(margin/config['transition_s'], -60, 60)))
    return score, margin
