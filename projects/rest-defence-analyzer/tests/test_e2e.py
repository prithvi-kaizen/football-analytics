import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from rest_defence.data import acquire, metadata, parse_events, parse_tracking
from rest_defence.pipeline import analyze, load_result, run


@pytest.mark.real
def test_offline_real_data_end_to_end_and_cache(tmp_path):
    paths=acquire(bundled=True,cache=tmp_path/"raw")
    first,audit=run(bundled=True,paths=paths,output=tmp_path/"result",clean_cache=tmp_path/"clean")
    assert len(first)==17 and audit["analysis"]==dict(candidates=17,accepted=17,rejected={})
    assert first.censored.sum()==1
    assert first.snapshot_frame.lt(first.frame).all()
    assert first.snapshot_age_s.between(.04,.2).all()
    assert first.vulnerability_score.between(0,100).all()
    assert first.progressed_10m.sum()==5
    assert not first.shot.any()
    assert first.loc[first.frame.eq(11528),"progress_m"].iloc[0]==pytest.approx(28.37)
    timeline=pd.read_parquet(tmp_path/"result/timeline.parquet")
    for row in first.itertuples():
        section=timeline[timeline.transition_id.eq(row.transition_id)]
        anchor=section[section.frame.eq(row.frame)]
        assert len(anchor)==1 and anchor.iloc[0].relative_s==0
        observed=section[section.relative_s.ge(0)]
        assert float((anchor.iloc[0].x-observed.x).max())==pytest.approx(row.progress_m)
    second,_=run(bundled=True,paths=paths,output=tmp_path/"result2",clean_cache=tmp_path/"clean")
    pd.testing.assert_frame_equal(first,second)
    loaded,_,_=load_result(tmp_path/"result")
    assert len(loaded)==17
    with (tmp_path/"result/transitions.csv").open("a") as f:
        f.write("\n")
    with pytest.raises(ValueError,match="integrity"):
        load_result(tmp_path/"result")


@pytest.mark.real
def test_score_cannot_see_future_events_or_player_positions(tmp_path):
    paths=acquire(bundled=True,cache=tmp_path)
    meta=metadata(paths["meta"])
    events,halves=parse_events(paths["events"],meta)
    p,b,_=parse_tracking(paths["tracking"],meta)
    original,*_=analyze(p,b,events,meta,halves)
    first=original.iloc[0]
    p.loc[p.frame>=first.frame,["x","y"]]*=-1
    events.loc[events.time>=first.time,"xg"]=10000.
    changed,*_=analyze(p,b,events,meta,halves)
    for key in ["behind_ball","compactness_rms_m","central_exposed_fraction","open_lanes","vulnerability_score"]:
        assert original.iloc[0][key]==pytest.approx(changed.iloc[0][key])


@pytest.mark.real
def test_packaged_full_match_snapshot_matches_smoke_scope():
    # Release evidence is checked offline; fresh full ingestion has its own audit.
    base=Path(__file__).resolve().parents[1]/"outputs"
    if not (base/"J03WPY/audit.json").exists():
        pytest.skip("Full-match release not present")
    full,_,audit=load_result(base/"J03WPY")
    smoke,_,_=load_result(base/"sample")
    joined=full.merge(smoke,on="transition_id",suffixes=("_full","_sample"))
    assert len(joined)==17
    for key in ["behind_ball","compactness_rms_m","central_exposed_fraction","open_lanes","vulnerability_score"]:
        np.testing.assert_allclose(joined[key+"_full"],joined[key+"_sample"])
    assert audit["parser"]["ball_rows"]==146211
    assert audit["analysis"]["accepted"]==293
