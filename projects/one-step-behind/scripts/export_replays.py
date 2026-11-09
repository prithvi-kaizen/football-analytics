"""Export real positions and independent scalar checks for selected stepping episodes."""
import hashlib
import json
import statistics
from pathlib import Path
import numpy as np
from one_step_behind.data import load_match, clock
from one_step_behind.detector import eligible_segments, gaps
ROOT=Path(__file__).resolve().parents[1]
cfg=json.loads((ROOT/'configs/pilot.json').read_text())
exports=[]; checks=0
for mid in [cfg['development_match'],cfg['held_out_match']]:
    d=load_match(ROOT/'data/raw',mid)
    segments,_=eligible_segments(d,cfg)
    episodes=json.loads((ROOT/f'outputs/episodes-{mid}.json').read_text())
    names={p['id']:p for p in d['metadata']['players']}
    for e in episodes:
        s=next(s for s in segments if s['team']==e['team_id'] and s['start']<=e['start_frame']<s['stop'])
        start=e['start_frame']; stop=min(s['stop'],e['end_frame']+1+cfg['hz'])
        xx=d['xy'][start:stop,s['members'],0]*s['sign']; gg=gaps(xx)
        peak_row,j=np.unravel_index(gg.argmax(),gg.shape)
        peak=float(gg[peak_row,j]); pid=int(d['ids'][s['members'][j]])
        # Deliberately independent Python/statistics implementation on all exported line values.
        for row,computed in zip(xx,gg):
            for k in range(len(row)):
                scalar=statistics.median([float(v) for i,v in enumerate(row) if i!=k])-float(row[k])
                assert abs(scalar-float(computed[k]))<1e-5
                checks+=1
        advance=xx[peak_row]-xx[0]; peer=np.delete(xx,j,axis=1)
        condition=dict(gap=peak>=cfg['gap_m'],peer_shape=float(np.ptp(peer[peak_row]))<=cfg['peer_spread_m'],
                       growth=peak-float(gg[0,j])>=cfg['gap_growth_m'],
                       relative_motion=float(advance[j])<=cfg['lag_motion_ratio']*float(np.median(np.delete(advance,j))))
        frames=[]
        # Display follow-up can outlast the step's candidate search window; eligibility still bounds it.
        display_stop=min(s['stop'],stop+40)
        for fr in range(start,display_stop):
            players=[]
            for k in np.flatnonzero(d['clean'][fr]):
                player=names[int(d['ids'][k])]
                players.append(dict(id=int(d['ids'][k]),number=player['number'],name=player['short_name'],
                                    team=player['team_id'],x=round(float(d['xy'][fr,k,0]*s['sign']),3),
                                    y=round(float(d['xy'][fr,k,1]*s['sign']),3),observed=bool(d['detected'][fr,k]),
                                    line=int(k) in s['members']))
            x=d['xy'][fr,s['members'],0]*s['sign']
            gap=gaps(x[None])[0]
            frames.append(dict(frame=fr,clock=clock(fr,e['period'],d['metadata']),t=round((fr-start)/10,2),players=players,
                               ball=[round(float(v*s['sign']),3) for v in d['ball'][fr]],
                               reference=round(float(np.median(x)),3),
                               gaps={str(int(d['ids'][k])):round(float(v),4) for k,v in zip(s['members'],gap)},
                               spread=round(float(np.ptp(x)),4)))
        lineids=[int(d['ids'][k]) for k in s['members']]
        line_obs=sum(p['observed'] for f in frames for p in f['players'] if p['line'])/(len(frames)*len(lineids))
        e.update(peak_search_gap_m=peak,highlight_id=pid,highlight_name=names[pid]['short_name'],
                 peak_frame=start+int(peak_row),peak_conditions=condition)
        team=next(t for t in [d['metadata']['home_team'],d['metadata']['away_team']] if t['id']==e['team_id'])
        exports.append(dict(**e,match=f"{d['metadata']['home_team']['short_name']} v {d['metadata']['away_team']['short_name']}",
                            date=d['metadata']['date_time'][:10],team_name=team['short_name'],
                            phase=d['phase_rows'][e['phase_id']]['team_in_possession_phase_type'],
                            split='development' if mid==cfg['development_match'] else 'held_out',line_ids=lineids,
                            line_observed_fraction=line_obs,frames=frames))
    (ROOT/f'outputs/episode-diagnostics-{mid}.json').write_text(json.dumps(episodes,indent=2)+'\n')
hold=[e for e in exports if e['split']=='held_out']
baseline=sorted([e for e in hold if e['baseline']],key=lambda e:e['start_frame'])
comparison=max([e for e in hold if not e['baseline']],key=lambda e:e['peak_search_gap_m'])
selected=(baseline+[comparison])[:3]
# If no baseline exists, select chronological eligible steps. Never relabel them candidates.
if len(selected)<3:
    selected += [e for e in hold if e not in selected][:3-len(selected)]
payload=dict(title='One Step Behind',config=cfg,examples=selected,
             selection='All held-out instantaneous baseline flags chronologically, then largest remaining search-window gap. No primary candidates exist.',
             summaries=[json.loads((ROOT/f'outputs/results-{mid}.json').read_text()) for mid in [cfg['development_match'],cfg['held_out_match']]])
(ROOT/'outputs/replays.json').write_text(json.dumps(payload,separators=(',',':'))+'\n')
(ROOT/'outputs/independent-checks.json').write_text(json.dumps(dict(scalar_gap_checks=checks,passed=True,selected_ids=[e['id'] for e in selected]),indent=2)+'\n')
for e in selected: print(e['id'],e['clock'],e['team_name'],e['highlight_name'],e['peak_search_gap_m'],e['peak_conditions'],len(e['frames']),e['line_observed_fraction'])
