"""Clearly synthetic geometry used only for unit tests."""

import pytest


@pytest.fixture
def metadata():
    return dict(id=1, home_team={"id": 10}, away_team={"id": 20},
                home_team_side=["left_to_right", "right_to_left"],
                pitch_length=104, pitch_width=68,
                match_periods=[dict(period=1, start_frame=10), dict(period=2, start_frame=27800)],
                players=[dict(id=101, team_id=10, short_name="Test runner", player_role={"acronym": "LW"}),
                         dict(id=201, team_id=20, short_name="Test defender", player_role={"acronym": "CB"})])
