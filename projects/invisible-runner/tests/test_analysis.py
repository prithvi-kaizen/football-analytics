from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from invisible_runner.analysis import (RunConfig, choose_teammate, defensive_line, detect_runs,
                                       free_area, receiving_patch)


def test_free_space_exact_grid():
    config = RunConfig()
    cells = np.array([[0, 0], [3, 0], [4, 0]])
    assert free_area(cells, np.array([[0, 0]]), config) == 2
    assert free_area(cells, np.array([[10, 0]]), config) == 3
    assert np.isnan(free_area(cells, np.empty((0, 2)), config))


def test_patch_respects_touchline_and_fixed_geometry():
    cells = receiving_patch(np.array([52., 34.]), 104, 68, RunConfig())
    assert (cells[:, 0] <= 52).all() and (cells[:, 1] <= 34).all()
    assert len(cells) > 0


def test_defensive_line_excludes_keeper_and_flips():
    opp = pd.DataFrame(dict(sx=[1, 2, 3, 4, 5, 6, 8, 9, 50], is_gk=[False]*8+[True]))
    assert defensive_line(opp, 1) == 8
    assert defensive_line(opp, -1) == -2
    assert np.isnan(defensive_line(opp.iloc[:3], 1))


def test_teammate_chosen_without_future_outcome():
    start = pd.DataFrame(dict(player_id=[1, 2, 3, 4], team_id=[10]*4, is_gk=[False]*4,
                              sx=[0., 2., 5., -20.], sy=[0.]*4))
    assert choose_teammate(start, start.iloc[0], 1) == 2


def synthetic_tracking():
    # Synthetic unit fixture. Only the runner needs valid speed for detection.
    rows = []
    for frame in range(50):
        x = max(0, min(frame - 10, 25)) * .6
        for pid, team, px, py in [(101, 10, x, 0), (102, 10, 6., 5.)] + [(200+i, 20, 5.+i*3, 8.) for i in range(9)]:
            rows.append(dict(frame=frame, period=1, player_id=pid, player_name=str(pid), team_id=team,
                             segment=pid, sx=px, sy=py, speed=6. if pid==101 and 11<=frame<=34 else 0.,
                             detected=True, is_gk=False, edge=frame<3 or frame>=47,
                             ball_x=-10., ball_y=-10., phase_team=10, possession_team=10,
                             carrier_id=102, provider_on_ball=False, ball_detected=True))
    return pd.DataFrame(rows)


def test_run_distance_speed_and_no_ball_exclusion(metadata):
    df = synthetic_tracking()
    runs = detect_runs(df, metadata, RunConfig())
    assert len(runs) == 1
    assert runs.iloc[0].distance_m == pytest.approx(13.8)
    assert runs.iloc[0].duration_s == pytest.approx(2.3)
    assert runs.iloc[0].progress_m == pytest.approx(13.8)
    assert runs.iloc[0].free_area_delta_m2 == 0
    assert runs.iloc[0].defender_displacement_m == 0
    df.loc[df.player_id.eq(101), "provider_on_ball"] = True
    assert detect_runs(df, metadata, RunConfig()).empty


@pytest.mark.parametrize("change", ["ball", "possession", "carrier", "boundary", "backward"])
def test_run_exclusions(metadata, change):
    df = synthetic_tracking()
    runner = df.player_id.eq(101)
    if change == "ball":
        df.loc[runner, "ball_x"] = df.loc[runner, "sx"]
        df.loc[runner, "ball_y"] = 0
    elif change == "possession":
        df["phase_team"] = 20
    elif change == "carrier":
        df["carrier_id"] = 101
    elif change == "boundary":
        df.loc[runner & df.frame.eq(10), "edge"] = True
    elif change == "backward":
        df.loc[runner, "sx"] *= -1
    assert detect_runs(df, metadata, RunConfig()).empty


def test_observation_flags_and_defender_motion(metadata):
    df = synthetic_tracking()
    df.loc[df.player_id.eq(101) & df.frame.eq(20), "detected"] = False
    # Every defender translates two metres by the run's endpoint.
    mask = df.team_id.eq(20)
    df.loc[mask, "sy"] += (df.loc[mask, "frame"] - 11).clip(0, 23) / 23 * 2
    run = detect_runs(df, metadata, RunConfig()).iloc[0]
    assert run.runner_detected_fraction == pytest.approx(23/24)
    assert run.defender_displacement_m == pytest.approx(2)


def test_missing_defenders_produce_missing_metrics(metadata):
    df = synthetic_tracking()
    df = df[~(df.player_id.eq(200) & df.frame.eq(34))]
    run = detect_runs(df, metadata, RunConfig()).iloc[0]
    assert not run.context_valid
    assert np.isnan(run.free_area_delta_m2)


def test_threshold_monotonicity_on_fixed_fixture(metadata):
    df = synthetic_tracking()
    assert len(detect_runs(df, metadata, RunConfig())) == 1
    assert detect_runs(df, metadata, replace(RunConfig(), min_distance_m=20)).empty
    assert detect_runs(df, metadata, replace(RunConfig(), speed_mps=7)).empty


def test_config_rejects_bad_values():
    with pytest.raises(ValueError):
        RunConfig(speed_mps=-1)
    with pytest.raises(ValueError):
        RunConfig(smoothing_window=4)


def test_behind_line_crossing_and_mirrored_pitch(metadata):
    df = synthetic_tracking()
    opponents = df.team_id.eq(20)
    df.loc[opponents, "sx"] = df.loc[opponents, "player_id"] - 197
    original = detect_runs(df, metadata, RunConfig()).iloc[0]
    assert original.behind_line
    flipped = df.copy()
    flipped["sx"] *= -1
    flipped["ball_x"] *= -1
    mirrored_metadata = dict(metadata, home_team_side=["right_to_left", "left_to_right"])
    mirrored = detect_runs(flipped, mirrored_metadata, RunConfig()).iloc[0]
    assert mirrored.behind_line
    for field in ["distance_m", "progress_m", "runner_separation_delta_m", "free_area_delta_m2"]:
        assert mirrored[field] == pytest.approx(original[field])


def test_context_requires_complete_published_opponent_roster(metadata):
    df = synthetic_tracking()
    players = metadata["players"] + [dict(id=999, team_id=20, playing_time={"by_period": [
        dict(name="period_1", start_frame=0, end_frame=50)]})]
    incomplete_metadata = dict(metadata, players=players)
    run = detect_runs(df, incomplete_metadata, RunConfig()).iloc[0]
    assert not run.context_valid
    assert np.isnan(run.free_area_delta_m2)
    assert np.isnan(run.behind_line)
