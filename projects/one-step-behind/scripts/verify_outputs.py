"""Cross-check exported frames directly against raw JSONL, without the analytics loader."""
import hashlib
import json
import statistics
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'outputs/replays.json').read_text())
assert len(data['examples'])==3
wanted={}
for e in data['examples']:
    for f in e['frames']:wanted.setdefault(e['match_id'],set()).add(f['frame'])
source={}
for mid,frames in wanted.items():
    with (ROOT/f'data/raw/{mid}_tracking_extrapolated.jsonl').open() as stream:
        for line in stream:
            row=json.loads(line)
            if row['frame'] in frames:source[mid,row['frame']]=row
checks=0;max_error=0
for e in data['examples']:
    m=json.loads((ROOT/f"data/raw/{e['match_id']}_match.json").read_text())
    sign=1 if m['home_team_side'][e['period']-1]=='left_to_right' else -1
    if e['team_id']!=m['home_team']['id']:sign=-sign
    for f in e['frames']:
        raw=source[e['match_id'],f['frame']]
        records={p['player_id']:p for p in raw['player_data']}
        depths=[records[pid]['x']*sign for pid in e['line_ids']]
        assert abs(f['reference']-statistics.median(depths))<=.000501
        for p in f['players']:
            r=records[p['id']]
            error=max(abs(p['x']-r['x']*sign),abs(p['y']-r['y']*sign));max_error=max(error,max_error)
            assert error<=.000501
            assert p['observed']==(r['is_detected'] is True)
            assert p['line']==(p['id'] in e['line_ids'])
            checks+=1
        for pid in e['line_ids']:
            gap=statistics.median([records[q]['x']*sign for q in e['line_ids'] if q!=pid])-records[pid]['x']*sign
            assert abs(f['gaps'][str(pid)]-gap)<.00011
        assert raw['period']==e['period']
    assert max(f['gaps'][str(e['highlight_id'])] for f in e['frames'] if f['frame']<=e['end_frame']+10)==round(e['peak_search_gap_m'],4)
for mid in [1925299,1996435]:
    r=json.loads((ROOT/f'outputs/results-{mid}.json').read_text())
    events=json.loads((ROOT/f'outputs/episodes-{mid}.json').read_text())
    assert len(events)==r['primary']['stepping_episodes']
    assert sum(e['candidate'] for e in events)==r['primary']['candidate_steps']
    assert sum(e['baseline'] for e in events)==r['primary']['baseline_steps']
    assert abs(sum(e['duration_s'] for e in events)-r['primary']['stepping_seconds'])<1e-7
    assert r['config_sha256']==hashlib.sha256((ROOT/'configs/pilot.json').read_bytes()).hexdigest()
    audit=json.loads((ROOT/f'outputs/audit-{mid}.json').read_text())
    assert sum(r['primary']['eligibility'].values())==audit['source_frames']*2
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(ROOT/'outputs/demo.mp4')]))
assert abs(float(probe['format']['duration'])-32)<.05
assert probe['streams'][0]['codec_name']=='h264'
assert probe['streams'][0]['width']==1600 and probe['streams'][0]['height']==900
files={}
for directory in ['outputs','one_step_behind','configs','scripts']:
    for path in (ROOT/directory).glob('*'):
        if path.is_file() and path.name not in ['verification.json','video-render.log']:
            files[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest()
report=dict(passed=True,raw_coordinate_and_flag_checks=checks,max_coordinate_rounding_error_m=max_error,
            replay_frames=sum(len(e['frames']) for e in data['examples']),duration_s=probe['format']['duration'],
            video_codec=probe['streams'][0]['codec_name'],files=files)
(ROOT/'outputs/verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='files'},indent=2))
