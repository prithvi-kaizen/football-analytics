import copy
import math

import pandas as pd
import pytest

from tacticai_lite.analysis import (canonical, clip_box, corner_sequence, delivery, extract_match,
    inside_polygon, is_corner, polygon_area, spatial_features, summary, timestamp_seconds, xy)
from tacticai_lite.data import DataError


def event(i=1, timestamp='00:00:00.000', typ='Pass', **kwargs):
    return {'id': str(i), 'index': i, 'timestamp': timestamp, 'period': 1,
            'type': {'name': typ}, 'team': {'id': 1, 'name': 'A'}, 'possession': 1,
            'possession_team': {'id': 1}, **kwargs}


def corner(**kwargs):
    return event(location=[120,0], **{'pass': {'type': {'name': 'Corner'}}}, **kwargs)


@pytest.mark.parametrize('value,expected', [('00:00:00.000',0),('00:47:12.325',2832.325),('01:01:00',3660)])
def test_period_clock(value, expected):
    assert timestamp_seconds(value) == pytest.approx(expected)


@pytest.mark.parametrize('value', [None, '45:60:00', '00:00:61', '2:00', '', 'nan'])
def test_bad_clock(value):
    with pytest.raises(DataError): timestamp_seconds(value)


@pytest.mark.parametrize('value', [None, [], [0], [float('nan'),2], [-1,2], [121,40], [1,81], ['1',2], [True,2]])
def test_invalid_coordinates(value):
    assert xy(value) is None


def test_coordinate_reflection_and_bounds():
    assert xy([120,80,1]) == (120.,80.)
    assert canonical((108,62),(120,80)) == (108,18)
    assert canonical(canonical((108,62),(120,80)),(120,80)) == (108,62)
    assert canonical((108,62),(120,0)) == (108,62)


def test_delivery_uses_recorded_technique_and_explicit_short_rule():
    e=corner();e['pass'].update(length=40,technique={'name':'Inswinging'})
    assert delivery(e)=='Inswinging'
    e['pass']['length']=15
    assert delivery(e)=='Short'
    e['pass'].pop('length');e['pass']['end_location']=[110,0]
    assert delivery(e)=='Short'
    e['pass'].pop('end_location');e['pass'].pop('technique')
    assert delivery(e)=='Other / unknown'
    assert not is_corner(event())
    assert not is_corner(corner(period=5))


def test_horizon_inclusive_and_one_millisecond_late():
    assert corner_sequence([corner(),event(2,'00:00:15.000','Shot')],0)['shot_created'] is True
    assert corner_sequence([corner(),event(2,'00:00:15.001','Shot')],0)['shot_created'] is False


def test_opponent_shot_period_end_and_possession_boundary():
    assert corner_sequence([corner(),event(2,'00:00:02','Shot',team={'id':2})],0)['shot_created'] is None
    assert corner_sequence([corner(),event(2,'00:00:02','Shot',possession=2)],0)['shot_created'] is False
    assert corner_sequence([corner(),event(2,'00:00:02','Shot',period=2)],0)['shot_created'] is False
    assert corner_sequence([corner(),event(2,'00:00:02','Half End')],0)['shot_created'] is False


def test_stoppage_restart_and_advantage():
    shot=event(3,'00:00:04','Shot')
    assert corner_sequence([corner(),event(2,'00:00:02','Foul Committed'),shot],0)['shots']==0
    advantage=event(2,'00:00:02','Foul Committed',foul_committed={'advantage':True})
    assert corner_sequence([corner(),advantage,shot],0)['shots']==1
    new=event(2,'00:00:02',**{'pass':{'type':{'name':'Corner'}}})
    assert corner_sequence([corner(),new,shot],0)['shots']==0
    assert corner_sequence([corner(),event(2,'00:00:02',out=True),shot],0)['shots']==0


def test_censored_outcome_and_xg_missing_not_zero():
    result=corner_sequence([corner()],0)
    assert result['shot_created'] is None
    shot=event(2,'00:00:01','Shot')
    assert corner_sequence([corner(),shot],0)['xg_sum'] is None
    shot['shot']={'statsbomb_xg':0.2}
    result=corner_sequence([corner(),shot,event(3,'00:00:02','Shot',shot={'statsbomb_xg':0.3})],0)
    assert result['xg_sum']==pytest.approx(0.5)
    assert result['shots']==2


def test_direct_corner_shot_and_negative_time():
    direct=event(1,typ='Shot',shot={'type':{'name':'Corner'}})
    assert is_corner(direct)
    assert delivery(direct)=='Direct shot'
    assert corner_sequence([direct],0)['shot_created'] is True
    assert corner_sequence([corner(timestamp='00:01:00'),event(2,'00:00:59','Shot')],0)['shots']==0


def test_polygon_clipping_and_boundary_inclusion():
    poly=[(0,0),(120,0),(120,80),(0,80)]
    assert polygon_area(clip_box(poly))==792
    assert polygon_area(clip_box([(0,0),(1,0),(1,1),(0,1)]))==0
    assert inside_polygon((102,18),clip_box(poly))
    assert not inside_polygon((90,40),clip_box(poly))


def test_density_respects_visibility_and_missing_frame():
    frame={'visible_area':[102,18,120,18,120,40,102,40], 'freeze_frame':[
        {'location':[110,20],'teammate':True}, {'location':[111,20],'teammate':False},
        {'location':[115,50],'teammate':False}, {'location':[120,0],'teammate':True,'actor':True}]}
    f=spatial_features(frame,(120,0))
    assert f['box_visible_fraction']==0.5
    assert f['defenders_box']==2
    assert f['defenders_per_100_visible_units']==pytest.approx(100/396)
    assert f['attackers_box']==1
    assert f['nearest_defender_mean']==1
    missing=spatial_features(None,(120,0))
    assert missing['defenders_box'] is None
    assert not missing['has_360']
    frame['visible_area']=[]
    assert spatial_features(frame,(120,0))['defenders_per_100_visible_units'] is None
    reflected=copy.deepcopy(frame)
    for p in reflected['freeze_frame']: p['location'][1]=80-p['location'][1]
    assert spatial_features(frame,(120,0))==spatial_features(reflected,(120,80))


def test_summary_denominator_and_wilson_bounds():
    data=pd.DataFrame({'tournament':['T']*4,'delivery':['Short']*4,'shot_created':[True,False,False,None]})
    s=summary(data).iloc[0]
    assert s.corners==3 and s.shots_created==1
    assert s.rate==pytest.approx(1/3)
    assert s.low==pytest.approx(0.0614919447)
    assert s.high==pytest.approx(0.7923403992)


def test_duplicate_event_rejected():
    with pytest.raises(DataError): extract_match({},[corner(),corner()],[])
