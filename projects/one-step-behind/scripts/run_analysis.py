"""Run frozen analysis; raw source verification is a prerequisite."""
import argparse
import csv
import hashlib
import json
import platform
from pathlib import Path
import numpy as np
from one_step_behind.data import load_match, clock
from one_step_behind.detector import eligible_segments, analyze
ROOT=Path(__file__).resolve().parents[1]

def save_csv(path, rows):
    if not rows:
        path.write_text('candidate\n')
        return
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w') as f:
        w=csv.DictWriter(f,fieldnames=keys); w.writeheader(); w.writerows(rows)

def main():
    p=argparse.ArgumentParser(); p.add_argument('--match',type=int); args=p.parse_args()
    config_bytes=(ROOT/'configs/pilot.json').read_bytes(); cfg=json.loads(config_bytes)
    provenance=json.loads((ROOT/'data/provenance.json').read_text())
    for r in provenance['files']:
        with (ROOT/r['file']).open('rb') as f:
            if hashlib.file_digest(f,'sha256').hexdigest()!=r['sha256']: raise ValueError('Source changed')
    for mid in ([args.match] if args.match else [cfg['development_match'],cfg['held_out_match']]):
        d=load_match(ROOT/'data/raw',mid)
        segments,reasons=eligible_segments(d,cfg)
        summary,events=analyze(segments,reasons,cfg)
        observed,oreasons=eligible_segments(d,cfg,True)
        obs,oevents=analyze(observed,oreasons,cfg)
        sensitivities=[]
        for tol in [2.,3.,4.]:
            for persistence in [.3,.5,.8]:
                settings={**cfg,'gap_m':tol,'persistence_s':persistence}
                result,_=analyze(segments,reasons,settings)
                sensitivities.append(dict(gap_m=tol,persistence_s=persistence,steps=result['stepping_episodes'],candidates=result['candidate_steps'],recovered=result['recovered'],censored=result['recovery_censored']))
        for i,e in enumerate(events):
            e['match_id']=mid; e['id']=f'{mid}-{i+1:03d}'
            e['clock']=clock(e['start_frame'],e['period'],d['metadata'])
            if e['candidate']: e['defender_id']=int(d['ids'][e['defender_index']])
        result=dict(match_id=mid,split='development' if mid==cfg['development_match'] else 'held_out',
                    match=f"{d['metadata']['home_team']['name']} v {d['metadata']['away_team']['name']}",
                    config=cfg,config_sha256=hashlib.sha256(config_bytes).hexdigest(),
                    primary=summary,observed_only=obs,sensitivity=sensitivities,
                    python=platform.python_version(),numpy=np.__version__)
        (ROOT/f'outputs/results-{mid}.json').write_text(json.dumps(result,indent=2)+'\n')
        (ROOT/f'outputs/episodes-{mid}.json').write_text(json.dumps(events,indent=2)+'\n')
        save_csv(ROOT/f'outputs/episodes-{mid}.csv',events)
        save_csv(ROOT/f'outputs/sensitivity-{mid}.csv',sensitivities)
        save_csv(ROOT/f'outputs/observed-episodes-{mid}.csv',oevents)
        print(json.dumps(result,indent=2))
if __name__=='__main__': main()
