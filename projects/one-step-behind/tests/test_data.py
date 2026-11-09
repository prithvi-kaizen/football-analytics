import csv
import json
import tempfile
import unittest
from pathlib import Path
from one_step_behind.data import load_match

class SchemaValidation(unittest.TestCase):
    def write(self, root, records):
        meta=dict(id=7,pitch_length=105,pitch_width=68,home_team={'id':1},away_team={'id':2},home_team_side=['left_to_right','right_to_left'],
                  players=[{'id':10,'team_id':1,'player_role':{'acronym':'LCB'}}],match_periods=[{'period':1,'start_frame':0,'end_frame':3}])
        (root/'7_match.json').write_text(json.dumps(meta))
        (root/'7_tracking_extrapolated.jsonl').write_text('\n'.join(json.dumps(r) for r in records)+'\n')
        (root/'7_phases_of_play.csv').write_text('match_id,frame_start,frame_end,period,team_in_possession_id,attacking_side\n7,0,4,1,2,right_to_left\n')
    def records(self):
        return [dict(frame=i,period=1,player_data=[dict(player_id=10,x=0,y=0,is_detected=False)],possession={'group':'away team'},ball_data={'x':1,'y':1}) for i in range(4)]
    def test_missing_rows_are_unknown_not_interpolated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);r=self.records();r[1]['player_data']=[];self.write(root,r)
            d=load_match(root,7)
            self.assertFalse(d['clean'][1,0]);self.assertFalse(d['detected'].any())
            self.assertTrue(d['clean'][0,0]);self.assertTrue(d['clean'][2,0])
    def test_duplicate_frames_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);r=self.records();r[2]['frame']=1;self.write(root,r)
            with self.assertRaisesRegex(ValueError,'non-increasing'):load_match(root,7)
    def test_unknown_identity_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);r=self.records();r[1]['player_data'][0]['player_id']=99;self.write(root,r)
            with self.assertRaisesRegex(ValueError,'Unknown player'):load_match(root,7)
    def test_out_of_bounds_not_used(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);r=self.records();r[1]['player_data'][0]['x']=80;self.write(root,r)
            d=load_match(root,7);self.assertFalse(d['clean'][1,0]);self.assertEqual(d['audit']['out_of_bounds_rows'],1)
