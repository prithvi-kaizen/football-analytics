"""Visible, stationary ground-pass scenarios. These are not causal alternatives."""

from __future__ import annotations

import pandas as pd

from .geometry import origin_context, pass_geometry, territorial_value
from .models import predict_bundle, support_flags


def evaluate_candidates(event_row: dict, scene: dict, bundle: dict | None) -> pd.DataFrame:
    records = []
    for teammate in scene["teammates"]:
        row = {key: event_row[key] for key in ("start_x", "start_y", "period")}
        row.update(origin_context(scene["origin"], scene["opponents"]))
        row["teammates_visible"] = len(scene["teammates"])
        row.update(pass_geometry(scene["origin"], teammate["location"], scene["opponents"]))
        row.update(teammate)
        row["proxy_target"] = teammate["candidate_id"] == scene.get("target_candidate_id")
        flags = support_flags(bundle, row) if bundle else ["target model unavailable: download more matches"]
        if not teammate.get("on_pitch", True):
            flags.append("target outside pitch")
        if teammate["inside_visible_area"] is not True:
            flags.append("target outside known camera polygon")
        if not scene["opponents"]:
            flags.append("no defenders observed")
        row["support_warning"] = "; ".join(flags)
        row["supported"] = not flags
        row["xpass"] = None
        row["expected_forward_gain"] = None
        if bundle and not flags:
            p = float(predict_bundle(bundle, pd.DataFrame([row]))[0])
            row["xpass"] = p
            row["expected_forward_gain"] = territorial_value(p, row["forward_gain"])
        records.append(row)
    if not records:
        return pd.DataFrame()
    result = pd.DataFrame(records)
    result["review_flag"] = False
    actual_proxy = result[result.proxy_target & result.supported]
    if len(actual_proxy) == 1:
        reference = float(actual_proxy.iloc[0].expected_forward_gain)
        result["review_flag"] = (
            ~result.proxy_target
            & result.supported
            & (result.forward_gain >= 10)
            & (result.xpass >= 0.7)
            & (result.expected_forward_gain >= reference + 5)
        )
    return result.sort_values(
        ["supported", "expected_forward_gain", "candidate_id"],
        ascending=[False, False, True],
        na_position="last",
    ).reset_index(drop=True)


def build_review_queue(df: pd.DataFrame, scenes: dict, bundle: dict | None):
    """Prespecified review flags on held-out proxy events only; no target labels exist for alternatives."""
    columns = [
        "event_id",
        "match_id",
        "tournament",
        "team",
        "player",
        "minute",
        "second",
        "candidate_id",
        "xpass",
        "forward_gain",
        "expected_forward_gain",
    ]
    queue = []
    counts = {
        "heldout_proxy_events": 0,
        "events_with_supported_chosen_proxy": 0,
        "candidate_lanes": 0,
        "supported_lanes": 0,
        "flagged_lanes": 0,
        "flagged_events": 0,
    }
    if bundle is None:
        return pd.DataFrame(columns=columns), counts
    for _, row in df[(df.partition == "test") & df.has_target].iterrows():
        counts["heldout_proxy_events"] += 1
        candidates = evaluate_candidates(row.to_dict(), scenes[row.event_id], bundle)
        if candidates.empty:
            continue
        counts["candidate_lanes"] += len(candidates)
        counts["supported_lanes"] += int(candidates.supported.sum())
        counts["events_with_supported_chosen_proxy"] += int(
            (candidates.proxy_target & candidates.supported).any()
        )
        flagged = candidates[candidates.review_flag]
        counts["flagged_events"] += int(len(flagged) > 0)
        counts["flagged_lanes"] += len(flagged)
        for _, candidate in flagged.iterrows():
            record = {k: row[k] for k in columns[:7]}
            record.update({k: candidate[k] for k in columns[7:]})
            queue.append(record)
    return pd.DataFrame(queue, columns=columns), counts
