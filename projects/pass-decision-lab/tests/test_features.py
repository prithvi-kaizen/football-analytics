import pandas as pd
import pytest

from passlab.features import eligible, extract_match, frame_players, outcome_label
from passlab.models import FEATURE_SETS


def test_actual_join_recipient_proxy_and_completion(match, events, frames):
    rows, scenes, audit = extract_match(match, events, frames)
    assert len(rows) == 1
    r = rows[0]
    assert r["complete"] == 1 and r["has_target"]
    assert r["target_x"] == 51  # snapshot position, not recorded endpoint 53
    assert r["history_age"] == 2 and r["history_distance"] == 1
    assert len(scenes["pass"]["teammates"]) == 2
    assert audit["passes_with_frame"] == 1


def test_outcome_changes_only_label_and_not_features(match, events, frames):
    a = extract_match(match, events, frames)[0][0]
    events[-1]["pass"].update(
        {"end_location": [120, 80], "length": 99, "angle": 3, "outcome": {"name": "Out"}}
    )
    events[-1]["duration"] = 100
    b = extract_match(match, events, frames)[0][0]
    for cols in FEATURE_SETS.values():
        for col in cols:
            assert a[col] == b[col] or pd.isna(a[col]) and pd.isna(b[col])
    assert a["complete"] == 1 and b["complete"] == 0


def test_no_future_or_other_period_identity(match, events, frames):
    events[0]["timestamp"] = "00:00:11.000"
    assert not extract_match(match, events, frames)[0][0]["has_target"]
    events[0]["timestamp"] = "00:00:08.000"
    events[0]["period"] = 2
    assert not extract_match(match, events, frames)[0][0]["has_target"]


def test_old_or_ambiguous_recipient_unmatched(match, events, frames):
    events[0]["timestamp"] = "00:00:04.000"
    assert not extract_match(match, events, frames)[0][0]["has_target"]
    events[0]["timestamp"] = "00:00:08.000"
    frames[0]["freeze_frame"][2]["location"] = [50, 41]
    assert not extract_match(match, events, frames)[0][0]["has_target"]


def test_unknown_missing_and_special_passes(match, events, frames):
    assert outcome_label(events[-1]) == 1
    events[-1]["pass"]["outcome"] = {"name": "Unknown"}
    assert outcome_label(events[-1]) is None
    assert extract_match(match, events, frames)[2]["unknown_outcome"] == 1
    events[-1]["pass"]["type"] = {"name": "Corner"}
    assert not eligible(events[-1])
    events[-1]["pass"].pop("type")
    events[-1]["period"] = 5
    assert not eligible(events[-1])


def test_missing_frame_preserves_event_observation(match, events):
    rows, scenes, audit = extract_match(match, events, [])
    assert not rows[0]["has_frame"] and not rows[0]["has_target"]
    assert not scenes and audit["passes_without_frame"] == 1


def test_duplicate_keys_fail(match, events, frames):
    with pytest.raises(ValueError, match="Duplicate event IDs"):
        extract_match(match, events + events, frames)
    with pytest.raises(ValueError, match="Duplicate frame"):
        extract_match(match, events, frames + frames)


def test_missing_actor_and_outside_polygon_handled(frames):
    frames[0]["freeze_frame"] = frames[0]["freeze_frame"][1:]
    frames[0]["visible_area"] = []
    teammates, opponents = frame_players(frames[0])
    assert len(teammates) == 2 and len(opponents) == 1
    assert teammates[0]["inside_visible_area"] is None


def test_feature_whitelist_excludes_results_and_ids():
    columns = set(sum(FEATURE_SETS.values(), []))
    assert columns.isdisjoint(
        {
            "complete",
            "match_id",
            "event_id",
            "actual_end",
            "end_location",
            "length",
            "angle",
            "duration",
            "recipient",
            "history_age",
            "under_pressure",
        }
    )


def test_off_pitch_defender_is_retained_in_geometry(match, events, frames):
    from collections import Counter

    frames[0]["freeze_frame"][-1]["location"] = [45, -1]
    audit = Counter()
    teammates, opponents = frame_players(frames[0], audit)
    assert opponents == [[45, -1]]
    assert audit["off_pitch_frame_players"] == 1
    assert not audit["invalid_frame_players"]
    frames[0]["freeze_frame"][1]["location"] = [51, -1]
    teammates, opponents = frame_players(frames[0])
    assert not teammates[0]["on_pitch"]
    events[0]["location"] = [50, 0]
    assert not extract_match(match, events, frames)[0][0]["has_target"]
