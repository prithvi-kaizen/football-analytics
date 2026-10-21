"""Reproducible, dependency-free pressure sequence extraction from StatsBomb events."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_WINDOW = 15
PRE_WINDOW = 15
NX, NY = 12, 8
STOP_TYPES = {'Half End', 'Foul Committed', 'Foul Won', 'Offside', 'Injury Stoppage', 'Referee Ball-Drop'}
RESTARTS = {'Throw-in', 'Free Kick', 'Corner', 'Goal Kick', 'Kick Off', 'Penalty'}

def name(e, field):
    return e.get(field, {}).get('name', '')

def seconds(e):
    h, m, s = e['timestamp'].split(':')
    return int(h) * 3600 + int(m) * 60 + float(s)

def point(e, team, end=False):
    p = e.get('pass', e.get('carry', {})).get('end_location') if end else e.get('location')
    if not p or len(p) < 2:
        return None
    x, y = p[:2]
    return [round(x, 2), round(y, 2)] if name(e, 'team') == team else [round(120-x, 2), round(80-y, 2)]

def stopped(e):
    return name(e, 'type') in STOP_TYPES or e.get('out', False) or name(e.get('pass', {}), 'type') in RESTARTS

def controlled(e, team):
    if name(e, 'team') != team or not e.get('location'):
        return False
    typ = name(e, 'type')
    if typ == 'Ball Recovery':
        return not e.get('ball_recovery', {}).get('recovery_failure', False)
    if typ == 'Interception':
        return name(e.get('interception', {}), 'outcome') in {'Won', 'Success', 'Success In Play'}
    if typ == 'Goal Keeper':
        return name(e.get('goalkeeper', {}), 'type') in {'Collected', 'Keeper Sweeper'} and name(e.get('goalkeeper', {}), 'outcome') not in {'Lost In Play', 'Lost Out', 'No Touch'}
    if name(e, 'possession_team') != team:
        return False
    return typ in {'Pass', 'Carry', 'Shot'} or (typ == 'Ball Receipt*' and 'outcome' not in e.get('ball_receipt', {}))

def cell(p):
    return min(NY-1, max(0, int(p[1]/80*NY))) * NX + min(NX-1, max(0, int(p[0]/120*NX)))

def fit_xt(matches):
    totals = Counter(); reward = Counter(); transitions = defaultdict(Counter)
    for events in matches.values():
        for e in events:
            typ = name(e, 'type')
            if typ not in {'Pass', 'Carry', 'Shot'} or not e.get('location') or e['period'] > 4:
                continue
            a = cell(e['location']); totals[a] += 1
            if typ == 'Shot':
                reward[a] += e.get('shot', {}).get('statsbomb_xg', 0)
            elif typ == 'Carry' or 'outcome' not in e.get('pass', {}):
                p = e[typ.lower()].get('end_location')
                if p:
                    transitions[a][cell(p)] += 1
    values = [0.] * (NX * NY)
    for iteration in range(2000):
        update = [(reward[a] + sum(n*values[b] for b,n in transitions[a].items()))/totals[a] if totals[a] else 0. for a in range(NX*NY)]
        delta = max(abs(a-b) for a,b in zip(values, update)); values = update
        if delta < 1e-10:
            break
    return values, {'nx': NX, 'ny': NY, 'iterations': iteration+1, 'residual': delta, 'actions': sum(totals.values()), 'values': values}

def compact(e, team, start):
    p = point(e, team)
    return {'id': e['id'], 'type': name(e, 'type'), 'team': name(e, 'team'),
            'player': name(e, 'player'), 't': round(seconds(e)-start, 3),
            'duration': e.get('duration', 0), 'x': p[0] if p else None, 'y': p[1] if p else None,
            'end': point(e, team, True), 'outcome': name(e.get('pass', {}), 'outcome')}

def detect(events, match, values=None):
    rows=[]; episode_counts=Counter()
    events=sorted(events, key=lambda e:e['index'])
    times=[seconds(e) for e in events]
    for i,e in enumerate(events):
        if name(e, 'type') != 'Pressure' or not e.get('location') or e['period'] > 4:
            continue
        team=name(e,'team'); opponent=name(e,'possession_team'); t=times[i]
        if team == opponent or not opponent:
            continue
        before=[]
        for j in range(i-1,-1,-1):
            p=events[j]
            if p['period'] != e['period'] or t-times[j] > PRE_WINDOW or p['possession'] != e['possession']:
                break
            if name(p,'type') == 'Pass' and name(p,'team') == opponent:
                before.append(p)
        before.reverse()
        prior=[p for p in before if 'outcome' not in p.get('pass',{}) and seconds(p)+p.get('duration',0) <= t+0.05]
        last=prior[-1] if prior else None
        recovery=None; recovery_index=None; after_passes=0
        tail=[]
        for j in range(i+1,len(events)):
            p=events[j]
            if p['period'] != e['period'] or times[j]-t > MAX_WINDOW:
                break
            if stopped(p):
                break
            tail.append(p)
            if name(p,'type') == 'Pass' and name(p,'team') == opponent:
                after_passes+=1
            if controlled(p,team):
                recovery=p; recovery_index=j; break
        duration=round(seconds(recovery)-t,3) if recovery else None
        pass_to_wide=False; direction='No preceding completed pass'; lag=None
        if last:
            a=last['location']; b=last['pass']['end_location']; dx=b[0]-a[0]; dy=b[1]-a[1]
            direction='Forward' if dx > 5 else 'Backward' if dx < -5 else 'Lateral'
            lag=t-seconds(last)-last.get('duration',0)
            target=point(last,team,True)
            pass_to_wide=(b[1]<=18 or b[1]>=62) and abs(dy)>=8 and 0<=lag<=3 and math.dist(target,e['location'])<=15
        subsequent=[]; xt=None; shot_xg=0.
        if recovery:
            xt=0. if values is not None else None
            gained_possession = recovery['possession'] if name(recovery, 'possession_team') == team else None
            for j in range(recovery_index,len(events)):
                p=events[j]
                if p['period'] != e['period'] or times[j]-seconds(recovery)>10 or name(p,'team') != team and name(p,'possession_team') != team:
                    break
                if j>recovery_index and stopped(p):
                    break
                if gained_possession is None and name(p, 'possession_team') == team:
                    gained_possession = p['possession']
                if gained_possession is not None and p['possession'] != gained_possession:
                    break
                if name(p,'team') != team:
                    continue
                subsequent.append(p)
                if name(p,'type')=='Shot':
                    shot_xg+=p.get('shot',{}).get('statsbomb_xg',0)
                if values is not None and p.get('location') and (name(p,'type')=='Carry' or name(p,'type')=='Pass' and 'outcome' not in p.get('pass',{})):
                    end=point(p,team,True)
                    if end:
                        xt+=values[cell(end)]-values[cell(p['location'])]
        episode=f"{match['match_id']}:{e['period']}:{e['possession']}:{team}"
        episode_counts[episode]+=1
        x,y=e['location']; rp=point(recovery,team) if recovery else None
        replay={p['id']:p for p in before[-5:]+[e]+tail+subsequent}
        replay=sorted(replay.values(),key=lambda p:p['index'])
        rows.append({'id':e['id'],'match_id':match['match_id'],'date':match['match_date'],
            'match':f"{match['home_team']['home_team_name']} vs {match['away_team']['away_team_name']}",
            'stage':match['competition_stage']['name'],'team':team,'opponent':opponent,'period':e['period'],
            'minute':e['minute'],'second':e['second'],'player':name(e,'player'), 'x':x,'y':y,
            'third':'Attacking third' if x>=80 else 'Middle third' if x>=40 else 'Defensive third',
            'channel':'Left' if y<80/3 else 'Right' if y>=160/3 else 'Centre',
            'episode':episode,'episode_first':episode_counts[episode]==1,
            'recovery_seconds':duration,'recovery_id':recovery['id'] if recovery else None,
            'recovery_x':rp[0] if rp else None,'recovery_y':rp[1] if rp else None,
            'recovery_type':name(recovery,'type') if recovery else None,
            'passes_before':len(before),'passes_after':after_passes if recovery else None,
            'passes_allowed':len(before)+after_passes if recovery else None,
            'pass_direction':direction,'wide_candidate':pass_to_wide,'wide_entry':'Yes' if pass_to_wide else 'No',
            'subsequent_xt':round(xt,6) if xt is not None else None,'subsequent_xg':round(shot_xg,6) if recovery else None,
            'replay_json':json.dumps([compact(p,team,t) for p in replay],separators=(',',':'))})
    return rows

def main():
    matches=json.loads((ROOT/'data/raw/matches.json').read_text())
    all_events={m['match_id']:json.loads((ROOT/f"data/raw/{m['match_id']}.json").read_text()) for m in matches}
    values, model=fit_xt(all_events)
    (ROOT/'outputs/xt_model.json').write_text(json.dumps(model,indent=2))
    rows=[r for m in matches for r in detect(all_events[m['match_id']],m,values)]
    now=datetime.now(timezone.utc).isoformat(); manifest=json.loads((ROOT/'data/manifest.json').read_text())
    source={'name':'StatsBomb Open Data · UEFA Euro 2024', 'url':'https://github.com/hudl/open-data',
        'files':[f"https://github.com/hudl/open-data/blob/{manifest['revision']}/data/matches/55/282.json"],
        'executedAt':now,'period':'14 June–14 July 2024','classification':'observed',
        'description':'All 51 matches; 24 teams; one row per located opposition-possession Pressure event, periods 1–4.',
        'caveats':['Temporal association does not establish defensive intent or causality.',
          'Multiple pressure events can share one recovery. Deduplicate recovery_id for regain counts.',
          'Event-level replays show recorded actions, not player tracking. Motion between events is interpolated.',
          'The 12×8 xT model is fitted on this tournament using shot xG as terminal reward; in-sample and unvalidated.',
          'Pass counts before pressure cover only the preceding 15 seconds of the same possession.'],
        'metricDefinitions':[
          {'label':'Pressure-to-recovery rate','definition':'Share of filtered pressure events followed by controlled team possession within the selected 3–15 second window, in the same period and before a dead ball.'},
          {'label':'Wide-entry candidate','definition':'Last completed opposition pass moved at least 8 y units, ended at y ≤18 or ≥62, arrived 0–3 seconds before pressure, and ended within 15 pitch units of the pressure. Heuristic, not proof of a trap.'},
          {'label':'Subsequent xT','definition':'Sum of signed xT changes from completed passes and carries within 10 seconds of the recovery, in its possession. The model is a 12×8 Markov grid fitted to Euro 2024 events, with shot xG as terminal reward.'}],
        'evidenceFlow':[{'title':'Source revision','detail':manifest['revision']},
                        {'title':'Download','detail':'python3 scripts/download_data.py; fetch competition 55, season 282 and all 51 event JSON files; verify event IDs and record SHA-256 hashes.'},
                        {'title':'Transform','detail':'python3 scripts/build_dataset.py; normalize opponent coordinates by (120−x,80−y), extract pressure anchors, link prior passes and earliest controlled regain within 15 seconds; stop at dead balls and period boundaries.'}]}
    snapshot={'title':'Pressing trap detector','subtitle':'UEFA Euro 2024','generatedAt':now,'buildStatus':'creating',
        'queries':{'pressures':{'rows':rows,'payloadColumns':['replay_json'],'source':source,
            'methods':[{'language':'python','code':'python3 scripts/build_dataset.py'}]}}}
    (ROOT/'outputs/reviewed.json').write_text(json.dumps(snapshot,separators=(',',':')))
    fields=[k for k in rows[0] if k!='replay_json']
    with (ROOT/'outputs/pressures.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(rows)
    print(json.dumps({'pressures':len(rows),'teams':len({r['team'] for r in rows}),'model_iterations':model['iterations'],
       'Spain':{'pressures':sum(r['team']=='Spain' for r in rows),'regains_5s':len({r['recovery_id'] for r in rows if r['team']=='Spain' and r['recovery_seconds'] is not None and r['recovery_seconds']<=5})}}))

if __name__=='__main__':
    main()
