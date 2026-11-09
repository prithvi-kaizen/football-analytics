import unittest
import json
from pathlib import Path
import numpy as np
from one_step_behind.detector import gaps, runs, line_geometry, step_windows, detect_segment, eligible_segments
from one_step_behind.data import attack_sign
CFG = json.loads((Path(__file__).resolve().parents[1]/'configs/pilot.json').read_text())

class Geometry(unittest.TestCase):
    def test_depth_uses_other_players(self):
        np.testing.assert_allclose(gaps(np.array([[-4., 0, 0, 0]])), [[4,0,0,0]])
    def test_direction_changes_at_half(self):
        m = {'home_team':{'id':1},'away_team':{'id':2},'home_team_side':['right_to_left','left_to_right']}
        self.assertEqual(attack_sign(m,1,1),-1)
        self.assertEqual(attack_sign(m,1,2),1)
        self.assertEqual(attack_sign(m,2,1),1)
        with self.assertRaises(ValueError): attack_sign(m,2,3)
    def test_flexible_line_and_midfield_cover_exclusion(self):
        for n in [3,4,5]:
            roles=np.array(['Central Defender']*2+['Full Back']*(n-2)+['Midfield']*(10-n))
            depth=np.r_[np.zeros(n), np.ones(10-n)*10]
            self.assertEqual(len(line_geometry(depth,np.arange(10)*7,roles,CFG)),n)
            depth[-1]=-2
            self.assertIsNone(line_geometry(depth,np.arange(10)*7,roles,CFG))
    def test_runs_do_not_bridge_missing(self):
        self.assertEqual(runs([1,1,0,1,1]),[(0,2),(3,5)])

class Episodes(unittest.TestCase):
    def fixture(self, recover=True):
        x=np.zeros((70,4))
        x[:,1:]=np.minimum(np.arange(70)[:,None]*.4, 6)
        if recover: x[20:,0]=np.minimum(np.arange(50)*.6,6)
        return dict(x=x,detected=np.ones_like(x,bool),start=100,members=(0,1,2,3),team=1,period=1,phase=0)
    def test_stationary_gap_is_not_a_step(self):
        x=np.tile([-5.,0,0,0],(60,1))
        self.assertEqual(step_windows(x,CFG),[])
    def test_collective_step_with_lag_and_recovery(self):
        e=detect_segment(self.fixture(),CFG)
        self.assertEqual(len(e),1)
        self.assertTrue(e[0]['candidate'])
        self.assertFalse(e[0]['recovery_censored'])
        self.assertEqual(e[0]['defender_index'],0)
        self.assertGreater(e[0]['recovery_s'],0)
    def test_truncated_recovery_is_censored(self):
        s=self.fixture(False)
        s['x']=s['x'][:20]; s['detected']=s['detected'][:20]
        e=detect_segment(s,CFG)[0]
        self.assertTrue(e['candidate'])
        self.assertIsNone(e['recovery_s'])
        self.assertTrue(e['gap_censored'])
    def test_translation_invariance(self):
        s=self.fixture(); e=detect_segment(s,CFG)
        s['x']=s['x']+37
        self.assertEqual(e,detect_segment(s,CFG))
    def test_short_fluctuation_rejected(self):
        s=self.fixture(); s['x'][11:,0]=s['x'][11:,1]
        self.assertFalse(any(e['candidate'] for e in detect_segment(s,CFG)))
    def test_no_detection_across_split(self):
        s=self.fixture(); s['x']=s['x'][11:]; s['detected']=s['detected'][11:]
        self.assertEqual(detect_segment(s,CFG),[])

class Eligibility(unittest.TestCase):
    def fixture(self):
        n=35
        roles=['Central Defender']*2+['Full Back']*2+['Midfield']*6
        players=[dict(id=i,player_role={'position_group':roles[i]},playing_time={'by_period':[dict(start_frame=0,end_frame=n-1)]}) for i in range(10)]
        meta=dict(players=players,home_team={'id':1},away_team={'id':2},home_team_side=['left_to_right','right_to_left'])
        xy=np.zeros((n,10,2));xy[:,:4,1]=[-15,-5,5,15];xy[:,4:,0]=15
        return dict(metadata=meta,ids=np.arange(10),teams=np.ones(10),gk=np.zeros(10,bool),xy=xy,
                    clean=np.ones((n,10),bool),detected=np.ones((n,10),bool),period=np.ones(n),phase=np.zeros(n),
                    phase_team=np.ones(n)*2,possession=np.ones(n)*2,ball=np.ones((n,2)),
                    phase_rows=[{'team_in_possession_phase_type':'create'}])
    def test_missing_position_resets_geometry(self):
        d=self.fixture();d['clean'][10,0]=False;d['xy'][10,0]=np.nan
        s,_=eligible_segments(d,CFG)
        self.assertEqual([(x['start'],x['stop']) for x in s],[(0,10),(11,35)])
    def test_extrapolation_sensitivity_has_own_population(self):
        d=self.fixture();d['detected'][10,9]=False
        primary,_=eligible_segments(d,CFG); observed,_=eligible_segments(d,CFG,True)
        self.assertEqual(sum(len(s['x']) for s in primary),35)
        self.assertEqual(sum(len(s['x']) for s in observed),34)
    def test_possession_conflict_and_phase_change_reset(self):
        d=self.fixture();d['possession'][10]=1
        d['phase'][20:]=1;d['phase_rows'].append({'team_in_possession_phase_type':'create'})
        s,_=eligible_segments(d,CFG)
        self.assertEqual([(x['start'],x['stop']) for x in s],[(0,10),(11,20),(20,35)])

if __name__=='__main__': unittest.main()
