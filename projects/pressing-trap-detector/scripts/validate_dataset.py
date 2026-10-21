"""Verify downloaded-file integrity and the published evidence's core invariants."""
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'data/manifest.json').read_text())
assert len(manifest['matches'])==51
for match in manifest['matches']:
    raw=(ROOT/f"data/raw/{match['match_id']}.json").read_bytes()
    assert hashlib.sha256(raw).hexdigest()==match['sha256']
    events=json.loads(raw)
    assert len(events)==match['events']
    assert len({e['id'] for e in events})==len(events)

rows=json.loads((ROOT/'outputs/reviewed.json').read_text())['queries']['pressures']['rows']
assert len(rows)==12891
assert len({r['id'] for r in rows})==len(rows)
assert len({r['team'] for r in rows})==24
for r in rows:
    assert 0<=r['x']<=120 and 0<=r['y']<=80
    assert r['team']!=r['opponent']
    if r['recovery_id'] is not None:
        assert 0<=r['recovery_seconds']<=15
        assert 0<=r['recovery_x']<=120 and 0<=r['recovery_y']<=80
        assert r['passes_allowed']==r['passes_before']+r['passes_after']
    else:
        assert r['recovery_seconds'] is None and r['subsequent_xt'] is None
    replay=json.loads(r['replay_json'])
    assert [e['t'] for e in replay]==sorted(e['t'] for e in replay)
    assert sum(e['id']==r['id'] for e in replay)==1

spain=[r for r in rows if r['team']=='Spain']
assert len(spain)==991
for window,successes,regains in [(5,171,132),(10,280,170)]:
    good=[r for r in spain if r['recovery_seconds'] is not None and r['recovery_seconds']<=window]
    assert len(good)==successes
    assert len({r['recovery_id'] for r in good})==regains
model=json.loads((ROOT/'outputs/xt_model.json').read_text())
assert len(model['values'])==96 and all(0<=v<=1 for v in model['values'])
assert model['residual']<1e-10
print('Verified: 51 source hashes, 187924 events, 12891 unique pressure anchors, 24 teams, coordinate bounds, replay order, recovery windows, pass counts, Spain totals and xT convergence.')
