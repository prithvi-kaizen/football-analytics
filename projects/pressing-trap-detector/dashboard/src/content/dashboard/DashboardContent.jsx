import React, { useEffect, useMemo, useState } from 'react';
import { DataComponent, EvidenceChart, Filters, SectionHeader, SortableItem, SortableRegion, useDataApp } from '../../data-app-public.jsx';
import './pressing.css';
import statsbombLogo from '../assets/statsbomb-logo.png';

const fmt = n => Number(n).toLocaleString('en-GB');
const pct = (a,b) => b ? `${(100*a/b).toFixed(1)}%` : 'No data';
const successful = (r,w) => r.recovery_seconds !== null && r.recovery_seconds <= w;
const uniqueRecoveries = rows => [...new Map(rows.map(r => [r.recovery_id,r])).values()];
const mean = values => values.length ? values.reduce((a,b)=>a+b,0)/values.length : null;
const threat = value => (Math.abs(value)<0.0005?0:value).toFixed(3);
const clock = r => `${r.minute}:${String(r.second).padStart(2,'0')}`;

function Pitch({children,label}) {
  return <svg className="pt-pitch" viewBox="-4 -4 128 91" role="img" aria-label={label}>
    <rect x="0" y="0" width="120" height="80" fill="var(--pt-pitch)" />
    <g fill="none" stroke="var(--pt-lines)" strokeWidth=".45">
      <rect x="0" y="0" width="120" height="80"/><path d="M60 0V80"/><circle cx="60" cy="40" r="9.15"/>
      <path d="M0 18H18V62H0 M120 18H102V62H120 M0 30H6V50H0 M120 30H114V50H120"/>
      <circle cx="12" cy="40" r=".5"/><circle cx="108" cy="40" r=".5"/>
    </g>{children}<text x="60" y="86" textAnchor="middle" className="pt-pitch-caption">Pressing team attacks to the right →</text>
  </svg>;
}

function PressureMap({rows,recovery=false,window,onSelect,selected}) {
  const points = recovery ? uniqueRecoveries(rows.filter(r=>successful(r,window))) : rows;
  return <div data-reviewed-rows>
    <Pitch label={recovery?'Distinct recovery locations in the pressing team’s coordinate frame':'Pressure locations in the pressing team’s coordinate frame'}>
      {points.map(r=><circle key={r.id} cx={recovery?r.recovery_x:r.x} cy={recovery?r.recovery_y:r.y}
        r={selected===r.id?1.5:1} fill={recovery?'var(--pt-recovery)':successful(r,window)?'var(--pt-red)':'var(--pt-dot)'}
        opacity={selected===r.id?1:.65} stroke={selected===r.id?'var(--text)':'none'} strokeWidth=".35"
        tabIndex={0} role="button" aria-label={`${r.match}, ${clock(r)}, ${r.player}, ${successful(r,window)?'recovered':'not recovered'}; open replay`}
        onClick={()=>onSelect(r.id)} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();onSelect(r.id);}}}>
        <title>{`${r.match} · ${clock(r)} · ${r.player}\n${successful(r,window)?`Regain after ${r.recovery_seconds.toFixed(1)}s`:`No regain within ${window}s`}`}</title>
      </circle>)}
    </Pitch>
    <p className="pt-legend">{recovery?<><i className="pt-green-dot"/>{fmt(points.length)} distinct controlled recoveries</>:<><i className="pt-red-dot"/>Regain within {window}s <i className="pt-grey-dot"/>Other pressures</>}</p>
    {!points.length&&<p className="pt-empty" role="status">No {recovery?'recoveries':'pressures'} in this selection. Broaden the filters.</p>}
  </div>;
}

function Replay({row}) {
  const [time,setTime]=useState(0); const [playing,setPlaying]=useState(false);
  const events=useMemo(()=>row?JSON.parse(row.replay_json):[],[row?.id]);
  const min=events.length?Math.min(0,events[0].t):0;
  const max=events.length?Math.max(1,...events.map(e=>e.t+Math.min(e.duration||0,3))):1;
  useEffect(()=>{setTime(min);setPlaying(false);},[row?.id,min]);
  useEffect(()=>{if(!playing)return;const timer=setInterval(()=>setTime(t=>{if(t+.08>=max){setPlaying(false);return max;}return t+.08;}),80);return()=>clearInterval(timer);},[playing,max]);
  const spatial=events.filter(e=>e.x!==null);
  const active=[...spatial].reverse().find(e=>e.t<=time)||spatial[0];
  let ball=active?{x:active.x,y:active.y}:null;
  if(active?.end&&active.duration>0){const f=Math.min(1,Math.max(0,(time-active.t)/active.duration));ball={x:active.x+(active.end[0]-active.x)*f,y:active.y+(active.end[1]-active.y)*f};}
  const step=dir=>{setPlaying(false);setTime(dir>0?(events.find(e=>e.t>time+.05)?.t??max):([...events].reverse().find(e=>e.t<time-.05)?.t??min));};
  if(!row)return <p className="pt-empty">Select a pressure on the map or in the sequence list to inspect its events.</p>;
  return <div className="pt-replay-body" data-reviewed-rows>
    <div className="pt-replay-heading"><strong>{row.match}</strong><span>{clock(row)} · {row.player}</span></div>
    <Pitch label="Event-level replay, with interpolated ball position and recorded pass paths">
      {spatial.filter(e=>e.t<=time&&e.end).map(e=><line key={e.id} x1={e.x} y1={e.y} x2={e.end[0]} y2={e.end[1]} stroke={e.team===row.team?'var(--pt-recovery)':'var(--pt-pass)'} strokeWidth=".65" strokeDasharray={e.type==='Carry'?'1 1':undefined} opacity=".6"/>)}
      {time>=0&&<><circle cx={row.x} cy={row.y} r="3" fill="none" stroke="var(--pt-red)" strokeWidth=".8"/><text x={row.x} y={Math.max(4,row.y-4)} textAnchor="middle" className="pt-field-label">Pressure</text></>}
      {row.recovery_seconds!==null&&time>=row.recovery_seconds&&<rect x={row.recovery_x-1.6} y={row.recovery_y-1.6} width="3.2" height="3.2" fill="var(--pt-recovery)"/>}
      {ball&&<circle cx={ball.x} cy={ball.y} r="1.4" fill="var(--text)" stroke="var(--surface)" strokeWidth=".5"/>}
    </Pitch>
    <div className="pt-play-controls"><button onClick={()=>{if(time>=max)setTime(min);setPlaying(p=>!p);}}>{playing?'Pause':'Play'}</button>
      <button onClick={()=>{setPlaying(false);setTime(min);}}>Restart</button><button onClick={()=>step(-1)} aria-label="Previous recorded event">Previous</button><button onClick={()=>step(1)} aria-label="Next recorded event">Next</button>
      <output>{time>0?'+':''}{time.toFixed(1)}s</output>
    </div>
    <label className="pt-scrub">Replay time<input aria-label="Replay time" type="range" min={min} max={max} step=".1" value={time} onChange={e=>{setPlaying(false);setTime(Number(e.target.value));}}/></label>
    <p className="pt-event-status" aria-live="off">{active?`${active.type} · ${active.player||active.team} · ${active.team}`:'No spatial event'}</p>
    <p className="pt-note">Recorded actions only. Ball movement between locations is interpolated; player positions and off-ball runs are unavailable.</p>
    <details><summary>Recorded events ({events.length})</summary><ol className="pt-events">{events.map(e=><li key={e.id}><button onClick={()=>{setPlaying(false);setTime(e.t);}}>{e.t>=0?'+':''}{e.t.toFixed(1)}s · {e.type} · {e.player||e.team}</button></li>)}</ol></details>
  </div>;
}

export function DashboardContent(){
  const {snapshot,queries,filters,setFilter,reviewedRows,activeFilters,assumptions,setAssumptions,chartStates,updateChartState}=useDataApp();
  const all=queries.pressures?.rows??[];
  const window=Math.max(3,Math.min(15,Number(assumptions.recoveryWindow)||5));
  const rows=reviewedRows('pressures',['id']);
  const good=rows.filter(r=>successful(r,window));const gains=uniqueRecoveries(good);
  const selected=chartStates['event-replay']?.inlineFilters?.event;
  const chosen=rows.find(r=>r.id===selected)||good.find(r=>r.wide_candidate)||good[0]||rows[0];
  const choose=id=>updateChartState('event-replay',{inlineFilters:{event:id}});
  const [outcome,setOutcome]=useState('all');const [page,setPage]=useState(0);
  useEffect(()=>{setPage(0);},[filters,window,outcome]);
  const listed=rows.filter(r=>outcome==='all'||(outcome==='success')===successful(r,window)).sort((a,b)=>Number(b.wide_candidate)-Number(a.wide_candidate)||Number(successful(b,window))-Number(successful(a,window))||a.date.localeCompare(b.date)||a.minute-b.minute||a.second-b.second);
  const scope=[...activeFilters,{field:'recoveryWindow',label:'Recovery window',value:`${window}s`}];
  const bind=rs=>({sourceRows:rs,displayRows:rs,scopeFilters:scope});
  const direction=['Forward','Lateral','Backward','No preceding completed pass'].map(direction=>({direction,pressures:rows.filter(r=>r.pass_direction===direction).length}));
  const zones=['Defensive third','Middle third','Attacking third'].map(third=>({third,recoveries:gains.filter(r=>(r.recovery_x>=80?'Attacking third':r.recovery_x>=40?'Middle third':'Defensive third')===third).length}));
  const comparisonRows=all.filter(r=>(!filters.third||filters.third==='all'||r.third===filters.third)&&(!filters.channel||filters.channel==='all'||r.channel===filters.channel)&&(!filters.wide_candidate||filters.wide_candidate==='all'||r.wide_entry===filters.wide_candidate));
  const teams=[...new Set(all.map(r=>r.team))].sort();
  const comparisons=teams.map(team=>{const rs=comparisonRows.filter(r=>r.team===team);const ok=rs.filter(r=>successful(r,window));const unique=uniqueRecoveries(ok);return {team,pressures:rs.length,successful:ok.length,recoveryRate:rs.length?ok.length/rs.length:null,recoveries:unique.length,meanXt:mean(unique.map(r=>r.subsequent_xt).filter(v=>v!==null))};});
  const directionChart={type:'horizontalBar',x:'direction',y:'pressures',colors:{pressures:'var(--pt-pass)'},valueDecimals:0};
  const zoneChart={type:'horizontalBar',x:'third',y:'recoveries',colors:{recoveries:'var(--pt-recovery)'},valueDecimals:0};
  const compareChart={type:'horizontalBar',x:'team',y:'recoveryRate',colors:{recoveryRate:'var(--pt-red)'},valueDecimals:3};
  const spain=all.filter(r=>r.team==='Spain');const spainGood=spain.filter(r=>successful(r,5));const spainGains=uniqueRecoveries(spainGood);
  const recoveryXt=mean(gains.map(r=>r.subsequent_xt).filter(v=>v!==null));
  const sourceUrl='https://github.com/hudl/open-data';
  return <article className="pt-app">
    <Filters filters={snapshot.filters??[]} queries={queries} values={filters} onChange={setFilter} ariaLabel="Pressure sequence filters" trailingControls={<>
      <label className="pt-window">Recovery window<select aria-label="Recovery window" value={window} onChange={e=>setAssumptions(a=>({...a,recoveryWindow:Number(e.target.value)}))}>{[3,5,8,10,15].map(w=><option key={w} value={w}>{w} seconds</option>)}</select></label>
      <button className="pt-reset" onClick={()=>{(snapshot.filters??[]).forEach(f=>setFilter(f.id,f.defaultValue??'all'));setAssumptions(a=>({...a,recoveryWindow:5}));setOutcome('all');}}>Reset filters</button>
    </>}/>
    <p className="pt-context" data-editable-id="scope-intro" data-editable-narrative="true">Opposition passes, pressure, controlled possession. Follow the recorded sequence and test the recovery window.</p>
    <DataComponent id="pressure-summary" queryId="pressures" title={`${filters.team==='all'?'All teams':filters.team||'Spain'} · pressure and recovery`} kind="custom" {...bind(rows)}>
      <div className="pt-summary" data-reviewed-rows><div><span>Pressure events</span><strong>{fmt(rows.length)}</strong><small>{new Set(rows.map(r=>r.match_id)).size} matches in selection</small></div>
        <div><span>Pressure-to-recovery rate</span><strong className="pt-emphasis">{pct(good.length,rows.length)}</strong><small>{fmt(good.length)} / {fmt(rows.length)} within {window}s</small></div>
        <div><span>Distinct recoveries</span><strong>{fmt(gains.length)}</strong><small>Shared recovery IDs counted once</small></div>
        <div><span>Mean subsequent xT</span><strong>{recoveryXt===null?'No data':`${recoveryXt>=0?'+':''}${recoveryXt.toFixed(3)}`}</strong><small>10s after regain · tournament-fitted model</small></div>
      </div>
    </DataComponent>
    <p className="pt-note">Pressure-to-recovery rate is the share of pressure events followed by controlled possession within {window}s, before a dead ball. Several pressures can lead to one recovery. Event data can reveal patterns consistent with traps; it cannot establish intent.</p>
    <SortableRegion id="pressing:maps" variant="freeform" className="pt-map-grid">
      <SortableItem id="pressure-map" label="Pressure locations" kind="custom"><DataComponent id="pressure-map" queryId="pressures" title="Where pressure starts" kind="custom" {...bind(rows)} description="Every located pressure in the current selection. Click a point to inspect the sequence."><PressureMap rows={rows} window={window} onSelect={choose} selected={chosen?.id}/></DataComponent></SortableItem>
      <SortableItem id="recovery-map" label="Recovery locations" kind="custom"><DataComponent id="recovery-map" queryId="pressures" title="Where possession returns" kind="custom" {...bind(gains)} description="Earliest controlled recovery in the window, deduplicated by recovery ID. Coordinates are in the pressing team's frame."><PressureMap rows={rows} recovery window={window} onSelect={choose} selected={chosen?.id}/></DataComponent></SortableItem>
    </SortableRegion>
    <section className="pt-replay-grid">
      <DataComponent id="sequence-list" queryId="pressures" title="Inspect a sequence" kind="table" {...bind(listed)} headerControls={<label className="pt-inline-label">Result<select aria-label="Sequence result" value={outcome} onChange={e=>setOutcome(e.target.value)}><option value="all">All pressures</option><option value="success">Recovered</option><option value="failure">No recovery</option></select></label>}>
        <p className="pt-note">Wide-entry candidates appear first. Passes allowed include opposition attempts in the 15s lookback and between pressure and regain.</p>
        <div className="pt-table-scroll"><table className="pt-table"><thead><tr><th>Match / player</th><th>Time</th><th>Pattern</th><th>Regain</th><th>Passes allowed</th></tr></thead><tbody>{listed.slice(page*8,page*8+8).map(r=><tr key={r.id} className={chosen?.id===r.id?'pt-selected':''}><td><button className="pt-row-button" onClick={()=>choose(r.id)}>{r.match}<small>{r.player}</small></button></td><td>{clock(r)}</td><td>{r.wide_candidate?'Wide entry':r.pass_direction}</td><td>{successful(r,window)?`${r.recovery_seconds.toFixed(1)}s`:`None ≤${window}s`}</td><td>{successful(r,window)?r.passes_allowed:'n/a'}</td></tr>)}</tbody></table></div>
        {!listed.length&&<p className="pt-empty">No sequences match these filters. Select another result or broaden the pitch region.</p>}
        <div className="pt-pagination"><span>{listed.length?`${page*8+1}–${Math.min(listed.length,page*8+8)} of ${fmt(listed.length)}`:'0 sequences'}</span><button disabled={page===0} onClick={()=>setPage(p=>p-1)}>Previous page</button><button disabled={(page+1)*8>=listed.length} onClick={()=>setPage(p=>p+1)}>Next page</button></div>
      </DataComponent>
      <DataComponent id="event-replay" queryId="pressures" title="Event replay" kind="custom" {...bind(chosen?[chosen]:[])}>
        <Replay row={chosen}/>{chosen&&<p className="pt-note">{chosen.wide_candidate?'Wide-entry candidate. ':''}{successful(chosen,window)?`Recovered after ${chosen.recovery_seconds.toFixed(1)}s. Subsequent xT ${chosen.subsequent_xt>=0?'+':''}${chosen.subsequent_xt.toFixed(3)}; shot xG ${chosen.subsequent_xg.toFixed(3)}.`:`No controlled recovery within ${window}s.`}</p>}
      </DataComponent>
    </section>
    <SortableRegion id="pressing:patterns" variant="freeform" className="pt-map-grid">
      <SortableItem id="pass-direction" label="Opposition pass direction" kind="chart"><EvidenceChart id="pass-direction" queryId="pressures" title="Pass direction before pressure" spec={directionChart} rows={direction} sourceRows={rows} scopeFilters={scope} height={230} description="Direction of the most recent completed opposition pass arriving before pressure, using the opponent's attacking frame. No preceding pass means none completed in the same possession within 15s."/></SortableItem>
      <SortableItem id="recovery-thirds" label="Recovery thirds" kind="chart"><EvidenceChart id="recovery-thirds" queryId="pressures" title="Recovery location by third" spec={zoneChart} rows={zones} sourceRows={gains} scopeFilters={scope} height={230}/></SortableItem>
    </SortableRegion>
    <section className="pt-comparison">
      <SectionHeader id="tournament-comparison-heading" title="Tournament comparison"/>
      <p className="pt-note">All matches for each team. Pitch region, channel, wide-entry filter and {window}s recovery window apply; the team and match selectors above do not. Rates are descriptive and unadjusted for opponents, game state or playing time.</p>
      <div className="pt-comparison-grid"><EvidenceChart id="team-comparison" queryId="pressures" title="Pressure-to-recovery rate by team" spec={compareChart} rows={[...comparisons].sort((a,b)=>(b.recoveryRate??-1)-(a.recoveryRate??-1))} sourceRows={comparisonRows} height={680} scopeFilters={scope.filter(f=>!['team','match'].includes(f.field))}/>
      <DataComponent id="comparison-detail" queryId="pressures" title="Counts and subsequent threat" kind="table" sourceRows={comparisonRows} displayRows={comparisons} scopeFilters={scope.filter(f=>!['team','match'].includes(f.field))}>
        <div className="pt-table-scroll"><table className="pt-table"><thead><tr><th>Team</th><th>Pressures</th><th>Successful</th><th>Regains</th><th>Mean xT</th></tr></thead><tbody>{comparisons.map(r=><tr key={r.team}><td>{r.team}</td><td>{fmt(r.pressures)}</td><td>{r.successful}</td><td>{r.recoveries}</td><td>{r.meanXt===null?'n/a':threat(r.meanXt)}</td></tr>)}</tbody></table></div>
        <p className="pt-note">Mean xT uses distinct recoveries and signed move values in the next 10 seconds. The 12×8 grid is fitted on Euro 2024; it has no independent predictive validation.</p>
      </DataComponent></div>
    </section>
    <DataComponent id="spain-analysis" queryId="pressures" title="Where does Spain actually win the ball?" kind="custom" sourceRows={spain} displayRows={spain} scopeFilters={[{field:'team',label:'Team',value:'Spain'},{field:'recoveryWindow',label:'Recovery window',value:'5s'}]}>
      <div className="pt-article"><p className="pt-note">Article draft · Spain’s full tournament · fixed five-second definition</p><p>Spain’s high press is an obvious place to look for their regains. This event-based test finds a broader picture: most controlled recoveries following a pressure arrive outside the attacking third.</p>
        <p>Across seven matches, {fmt(spain.length)} pressure events produce {fmt(spainGood.length)} successful anchors within five seconds, a {pct(spainGood.length,spain.length)} rate. Those anchors resolve to {spainGains.length} distinct regains: 58 in the middle third, 57 in the defensive third and 17 in the attacking third.</p>
        <p>The wide-entry heuristic identifies 133 pressures, of which 21 lead to a regain within five seconds (15.8%). That supplies sequences worth watching, but the raw rate is lower than Spain’s overall baseline. Different locations and game contexts prevent a fair effectiveness claim.</p>
        <p>Extend the window to ten seconds and Spain’s pressure-to-recovery rate rises to 28.3%, associated with 170 distinct regains. Only 19 are in the attacking third. The clock changes the count, and a longer window makes it easier to associate a pressure with a later, unrelated regain.</p>
        <p>To test the tactical explanation, compare successful and unsuccessful wide-entry sequences from the same match. Look for the return pass, the route inside, and the second defender’s arrival. Event data provide the shortlist; video or tracking is needed to investigate the mechanism and intent.</p>
      </div>
    </DataComponent>
    <footer className="pt-footer"><span>Data: <a href={sourceUrl} target="_blank" rel="noreferrer"><img className="pt-provider-logo" src={statsbombLogo} alt="StatsBomb"/>StatsBomb Open Data</a> · Euro 2024 · 51 matches</span><span>Source revision: 4b73468 · event data, no tracking</span></footer>
  </article>;
}
