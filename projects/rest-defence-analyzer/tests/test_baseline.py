import numpy as np
import pandas as pd
import pytest

from rest_defence.baseline import align_events, detect_turnovers, preloss_snapshot, transition_outcome


def test_stable_live_turnover_first_new_frame(ball_factory):
    b = ball_factory([1]*20+[2]*20)
    t = detect_turnovers(b)
    assert len(t) == 1
    assert t.iloc[0].frame == 10020
    assert t.iloc[0].time == .8


@pytest.mark.parametrize("case", ["short", "dead", "unknown", "gap", "period"])
def test_no_turnover_across_breaks(ball_factory, case):
    b = ball_factory([1]*20+[2]*(5 if case == "short" else 20))
    if case == "dead":
        b.loc[19, "live"] = 0
    if case == "unknown":
        b.loc[19, "possession"] = 0
    if case == "gap":
        b.loc[20:, "frame"] += 1
    if case == "period":
        b.loc[20:, "period"] = "secondHalf"
    assert detect_turnovers(b).empty


def test_outcome_stops_at_regain_and_excludes_later_shot(ball_factory, empty_events):
    b = ball_factory([2]*50+[1]*100)
    e = pd.DataFrame([dict(period="firstHalf", kind="ShotAtGoal", team="away", time=3., aligned_time=3., alignment="utc_approximate", xg=.2)])
    result = transition_outcome(b,e,"firstHalf",10000,2,"away",1)
    assert result["stop_reason"] == "regain"
    assert not result["censored"] and not result["shot"]
    assert result["observed_seconds"] == 49/25
    assert result["progress_m"] == pytest.approx(4.9)


def test_outcome_censors_source_end(ball_factory, empty_events):
    result = transition_outcome(ball_factory([2]*50),empty_events,"firstHalf",10000,2,"away",1)
    assert result["censored"] and result["stop_reason"] == "source_end"


def test_outcome_horizon_and_direction(ball_factory, empty_events):
    b = ball_factory([2]*400)
    r = transition_outcome(b,empty_events,"firstHalf",10000,2,"away",1)
    assert r["observed_seconds"] == 10 and r["progress_m"] == 25
    assert not r["censored"] and r["progressed_10m"]
    b.x *= -1
    other = transition_outcome(b,empty_events,"firstHalf",10000,2,"away",-1)
    assert other["progress_m"] == r["progress_m"]


@pytest.mark.parametrize("column,value,reason", [("live",0,"dead_ball"),("valid",False,"invalid_ball"),("possession",0,"unknown_control")])
def test_outcome_breaks(ball_factory, empty_events, column, value, reason):
    b = ball_factory([2]*400)
    b.loc[30,column] = value
    r = transition_outcome(b,empty_events,"firstHalf",10000,2,"away",1)
    assert r["stop_reason"] == reason and r["end_frame"] == 10029


def test_corrected_event_frame_preferred(ball_factory):
    b = ball_factory([1]*20)
    e = pd.DataFrame([dict(period="firstHalf",time=3.,corrected_frame=10005),dict(period="firstHalf",time=4.,corrected_frame=np.nan)])
    result = align_events(e,b)
    assert result.iloc[0].aligned_time == .2
    assert result.iloc[0].alignment == "corrected_frame"
    assert result.iloc[1].aligned_time == 4.


def test_snapshot_strictly_precedes_turnover(ball_factory):
    b = ball_factory([1]*20+[2]*20)
    rows = [dict(period="firstHalf",frame=n,time=(n-10000)/25,player=f"{team}{i}",team=team,x=float(i),y=0.,is_gk=i==0)
            for n in [10015,10020,10025] for team in ["A","B"] for i in range(11)]
    p = pd.DataFrame(rows)
    snap, anchor = preloss_snapshot(p,b,"firstHalf",10020)
    assert snap.frame.eq(10015).all() and anchor.frame == 10015
    with pytest.raises(ValueError,match="Incomplete"):
        preloss_snapshot(p.drop(index=0),b,"firstHalf",10020)


def test_no_snapshot_lookahead(ball_factory):
    b = ball_factory([1]*20+[2]*20)
    p = pd.DataFrame([dict(period="firstHalf",frame=10020)])
    with pytest.raises(ValueError,match="No pre-loss"):
        preloss_snapshot(p,b,"firstHalf",10020)


def test_shot_requires_bounded_window_winning_team_and_half(ball_factory):
    b=ball_factory([2]*300)
    events=pd.DataFrame([dict(period=p,kind="ShotAtGoal",team=t,time=1.,aligned_time=1.,alignment="corrected_frame",xg=xg)
                         for p,t,xg in [("firstHalf","away",.2),("firstHalf","home",.8),("secondHalf","away",.9)]])
    r=transition_outcome(b,events,"firstHalf",10000,2,"away",1)
    assert r["shot"] and r["shot_xg"]==.2 and r["approx_shots"]==0


def test_final_third_uses_actual_pitch_length(ball_factory,empty_events):
    b=ball_factory([2]*300)
    b.x=-b.index/10
    r=transition_outcome(b,empty_events,"firstHalf",10000,2,"away",1,length=120)
    assert r["entered_final_third"]
