"""Independent checks of executed real-data outputs, skipped until the experiment runs."""
import csv
import json
import math
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def rank(values):
    order = sorted(range(len(values)), key=values.__getitem__)
    ranks = [0.]*len(values)
    i = 0
    while i < len(order):
        j = i+1
        while j < len(order) and values[order[i]] == values[order[j]]:
            j += 1
        for k in range(i,j):
            ranks[order[k]] = (i+1+j)/2
        i = j
    return ranks


def correlation(x,y):
    a,b=rank(x),rank(y)
    ma,mb=sum(a)/len(a),sum(b)/len(b)
    return sum((u-ma)*(v-mb) for u,v in zip(a,b))/math.sqrt(sum((u-ma)**2 for u in a)*sum((v-mb)**2 for v in b))


@unittest.skipUnless((ROOT/'outputs/results.json').exists(), 'run the real-data experiment first')
class ExecutedOutputTests(unittest.TestCase):
    def test_held_out_correlations_independently_recomputed(self):
        result=json.loads((ROOT/'outputs/results.json').read_text())
        config=json.loads((ROOT/'configs/pilot.json').read_text())
        with (ROOT/'outputs/possessions.csv').open() as f:
            rows=[r for r in csv.DictReader(f) if int(r['match_id']) in config['held_out_matches'] and r['ease']]
        self.assertEqual(len(rows),result['pooled']['n'])
        for name in ['geometry','arrival']:
            actual=correlation([float(r[name]) for r in rows],[float(r['ease']) for r in rows])
            self.assertAlmostEqual(actual,result['pooled'][name+'_rho'],places=12)

    def test_exclusion_waterfalls_and_csv_grain(self):
        audit=json.loads((ROOT/'outputs/data_audit.json').read_text())
        with (ROOT/'outputs/possessions.csv').open() as f:
            rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),len({(r['match_id'],r['event_id']) for r in rows}))
        for a in audit:
            self.assertEqual(a['possession_rows'],a['eligible_starts']+sum(a['exclusions'].values()))
            self.assertEqual(sum(int(r['match_id'])==a['match_id'] for r in rows),a['eligible_starts'])

    def test_dlo_nonnegative_and_not_double_counted(self):
        with (ROOT/'outputs/possessions.csv').open() as f:
            team={(r['match_id'],r['event_id']):float(r['arrival']) for r in csv.DictReader(f)}
        totals={}
        with (ROOT/'outputs/defender_snapshots.csv').open() as f:
            for r in csv.DictReader(f):
                dlo=float(r['dlo']);self.assertTrue(0<=dlo<=1)
                key=(r['match_id'],r['event_id']);totals[key]=totals.get(key,0)+dlo
        for key,value in totals.items():
            self.assertLessEqual(value,team[key]+1e-12)

    def test_replay_freeze_matches_initial_state(self):
        replay=json.loads((ROOT/'outputs/replays.json').read_text())
        for example in replay['examples']:
            first=example['frames'][0]
            self.assertEqual(first['obstruction'],first['frozen_obstruction'])
            self.assertTrue(all(v==0 for v in first['defender_state_effect']))
            self.assertGreaterEqual(example['frames'][-1]['t'],3)
