'use strict';
const byId = id => document.getElementById(id);
const num = (v, digits=1) => v == null ? 'Withheld' : Number(v).toFixed(digits);
const probability = p => p == null ? 'Withheld' : p >= .9995 ? '>99.9%' : p < .0005 ? '<0.1%' : `${(p*100).toFixed(1)}%`;
let data, currentCase;
function option(value, label) { const el=document.createElement('option'); el.value=value; el.textContent=label; return el; }
function cell(value) { const el=document.createElement('td'); el.textContent=value; return el; }
function view(name) {
 document.querySelectorAll('.view').forEach(el=>el.hidden=el.id!==name);
 document.querySelectorAll('nav button').forEach(el=>el.setAttribute('aria-pressed', String(el.dataset.view===name)));
}
function target() {
 const chosen=currentCase.targets.find(t=>t.id===byId('target').value);
 byId('pitch').src=chosen.figure;
 byId('pitch').alt=`${currentCase.match}, ${currentCase.clock}, ${currentCase.player}. Recorded pass and anonymous visible teammates; ${chosen.id} highlighted as a hypothetical target.`;
 byId('target-title').textContent=chosen.id+(chosen.proxyChosen?' · inferred chosen receiver':' · hypothetical receiver');
 byId('target-probability').textContent=probability(chosen.probability);
 byId('target-gain').textContent=`Forward gain ${chosen.forwardGain>=0?'+':''}${num(chosen.forwardGain)} units. Expected positive gain: ${num(chosen.expectedGain)}.`;
 byId('target-note').textContent=chosen.withholdingReasons ? `Probability withheld: ${chosen.withholdingReasons}.` : `${chosen.flagged?'Meets the fixed exploratory review rules. ':'Within the marginal training-range guards. '}This is an experimental estimate, not a validated counterfactual.`;
 document.querySelectorAll('#candidate-table tbody tr').forEach(row=>row.classList.toggle('selected',row.dataset.target===chosen.id));
}
function renderCase() {
 currentCase=data.cases.find(c=>c.id===byId('case').value);
 byId('decision-title').textContent=`${currentCase.clock} · ${currentCase.player}`;
 byId('decision-meta').textContent=`${currentCase.match} · ${currentCase.date} · period ${currentCase.period} · possession ${currentCase.possession} · actual pass ${currentCase.completed?'completed':'not completed'}. Inferred chosen receiver: ${currentCase.proxyTarget}.`;
 byId('source-event').href=`https://github.com/hudl/open-data/blob/${data.revision}/data/events/${currentCase.matchId}.json`;
 byId('target').replaceChildren(...currentCase.targets.map(t=>option(t.id,t.id+(t.proxyChosen?' · inferred chosen':t.flagged?' · review flag':''))));
 const body=byId('candidate-table').querySelector('tbody'); body.replaceChildren();
 for(const t of currentCase.targets) {
  const row=document.createElement('tr'); row.dataset.target=t.id;
  [t.id,t.proxyChosen?'Yes':'',`${t.forwardGain>=0?'+':''}${num(t.forwardGain)}`,num(t.distance),t.laneClearance==null?'Unobserved':num(t.laneClearance),probability(t.probability),num(t.expectedGain),t.flagged?'Yes':''].forEach(v=>row.append(cell(v)));
  body.append(row);
 }
 target();
 const state=new URLSearchParams(location.hash.slice(1)); state.set('case',currentCase.id);
 history.replaceState(null,'',`#${state}`);
}
function casesForTournament(preferred) {
 const cases=data.cases.filter(c=>c.tournament===byId('tournament').value);
 byId('case').replaceChildren(...cases.map(c=>option(c.id,`${c.match} · ${c.clock}`)));
 if(cases.some(c=>c.id===preferred)) byId('case').value=preferred;
 byId('selection-note').textContent=`${cases.length} published cases in this tournament. Six distinct held-out matches; first chronological flagged event per match.`;
 renderCase();
}
function metrics() {
 const body=byId('metrics-table').querySelector('tbody'); body.replaceChildren();
 for(const m of data.metrics.filter(m=>m.population===byId('population').value)) {
  const row=document.createElement('tr');
  const ci=m.log_loss_ci_low==null?'Unavailable':`${num(m.log_loss_ci_low,3)}–${num(m.log_loss_ci_high,3)}`;
  [m.estimator,m.features,Number(m.train_n).toLocaleString(),Number(m.n).toLocaleString(),num(m.log_loss,4),ci,num(m.brier,4),num(m.roc_auc,3)].forEach(v=>row.append(cell(v)));
  body.append(row);
 }
}
async function init() {
 try {
  const response=await fetch('analysis.json'); if(!response.ok) throw new Error(`Analysis unavailable (${response.status})`);
  data=await response.json(); if(data.schemaVersion!==1 || data.cases.length!==12) throw new Error('Unrecognized release');
  byId('matches').textContent=data.summary.matches;
  byId('passes').textContent=data.summary.eligible_passes.toLocaleString();
  byId('holdout').textContent=data.testMatches;
  byId('coverage').textContent=`${(100*data.summary.recipient_proxies/data.summary.frames_with_defenders).toFixed(1)}%`;
  byId('case-method').textContent=data.caseSelection;
  byId('revision').textContent=data.revision;
  const initial=new URLSearchParams(location.hash.slice(1)).get('case'); const preferred=data.cases.find(c=>c.id===initial);
  byId('tournament').replaceChildren(...[...new Set(data.cases.map(c=>c.tournament))].map(t=>option(t,t)));
  if(preferred) byId('tournament').value=preferred.tournament;
  byId('tournament').addEventListener('change',()=>casesForTournament());
  byId('case').addEventListener('change',renderCase); byId('target').addEventListener('change',target);
  byId('population').addEventListener('change',metrics);
  document.querySelectorAll('nav button').forEach(b=>b.addEventListener('click',()=>view(b.dataset.view)));
  casesForTournament(initial); metrics(); byId('loading').hidden=true; view('lab');
 } catch(error) { byId('loading').hidden=true; byId('error').hidden=false; byId('error').textContent=`The reviewed analysis could not load. ${error.message}. Please reload or use the source repository.`; }
}
init();
