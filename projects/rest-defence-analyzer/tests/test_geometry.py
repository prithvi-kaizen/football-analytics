import numpy as np
import pytest

from rest_defence.geometry import central_grid, clear_lane, rest_geometry, vulnerability_score


def test_segment_corridor():
    assert not clear_lane([0,0],[-10,0],[[-5,1]])
    assert clear_lane([0,0],[-10,0],[[-5,3]])
    assert clear_lane([0,0],[-10,0],[[-15,0],[1,0]])
    assert not clear_lane([0,0],[0,0],[])
    assert clear_lane([0,0],[-10,0],[])


def test_known_compactness_and_numerical_coverage():
    m = rest_geometry([[-10,-5],[-10,5],[10,0]],[[-20,0],[5,0]],[0,0])
    assert m["behind_ball"] == 2 and m["counter_options"] == 1 and m["coverage_margin"] == 1
    assert m["compactness_rms_m"] == 5
    assert m["rest_width_m"] == 10 and m["rest_depth_m"] == 0
    assert m["open_lanes"] == 1
    assert m["nearest_option_mean_m"] == pytest.approx(np.sqrt(125))


def test_hull_area_and_collinear():
    m = rest_geometry([[-10,0],[-20,0],[-10,10]],[],[0,0])
    assert m["hull_area_m2"] == pytest.approx(50.)
    m = rest_geometry([[-10,0],[-20,0],[-30,0]],[],[0,0])
    assert m["hull_area_m2"] == 0


def test_no_defenders_and_no_options_are_explicit():
    m = rest_geometry([[5,0]],[],[0,0])
    assert m["behind_ball"] == 0 and m["central_exposed_fraction"] == 1.
    assert np.isnan(m["compactness_rms_m"]) and np.isnan(m["nearest_option_mean_m"])
    assert m["open_lane_fraction"] == 0 and 0 <= vulnerability_score(m) <= 100


def test_grid_cell_centres_and_pitch_clipping():
    g = central_grid([0,20])
    assert len(g) == 150 and g[:,0].max() == -1 and abs(g[:,1]).max() == 9
    assert (central_grid([-50,0])[:,0] > -52.5).all()
    assert len(central_grid([-52.5,0])) == 0


def test_score_fixed_weights():
    m = dict(behind_ball=2,compactness_rms_m=10.,central_exposed_fraction=.5,open_lane_fraction=.5)
    assert vulnerability_score(m) == 50.
    m["behind_ball"] = 4
    assert vulnerability_score(m) == 37.5


def test_lateral_mirror_invariant():
    d = np.array([[-10,-4],[-30,2],[-20,12]])
    o = np.array([[-15,-10],[-25,0]])
    a = rest_geometry(d,o,[0,4])
    b = rest_geometry(d*[1,-1],o*[1,-1],[0,-4])
    for k in a:
        assert a[k] == pytest.approx(b[k],nan_ok=True)
