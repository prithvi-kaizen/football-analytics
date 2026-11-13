const horizon=document.getElementById('horizon');const tournament=document.getElementById('tournament');
const pct=(n,d)=>(100*n/d).toFixed(1)+'%';
fetch('data.json').then(r=>{if(!r.ok)throw Error('Data unavailable');return r.json()}).then(data=>{
 const windows=['10','15','20','30'];
 function render(){const h=windows[Number(horizon.value)],s=data.summary[h][tournament.value],f=data.flow[h][tournament.value],n=s.corners;
  document.getElementById('horizonValue').textContent=h+' seconds';
  for(const [id,key] of [['recovery','recovered'],['shot','second_shots'],['box','second_box_entries']])document.getElementById(id).textContent=pct(s.outcomes[key].count,n);
  document.getElementById('recoveryCI').textContent=`${s.outcomes.recovered.count}/${n} corners · match bootstrap 95%: ${pct(s.outcomes.recovered.match_bootstrap_95[0]*n,n)}–${pct(s.outcomes.recovered.match_bootstrap_95[1]*n,n)}`;
  document.getElementById('shotCI').textContent=`${s.outcomes.second_shots.count}/${n} corners · match bootstrap 95%: ${pct(s.outcomes.second_shots.match_bootstrap_95[0]*n,n)}–${pct(s.outcomes.second_shots.match_bootstrap_95[1]*n,n)}`;
  const flowRows=[['All corners',n,''],['Defensive contact',f.contact,'child'],['Attacking recovery after contact',f.contact_recovered,'grandchild'],['No observed recovery after contact',f.contact_no_recovery,'grandchild'],['No defensive contact',f.no_contact,'child']];
  document.getElementById('flow').innerHTML=flowRows.map(([label,count,cls])=>`<div class="flow-row ${cls}"><span>${label}</span><strong>${count} · ${pct(count,n)}</strong><div class="bar"><span class="fill" style="width:${100*count/n}%"></span></div></div>`).join('')+`<p class="footnote">Among ${f.contact_recovered} observed recoveries, ${f.recovered_shot} led to a second-phase shot (${pct(f.recovered_shot,f.contact_recovered)}). A later defensive control can follow a recovery; these are event-order branches, not final possession shares.</p>`;
  const shots=[['First-ball shots',s.shots.immediate],['Unopposed continuation shots',s.shots.unopposed_continuation],['Recovered second-phase shots',s.shots.recovered_second_phase],['Phase unknown: simultaneous events',s.shots.ambiguous_phase]],max=Math.max(...shots.map(x=>x[1]));
  document.getElementById('shots').innerHTML=shots.map(([label,count])=>`<div class="shotbar"><div class="label"><span>${label}</span><strong>${count}</strong></div><div class="bar"><span class="fill" style="width:${100*count/max}%"></span></div></div>`).join('');
  document.getElementById('xgNote').textContent=`Known-phase shot xG: first ball ${s.shot_xg.immediate_xg.toFixed(2)}, unopposed continuation ${s.shot_xg.continuation_xg.toFixed(2)}, recovered second phase ${s.shot_xg.second_xg.toFixed(2)}. Phase-unknown shots are excluded from this comparison.`;
 }
 document.getElementById('examples').innerHTML=data.examples.map(e=>`<article class="example"><small>${e.match} · ${e.date} · ${e.minute}'</small><h3>${e.title}</h3><p>${e.note}</p><div class="stages">${e.phases.map(p=>`<span class="stage">${p.label}${p.t===null?'':` +${p.t.toFixed(2)}s`}</span>`).join('')}</div><small>Observed endpoint within 15s: ${e.outcome}</small></article>`).join('');
 horizon.addEventListener('input',render);tournament.addEventListener('change',render);render();
}).catch(e=>{document.getElementById('flow').textContent='Could not load the verified aggregate results.';console.error(e)});
