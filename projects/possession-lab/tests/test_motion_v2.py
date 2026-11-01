"""Motion invariants; no historical generator or benchmark expectation changes."""
import json
from pathlib import Path
import tarfile
import numpy as np
import pytest
from possession_lab.motion_v2 import generate, observe, FPS
from possession_lab.explorer_v2 import scenario, observability, public_demo


@pytest.mark.parametrize('seed',[1,42,101,301,99999])
@pytest.mark.parametrize('mechanism',['ordinary','stationary_live','contested'])
def test_latent_motion_has_bounded_speed_and_acceleration(seed,mechanism):
    match=generate(seed,mechanism)
    for values,speed_cap,acc_cap in [(match.tracking.home,7,3),(match.tracking.away,7,3),(match.tracking.ball,35,35)]:
        assert np.linalg.norm(np.diff(values,axis=0)*FPS,axis=-1).max()<=speed_cap+1e-6
        assert np.linalg.norm(np.diff(values,n=2,axis=0)*FPS**2,axis=-1).max()<=acc_cap+1e-6
        assert np.isfinite(values).all()
    assert match.diagnostics['max_player_step_m']<.29


def test_players_move_individually_with_goalkeepers_near_their_goals():
    batch=generate(101).tracking
    assert np.median(np.std(np.diff(batch.home,axis=0)[:,1:]*FPS,axis=1))>.1
    assert batch.home[:,0,0].max()<14 and batch.away[:,0,0].min()>91
    for team in (batch.home,batch.away):
        assert (team>=0).all() and (team<=[105,68]).all()


def test_passes_reach_actual_receivers_without_relocating_them():
    match=generate(101)
    assert any(event['type']=='interception' for event in match.actions)
    assert len({event['to_slot'] for event in match.actions})>3
    for event in match.actions:
        team=match.tracking.home if event['to_team']=='H' else match.tracking.away
        assert np.linalg.norm(match.tracking.ball[event['catch']]-team[event['catch'],event['to_slot']])<.8
        assert match.truth[event['catch']]==event['to_team']


def test_live_pause_keeps_other_players_walking():
    match=generate(101,'stationary_live')
    assert set(match.truth[350:450])=={'H'}
    assert np.max(abs(np.diff(match.tracking.ball[351:450],axis=0)))<1e-10
    movement=np.linalg.norm(match.tracking.home[449]-match.tracking.home[351],axis=1)
    assert (movement>.15).sum()>=8 and np.median(movement)>.5


def test_stoppages_do_not_freeze_the_teams():
    match=generate(101)
    assert set(match.truth[1050:1200])=={'D'}
    movement=np.linalg.norm(match.tracking.home[1199]-match.tracking.home[1050],axis=1)
    assert (movement>1).sum()>=8


def test_observation_corruption_preserves_latent_paths_and_is_repeatable():
    match=generate(101);before=match.tracking.home.copy()
    a=observe(match,noise=0,loss=0,gap_duration=0)
    kwargs=dict(seed=101,noise=.2,loss=.3,gap_start=12,gap_duration=6,mechanism='identity_switches')
    b=observe(match,**kwargs)
    np.testing.assert_array_equal(match.tracking.home,before)
    assert np.isnan(b.ball[300:450]).all() and not np.isnan(a.ball).any()
    np.testing.assert_array_equal(b.ball,observe(match,**kwargs).ball)


@pytest.mark.parametrize('evidence',['none','null','independent'])
def test_moving_twins_have_identical_observations_and_honest_null_controls(evidence):
    data=observability({'evidence':evidence});a,b=data['worlds'];lo,hi=a['target']
    assert a['tracking']==b['tracking']
    assert set(a['truth'][lo:hi])=={'H'} and set(b['truth'][lo:hi])=={'D'}
    coords=np.asarray(a['tracking']['home'],float)
    assert np.max(np.linalg.norm(coords[hi-1]-coords[lo],axis=1))>3
    if evidence!='independent':
        assert a['tags']==b['tags']
        assert all(row['balanced_target_accuracy']<=.5 for row in data['summary'])


def test_public_zero_intervention_preserves_original_predictions():
    root=Path(__file__).resolve().parents[1]
    with tarfile.open(root/'web/release.tar.gz') as archive:
        payload=json.load(archive.extractfile('public-inputs/sample1.json'))
        original=json.load(archive.extractfile('data/public1.json'))
    altered=public_demo({'source':'public1','noise':0,'loss':0,'gap_duration':0},payload)
    assert altered['truth'] is None and all(m['metrics'] is None for m in altered['models'])
    assert [m['labels'] for m in altered['models']]==[m['labels'] for m in original['models']]
    lost=public_demo({'source':'public1','noise':0,'loss':0,'gap_start':12,'gap_duration':6},payload)
    assert lost['tracking']['home']==original['tracking']['home']
    assert lost['tracking']['ball'][300:450]==[[None,None]]*150
    assert all(m['metrics'] is None for m in lost['models'])


@pytest.mark.parametrize('parameters',[{'seed':True},{'noise':float('nan')},{'loss':2},{'source':'/private'},{'path':'anything'}])
def test_new_interface_rejects_path_or_unbounded_requests(parameters):
    with pytest.raises(ValueError):scenario(parameters)
