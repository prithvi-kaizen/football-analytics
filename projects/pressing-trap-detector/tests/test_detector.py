import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('detector',Path(__file__).parents[1]/'scripts/build_dataset.py')
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
MATCH={'match_id':1,'match_date':'2024-06-15','home_team':{'home_team_name':'Spain'},'away_team':{'away_team_name':'Germany'},'competition_stage':{'name':'Group Stage'}}

def event(i,t,typ,team='Germany',pos=1,period=1,**extra):
    return {'id':str(i),'index':i,'timestamp':f'00:00:{t:06.3f}','minute':0,'second':int(t),'period':period,
      'type':{'name':typ},'team':{'name':team},'possession_team':{'name':'Germany' if pos==1 else 'Spain'},
      'possession':pos,'location':[90,10] if team=='Spain' else [30,70],**extra}

class DetectorTest(unittest.TestCase):
    def test_flip_both_axes(self):
        self.assertEqual(d.point(event(1,0,'Pass'),'Spain'),[90,10])
    def test_success_and_candidate(self):
        events=[event(1,1,'Pass',location=[25,50],duration=1,**{'pass':{'end_location':[30,70]}}),
                event(2,3,'Pressure','Spain'),event(3,7,'Ball Recovery','Spain',2)]
        r=d.detect(events,MATCH)[0]
        self.assertEqual(r['recovery_seconds'],4)
        self.assertTrue(r['wide_candidate']);self.assertEqual(r['pass_direction'],'Lateral')
    def test_period_boundary(self):
        r=d.detect([event(1,3,'Pressure','Spain'),event(2,4,'Ball Recovery','Spain',2,2)],MATCH)[0]
        self.assertIsNone(r['recovery_id'])
    def test_dead_ball(self):
        r=d.detect([event(1,3,'Pressure','Spain'),event(2,4,'Foul Won'),event(3,5,'Ball Recovery','Spain',2)],MATCH)[0]
        self.assertIsNone(r['recovery_id'])
    def test_failed_recovery_and_lost_interception(self):
        events=[event(1,3,'Pressure','Spain'),event(2,4,'Ball Recovery','Spain',ball_recovery={'recovery_failure':True}),
          event(3,5,'Interception','Spain',interception={'outcome':{'name':'Lost In Play'}})]
        self.assertIsNone(d.detect(events,MATCH)[0]['recovery_id'])
    def test_dedup_identity(self):
        events=[event(1,1,'Pressure','Spain'),event(2,2,'Pressure','Spain'),event(3,4,'Ball Recovery','Spain',2)]
        a,b=d.detect(events,MATCH)
        self.assertEqual(a['recovery_id'],b['recovery_id']);self.assertTrue(a['episode_first']);self.assertFalse(b['episode_first'])
    def test_exact_window_limit(self):
        for t,success in [(18,True),(18.001,False)]:
            r=d.detect([event(1,3,'Pressure','Spain'),event(2,t,'Ball Recovery','Spain',2)],MATCH)[0]
            self.assertEqual(r['recovery_id'] is not None,success)
    def test_opposition_pass_direction(self):
        p=event(1,1,'Pass',location=[50,40],duration=1,**{'pass':{'end_location':[30,70]}})
        r=d.detect([p,event(2,3,'Pressure','Spain')],MATCH)[0]
        self.assertEqual(r['pass_direction'],'Backward')
    def test_prior_possession_excluded(self):
        p=event(1,1,'Pass',pos=3,duration=1,**{'pass':{'end_location':[30,70]}})
        r=d.detect([p,event(2,3,'Pressure','Spain')],MATCH)[0]
        self.assertEqual(r['passes_before'],0)
    def test_threat_after_interception_changes_possession_id(self):
        events=[event(1,3,'Pressure','Spain'),event(2,4,'Interception','Spain',interception={'outcome':{'name':'Won'}}),
                event(3,5,'Carry','Spain',2,carry={'end_location':[110,10]})]
        values=[i/100 for i in range(96)]
        r=d.detect(events,MATCH,values)[0]
        self.assertGreater(r['subsequent_xt'],0)

    def test_no_replay_tracking_claim(self):
        events=[event(1,3,'Pressure','Spain'),event(2,6,'Ball Recovery','Spain',2)]
        import json
        replay=json.loads(d.detect(events,MATCH)[0]['replay_json'])
        self.assertEqual([x['t'] for x in replay],[0,3])

if __name__=='__main__':unittest.main()
