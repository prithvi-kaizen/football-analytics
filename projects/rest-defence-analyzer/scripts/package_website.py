"""Package only verified public results into a portable browser release."""
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from rest_defence.pipeline import load_result
from rest_defence.geometry import central_grid,clear_lane
from rest_defence.data import analysis_fingerprint


def sha(data):
    return hashlib.sha256(data).hexdigest()


def package():
    result=ROOT/'outputs/J03WPY'
    df,meta,audit=load_result(result)
    if audit.get('analysis_code_sha256')!=analysis_fingerprint():
        raise ValueError('Analytical sources changed: reproduce the full-match pipeline before publication')
    snapshots=pd.read_parquet(result/'snapshots.parquet')
    replays=pd.read_parquet(result/'replays.parquet')
    timelines=pd.read_parquet(result/'timeline.parquet')
    rows=json.loads(df.to_json(orient='records',double_precision=12))
    for row in rows:
        key=row['transition_id']
        snap=snapshots[snapshots.transition_id.eq(key)]
        replay=replays[replays.transition_id.eq(key)]
        timeline=timelines[timelines.transition_id.eq(key)]
        ball=np.array([row['ball_x'],row['ball_y']])
        rest=snap[snap.team.eq(row['losing_team'])&~snap.is_gk&snap.x.le(ball[0])]
        grid=central_grid(ball,meta['length'],meta['width'])
        open_cells=grid[(cdist(grid,rest[['x','y']]).min(axis=1)>5) if len(rest) else np.ones(len(grid),dtype=bool)]
        opponents=snap[~snap.team.eq(row['losing_team'])&~snap.is_gk]
        options=opponents[(opponents.x<=ball[0]-3)&(np.linalg.norm(opponents[['x','y']].to_numpy()-ball,axis=1)<=40)]
        defenders=snap[snap.team.eq(row['losing_team'])&~snap.is_gk][['x','y']].to_numpy()
        lanes=[xy.tolist() for xy in options[['x','y']].to_numpy() if clear_lane(ball,xy,defenders)]
        row['overlay']={'central':open_cells.tolist(),'lanes':lanes}
        def players(g):
            return [[p.player,round(p.x,3),round(p.y,3)] for p in g.itertuples()]
        row['snapshot']=players(snap)
        row['replay']=[]
        indexed=timeline.set_index('frame')
        for frame,group in replay.groupby('frame',sort=True):
            if frame not in indexed.index:
                continue
            b=indexed.loc[frame]
            row['replay'].append({'frame':int(frame),'time':round(float(b.relative_s),3),'ball':[float(b.x),float(b.y)],'players':players(group)})
        observed=timeline[timeline.relative_s.ge(0)]
        if observed.empty or observed.iloc[0].relative_s!=0:
            raise ValueError('Timeline lacks native turnover frame')
        row['timeline']=[[round(float(p.relative_s),3),round(float(observed.iloc[0].x-p.x),3)] for p in observed.itertuples()]
        if abs(max(p[1] for p in row['timeline'])-row['progress_m'])>.002:
            raise ValueError('Timeline progression mismatch')
    payload={'schema_version':1,'metadata':meta,'audit':audit,'transitions':rows,
             'findings':json.loads((result/'findings.json').read_text())}
    data=json.dumps(payload,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
    archive=gzip.compress(data,compresslevel=9,mtime=0)
    web=ROOT/'web'
    (web/'snapshot.json.gz').write_bytes(archive)
    assets={name:sha((web/name).read_bytes()) for name in ['index.html','style.css','app.js']}
    bundle={'schema_version':1,'snapshot':{'archive':'snapshot.json.gz','archive_sha256':sha(archive),'sha256':sha(data),
             'path':f'snapshot.{sha(data)[:16]}.json.gz'},'assets':assets,'transitions':len(rows)}
    (web/'bundle.json').write_text(json.dumps(bundle,indent=2)+'\n')
    print(f'Packaged {len(rows)} real transitions: {len(data):,} bytes / {len(archive):,} gzip bytes')


if __name__=='__main__':
    package()
