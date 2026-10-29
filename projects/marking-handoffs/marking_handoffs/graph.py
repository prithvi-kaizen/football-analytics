"""Weighted opponent graphs. Scores are heuristics, never marking probabilities."""
from __future__ import annotations

import numpy as np


def edge_features(attacker_xy, defender_xy, attacker_v, defender_v, sign, config):
    """Arrays are [time, defender, xy]; local line uses self + two nearest teammates."""
    rel = defender_xy - attacker_xy[:, None]
    distance = np.linalg.norm(rel, axis=2)
    rv = defender_v - attacker_v[:, None]
    radial = np.sum(rv * rel, axis=2) / np.maximum(distance, 1e-6)
    predicted = np.linalg.norm(rel + config["prediction_s"] * rv, axis=2)
    goal_margin = rel[:, :, 0] * sign
    teammate_dist = np.linalg.norm(defender_xy[:, :, None] - defender_xy[:, None, :], axis=3)
    neighbours = np.argsort(teammate_dist, axis=2)[:, :, :min(3, defender_xy.shape[1])]
    depths = np.broadcast_to(defender_xy[:, None, :, 0], teammate_dist.shape)
    line = np.median(np.take_along_axis(depths, neighbours, axis=2), axis=2)
    structure = np.abs(attacker_xy[:, None, 0] - line)
    score = distance + config["motion_weight_s"] * np.clip(radial, -3, 6) + config["structure_weight"] * structure
    finite = np.isfinite(score) & np.isfinite(predicted)
    geometry = (goal_margin >= -config["goal_tolerance_m"]) & (predicted <= config["prediction_radius_m"]) & finite
    plausible = geometry & (distance <= config["radius_m"])
    retain = geometry & (distance <= config["release_radius_m"])
    return dict(distance=distance, radial=radial, predicted=predicted, goal_margin=goal_margin,
                structure=structure, score=score, plausible=plausible, retain=retain,
                edge=finite & (distance <= config["graph_radius_m"]))


def real_features(data, segment, config):
    fr, ai, di = segment["frames"], segment["attacker"], segment["defenders"]
    return edge_features(data["xy"][fr, ai], data["xy"][fr[:, None], di],
                         data["velocity"][fr, ai], data["velocity"][fr[:, None], di],
                         segment["sign"], config)
