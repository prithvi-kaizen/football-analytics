import copy
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
import pandas as pd
from lane_obstruction.data import read_tracking, snapshot
from lane_obstruction.evaluation import bootstrap

CFG = json.loads((Path(__file__).resolve().parents[1]/'configs/pilot.json').read_text())


def fixture():
    meta = dict(home_team={'id': 1}, away_team={'id': 2}, home_team_side=['left_to_right', 'right_to_left'], pitch_length=105, pitch_width=68,
                players=[dict(id=i, team_id=1 if i < 12 else 2, player_role={'acronym': 'GK' if i in [11, 22] else 'CM'}) for i in range(1, 23)])
    ps = [dict(player_id=i, x=0 if i == 1 else (i-1)*2 if i < 12 else 35+(i-12), y=0 if i == 1 else i % 3*4, is_detected=True) for i in range(1, 23)]
    records = {f:dict(frame=f, period=1, player_data=copy.deepcopy(ps), ball_data=dict(x=0,y=0,z=0,is_detected=True), possession={'player_id':1,'group':'home team'}) for f in range(5, 11)}
    phases = pd.DataFrame([dict(period=1,frame_start=0,frame_end=11,team_in_possession_id=1,attacking_side='left_to_right')])
    return meta, records, phases


class DataTests(unittest.TestCase):
    def test_future_tracking_does_not_change_snapshot(self):
        m, records, p = fixture()
        before, why = snapshot(records, m, p, 10, 1, 1, CFG)
        self.assertIsNone(why)
        records[11] = {'arbitrary_future_data': True}
        after, _ = snapshot(records, m, p, 10, 1, 1, CFG)
        np.testing.assert_array_equal(before.xy, after.xy)
        np.testing.assert_array_equal(before.velocity, after.velocity)

    def test_half_open_phase_boundary(self):
        m, records, p = fixture()
        p.loc[0, 'frame_end'] = 10
        _, why = snapshot(records, m, p, 10, 1, 1, CFG)
        self.assertEqual(why, 'no_matching_in_play_phase')

    def test_no_velocity_across_gap_or_period(self):
        m, records, p = fixture()
        records[5]['period'] = 2
        _, why = snapshot(records, m, p, 10, 1, 1, CFG)
        self.assertEqual(why, 'missing_past_velocity_window')

    def test_unknown_carrier_is_not_inferred(self):
        m, records, p = fixture()
        records[10]['possession']['player_id'] = None
        _, why = snapshot(records, m, p, 10, 1, 1, CFG)
        self.assertEqual(why, 'carrier_not_confirmed')

    def test_clear_offside_and_gk_not_candidate(self):
        m, records, p = fixture()
        records[10]['player_data'][1]['x'] = 49
        s, why = snapshot(records, m, p, 10, 1, 1, dict(CFG, max_pass_m=60))
        self.assertIsNone(why)
        self.assertNotIn(2, s.ids[s.target_indices])
        self.assertNotIn(11, s.ids[s.target_indices])

    def test_duplicate_frame_rejected(self):
        m, records, _ = fixture()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'bad.jsonl'
            path.write_text(json.dumps(records[10])+'\n'+json.dumps(records[10])+'\n')
            with self.assertRaisesRegex(ValueError, 'increase strictly'):
                read_tracking(path, m, {10})

    def test_paired_cluster_bootstrap_preserves_identical_models(self):
        df = pd.DataFrame(dict(match_id=[1]*6, phase=['a','a','b','b','c','c'], geometry=[.1,.2,.3,.4,.5,.6], arrival=[.1,.2,.3,.4,.5,.6], ease=[1,2,3,2,4,5]))
        result = bootstrap(df, 50, 42)
        self.assertEqual(result, bootstrap(df, 50, 42))
        self.assertEqual(result['interval_95'], [0., 0.])

    def test_splits_disjoint(self):
        self.assertFalse(set(CFG['development_matches']) & set(CFG['held_out_matches']))
