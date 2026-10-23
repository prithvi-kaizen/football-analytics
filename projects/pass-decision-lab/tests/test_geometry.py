import math

import pytest

from passlab.geometry import (
    nominal_match_seconds,
    origin_context,
    pass_geometry,
    period_seconds,
    point_segment_distance,
    point_visible,
    territorial_value,
    xy,
)


@pytest.mark.parametrize("point", [[-1, 40], [121, 30], [40, 81], [math.nan, 20], [20], None])
def test_invalid_coordinates(point):
    with pytest.raises((ValueError, TypeError)):
        xy(point)


def test_coordinates_not_mirrored_and_y_angle():
    assert xy([120, 80]) == (120.0, 80.0)
    g = pass_geometry([10, 10], [13, 14], [[11.5, 12]])
    assert g["distance"] == 5
    assert g["angle_sin"] == pytest.approx(0.8)
    assert g["forward_gain"] == 3
    assert g["lane_clearance"] == 0
    assert g["lane_defenders_3"] == 1


def test_projection_not_infinite_line():
    assert point_segment_distance([12, 3], [0, 0], [10, 0]) == (pytest.approx(math.sqrt(13)), 1.2)
    g = pass_geometry([0, 0], [10, 0], [[12, 0], [-2, 0]])
    assert math.isnan(g["lane_clearance"])
    assert g["lane_defenders_3"] == 0
    assert point_segment_distance([3, 4], [0, 0], [0, 0]) == (5, 0)


def test_missing_defenders_not_clear_lane():
    assert math.isnan(origin_context([10, 10], [])["nearest_passer"])
    assert math.isnan(pass_geometry([10, 10], [20, 10], [])["lane_defenders_3"])


@pytest.mark.parametrize("time", ["00:60:00", "00:00:60", "-1:00:00", "bad", "00:00:nan"])
def test_bad_timestamps(time):
    with pytest.raises(ValueError):
        period_seconds(time)


def test_period_and_stoppage_time():
    assert period_seconds("00:47:05.125") == 2825.125
    assert nominal_match_seconds(2, "00:00:02.500") == 2702.5
    assert nominal_match_seconds(4, "00:15:00") == 7200
    with pytest.raises(KeyError):
        nominal_match_seconds(5, "00:00:00")


def test_visibility_and_value():
    polygon = [0, 0, 20, 0, 20, 20, 0, 20, 0, 0]
    assert point_visible([10, 10], polygon) is True
    assert point_visible([20, 10], polygon) is True
    assert point_visible([21, 10], polygon) is False
    assert point_visible([10, 10], []) is None
    assert territorial_value(0.8, 20) == 16
    assert territorial_value(0.8, -20) == 0


def test_frame_coordinates_can_be_finite_and_outside_pitch():
    assert xy([40, -1.5], bounded=False) == (40, -1.5)
    with pytest.raises(ValueError):
        xy([40, float("inf")], bounded=False)
