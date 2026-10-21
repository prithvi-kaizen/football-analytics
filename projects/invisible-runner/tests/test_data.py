import json
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from invisible_runner.data import (annotate_context, attack_sign, clock_seconds, download,
                                   parse_tracking, sha256, smooth_tracking, validate_intervals)


def record(frame=10, period=1, x=0, pid=101):
    return dict(frame=frame, period=period, possession={"player_id": 201, "group": "home team"},
                ball_data=dict(x=0, y=1, is_detected=True),
                player_data=[dict(player_id=pid, x=x, y=0, is_detected=True)])


def test_parser_nulls_and_ids(tmp_path, metadata):
    path = tmp_path / "sample.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in [record(0, None), record(), record(11, x=None), record(12, pid=999)]))
    df, audit = parse_tracking(path, metadata)
    assert df.player_id.tolist() == [101]
    assert df.iloc[0].team_id == 10
    assert df.iloc[0].x == 0
    assert audit["null_period_frames"] == audit["invalid_positions"] == audit["unknown_players"] == 1


@pytest.mark.parametrize("records", [[record(), record()], [record(11), record(10)]])
def test_parser_rejects_duplicate_or_reversed_frames(tmp_path, metadata, records):
    path = tmp_path / "bad.jsonl"
    path.write_text("\n".join(map(json.dumps, records)))
    with pytest.raises(ValueError, match="Non-increasing"):
        parse_tracking(path, metadata)


def test_parser_duplicate_player(tmp_path, metadata):
    r = record()
    r["player_data"] *= 2
    path = tmp_path / "bad.jsonl"
    path.write_text(json.dumps(r))
    with pytest.raises(ValueError, match="Duplicate player"):
        parse_tracking(path, metadata)


def test_parser_malformed(tmp_path, metadata):
    path = tmp_path / "bad.jsonl"
    path.write_text("not json")
    with pytest.raises(ValueError, match="line 1"):
        parse_tracking(path, metadata)


def test_coordinates_and_halves(metadata):
    assert attack_sign(metadata, 10, 1) == 1
    assert attack_sign(metadata, 10, 2) == -1
    assert attack_sign(metadata, 20, 1) == -1
    assert clock_seconds(28, 1, metadata) == pytest.approx(1.8)
    assert clock_seconds(27824, 2, metadata) == pytest.approx(2702.4)
    with pytest.raises(ValueError):
        attack_sign(metadata, 999, 1)


def test_phase_half_open_and_period_aware(metadata):
    df = pd.DataFrame(dict(frame=[19, 20, 25, 27824], period=[1, 1, 1, 2],
                           player_id=[101]*4))
    phases = pd.DataFrame([dict(match_id=1, frame_start=10, frame_end=20, period=1, team_in_possession_id=10, attacking_side="left_to_right"),
                           dict(match_id=1, frame_start=20, frame_end=25, period=1, team_in_possession_id=20, attacking_side="right_to_left"),
                           dict(match_id=1, frame_start=27820, frame_end=27825, period=2, team_in_possession_id=10, attacking_side="right_to_left")])
    events = pd.DataFrame([dict(match_id=1, frame_start=20, frame_end=20, period=1, event_type="player_possession", player_id=101)])
    annotated = annotate_context(df, phases, events, metadata)
    assert annotated.phase_team.iloc[:2].tolist() == [10, 20]
    assert np.isnan(annotated.phase_team.iloc[2])
    assert annotated.phase_team.iloc[3] == 10
    assert annotated.provider_on_ball.tolist() == [False, True, False, False]


def test_interval_rejects_wrong_match():
    events = pd.DataFrame([dict(match_id=2, period=1, frame_start=10, frame_end=11)])
    with pytest.raises(ValueError, match="Wrong match"):
        validate_intervals(events, 1)


def trajectory(frames, x):
    return pd.DataFrame(dict(frame=frames, period=1, player_id=101, x=x, y=0))


def test_smoothing_preserves_straight_line_speed():
    df = smooth_tracking(trajectory(np.arange(30), np.arange(30)*.6))
    assert np.allclose(df.speed, 6)
    assert np.allclose(df.sx, df.x)


def test_smoothing_does_not_bridge_gaps_or_periods():
    df = trajectory([0, 1, 2, 10, 11, 12], [0, .5, 1, 40, 40.5, 41])
    cleaned = smooth_tracking(df)
    assert cleaned.segment.nunique() == 2
    assert not cleaned.raw_jump.any()
    assert cleaned.speed.max() == pytest.approx(5)


def test_raw_jump_flagged_before_smoothing():
    df = smooth_tracking(trajectory(np.arange(20), [i*.5 if i<10 else 40+(i-10)*.5 for i in range(20)]))
    assert df.loc[9:10, "raw_jump"].all()
    assert df.loc[9:10, "sx"].isna().all()
    assert df.loc[8, "segment"] != df.loc[11, "segment"]


def test_download_cache_and_corruption(tmp_path):
    import io
    path = tmp_path / "sample.jsonl"
    with patch("invisible_runner.data.urlopen", return_value=io.BytesIO(b"a\nb\nc\n")) as request:
        receipt = download("https://example.invalid/data", path, 2)
        assert path.read_bytes() == b"a\nb\n"
        assert not receipt["complete"]
        assert receipt["sha256"] == sha256(path)
        download("https://example.invalid/data", path, 2)
        assert request.call_count == 1
    path.write_bytes(b"corruption")
    with patch("invisible_runner.data.urlopen", return_value=io.BytesIO(b"a\nb\nc\n")) as request:
        download("https://example.invalid/data", path, 2)
        assert request.call_count == 1


def test_failed_download_leaves_no_partial_file(tmp_path):
    path = tmp_path / "data.json"
    with patch("invisible_runner.data.urlopen", side_effect=OSError("network unavailable")):
        with pytest.raises(OSError):
            download("https://example.invalid/data", path)
    assert not path.exists()
    assert not list(tmp_path.glob("*.part"))
