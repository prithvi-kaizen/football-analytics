"""Independent full-source label reconstruction and threshold sensitivity audit.

Uses pandas period-clock arithmetic and source records, not the extraction labeler.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT=Path(__file__).resolve().parents[1]


def reference_label(events, kick_index, horizon):
    kick=events[kick_index]
    elapsed=pd.to_timedelta([e['timestamp'] for e in events]).total_seconds()
    origin=elapsed[kick_index]
    same_period=[i for i,e in enumerate(events) if i>=kick_index and e['period']==kick['period']]
    stop=len(events)
    inclusive=False
    observable=False
    for i in same_period:
        e=events[i]
        if elapsed[i]<origin: continue
        if elapsed[i]>origin+horizon:
            stop,observable=i,True
            break
        typ=e['type']['name']
        subtype=e.get('pass',{}).get('type',{}).get('name') if typ=='Pass' else e.get('shot',{}).get('type',{}).get('name')
        new_restart=(typ=='Pass' and subtype in {'Corner','Free Kick','Throw-in','Throw In','Goal Kick','Kick Off'}) or (typ=='Shot' and subtype in {'Corner','Free Kick','Penalty','Kick Off'})
        if i>kick_index and (new_restart or e.get('possession')!=kick.get('possession') or e.get('possession_team',{}).get('id',kick['team']['id'])!=kick['team']['id']):
            stop,observable=i,True
            break
        foul=typ in {'Foul Won','Foul Committed'} and not e.get(typ.lower().replace(' ','_'),{}).get('advantage',False)
        is_goal=typ=='Shot' and e.get('shot',{}).get('outcome',{}).get('name')=='Goal'
        if e.get('out') or typ in {'Half End','Offside','Injury Stoppage','Referee Ball-Drop'} or foul or is_goal:
            stop,inclusive,observable=i,True,True
            break
    if any(e['period']>kick['period'] for e in events[kick_index:]): observable=True
    indexes=[i for i in same_period if i<stop or (inclusive and i==stop)]
    shots=[events[i]['id'] for i in indexes if 0<=elapsed[i]-origin<=horizon and events[i]['type']['name']=='Shot' and events[i]['team']['id']==kick['team']['id']]
    return (True if shots else False if observable else None), shots


def main():
    actual=pd.read_csv(ROOT/'outputs/corners.csv').set_index('corner_id')
    info=json.loads((ROOT/'outputs/manifest.json').read_text())
    sensitivity=[]
    checked=0
    for match in info['matches']:
        events=json.loads((ROOT/f'data/raw/data/events/{match["match_id"]}.json').read_text())
        for i,kick in enumerate(events):
            if kick['id'] not in actual.index: continue
            row=actual.loc[kick['id']]
            label,shots=reference_label(events,i,info['horizon_seconds'])
            assert label==row.shot_created, (kick['id'],label,row.shot_created)
            assert len(shots)==row.shots, kick['id']
            checked+=1
            for horizon in [10,15,20]:
                label,_=reference_label(events,i,horizon)
                sensitivity.append({'tournament':row.tournament,'horizon_seconds':horizon,'positive':label,'match_id':match['match_id']})
    assert checked==len(actual)
    sensitivity=pd.DataFrame(sensitivity)
    table=sensitivity.groupby(['tournament','horizon_seconds']).positive.agg(corners='count',shot_created='sum').reset_index()
    table['rate']=table.shot_created/table.corners
    table.to_csv(ROOT/'reports/window_sensitivity.csv',index=False)
    metrics=json.loads((ROOT/'outputs/model.json').read_text())
    result={'status':'passed','independently_reconstructed_corners':checked,'matches':len(info['matches']),
            'source_revision':info['revision'],'mismatched_labels':0,'mismatched_shot_counts':0,
            'disjoint_model_match_split':not bool(set(metrics.get('train_matches',[])) & set(metrics.get('test_matches',[]))),
            'scope':'All local source corner labels and shot counts; 10/15/20 second sensitivity. Not video adjudication.'}
    (ROOT/'reports/validation.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
    print(table.to_string(index=False))


if __name__=='__main__': main()
