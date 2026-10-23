import copy
import math
import pytest

from possession_danger.events import action_rows, coordinate, parse_events, possessions, seconds, union_seconds
from conftest import event


@pytest.mark.parametrize("value, expected", [("00:00:00.000", 0), ("00:47:08.606", 2828.606), ("01:00:00", 3600)])
def test_timing(value, expected):
    assert seconds(value) == pytest.approx(expected)


@pytest.mark.parametrize("value", ["", "0:1:2", "00:60:00", "00:00:60", "-1:00:00"])
def test_bad_timing(value):
    with pytest.raises(ValueError):
        seconds(value)


def test_coordinates():
    assert coordinate([120, 80]) == (120, 80)
    assert math.isnan(coordinate(None)[0])
    for bad in [[121, 1], [-1, 0], [1], [float("nan"), 0], [0, 81]]:
        with pytest.raises(ValueError):
            coordinate(bad)


def test_completed_pass_missing_outcome(match):
    raw = [event(1), event(2, t="00:00:03", **{"pass": {"end_location": [90, 40], "outcome": {"name": "Unknown"}}})]
    parsed = parse_events(raw, match)
    assert parsed.complete.tolist() == [True, False]


def test_halftime_clock_and_coordinates(match):
    frame = parse_events([event(1, t="00:47:00"), event(2, t="00:00:02", period=2)], match)
    assert frame.clock.tolist() == [2820, 2822]
    assert frame.display_minute.tolist() == [47, pytest.approx(45 + 2 / 60)]
    assert frame.x.tolist() == [60, 60]


def test_score_before_goal_and_shootout_excluded(match):
    match["home_score"] = 1
    raw = [event(1, "Shot", shot={"outcome": {"name": "Goal"}, "statsbomb_xg": .3}),
           event(2, t="00:00:04", team=20, owner=20, possession=2),
           event(3, "Shot", period=5, shot={"outcome": {"name": "Goal"}})]
    frame = parse_events(raw, match)
    assert len(frame) == 2
    assert frame.score_state.tolist() == ["drawing", "losing"]
    assert frame.home_score_before.tolist() == [0, 1]


def test_own_goal_pair_counted_once(match):
    match["away_score"] = 1
    frame = parse_events([event(1, "Own Goal Against"), event(2, "Own Goal For", team=20),
                          event(3, t="00:00:04")], match)
    assert frame.iloc[-1].score_state == "losing"


def test_score_mismatch_and_duplicates_fail(match):
    with pytest.raises(ValueError, match="Score reconciliation"):
        parse_events([event(1, "Shot", shot={"outcome": {"name": "Goal"}})], match)
    with pytest.raises(ValueError, match="Duplicate"):
        parse_events([event(1), event(1)], match)


def test_opponent_defensive_events_not_attributed(match):
    raw = [event(1, duration=2), event(2, "Pressure", team=20, t="00:00:02", duration=40),
           event(3, "Half End", t="00:00:10", duration=0)]
    frame = parse_events(raw, match)
    seq, _ = possessions(frame)
    assert seq.iloc[0].passes == 1
    assert seq.iloc[0].active_seconds == 2
    assert seq.iloc[0].elapsed_seconds == 2
    assert len(action_rows(frame)) == 1


def test_overlap_and_restart_boundary(match):
    raw = [event(1, duration=5), event(2, t="00:00:03", duration=5),
           event(3, t="00:00:06", possession=2, duration=2), event(4, "Half End", t="00:00:10", duration=0)]
    seq, frame = possessions(parse_events(raw, match))
    assert seq.active_seconds.tolist() == [5, 2]
    assert seq.elapsed_seconds.tolist() == [5, 2]
    assert frame.active_seconds.sum() == 7
    assert union_seconds([(1, 6), (3, 8), (10, 11)]) == 8


def test_missing_successful_endpoint_fails(match):
    with pytest.raises(ValueError, match="endpoint"):
        action_rows(parse_events([event(1, **{"pass": {}})], match))


def test_tiny_negative_duration_flagged_larger_errors_rejected(match):
    frame = parse_events([event(1, "Interception", duration=-.090642)], match)
    assert frame.duration.iloc[0] == 0
    assert frame.raw_duration.iloc[0] == -.090642
    assert frame.duration_repaired.iloc[0]
    with pytest.raises(ValueError, match="duration"):
        parse_events([event(1, duration=-1)], match)


def test_provider_starter_does_not_drop_opposition_counterattack(match):
    # Real-data pattern: the provider chain's starter persists through an opposition shot.
    raw = [event(1, duration=2), event(2, "Ball Recovery", t="00:00:03", team=20),
           event(3, "Carry", t="00:00:03", team=20, carry={"end_location": [95, 40]}, duration=2),
           event(4, "Pressure", t="00:00:04", team=10),
           event(5, "Shot", t="00:00:06", team=20, shot={"outcome": {"name": "Off T"}, "statsbomb_xg": .2}),
           event(6, "Half End", t="00:00:09", duration=0)]
    seq, parsed = possessions(parse_events(raw, match))
    assert seq.team.tolist() == ["Home", "Away"]
    assert seq.shots.sum() == 1
    assert seq.xg.sum() == .2
    assert parsed.loc[parsed.type.eq("Shot"), "owner_id"].iloc[0] == 20
    assert parsed.loc[parsed.type.eq("Shot"), "provider_owner_id"].iloc[0] == 10
    assert len(action_rows(parsed)) == 3
    assert parsed.control_switch.sum() == 1
