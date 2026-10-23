'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const NS = 'http://www.w3.org/2000/svg';
  const RED = '#9f2936', TEAL = '#086b67', INK = '#202c2b';
  const state = {data:null, rows:[], selected:null, timer:null};
  const finite = Number.isFinite;
  const fmt = (v, digits=1, suffix='') => finite(v) ? v.toFixed(digits)+suffix : 'Unavailable';
  const clock = t => `${String(Math.floor(t/60)).padStart(2,'0')}:${String(Math.floor(t%60)).padStart(2,'0')}`;
  const el = (tag, attrs={}, text=null) => {const n=document.createElementNS(NS,tag); Object.entries(attrs).forEach(([k,v])=>n.setAttribute(k,String(v)));if(text!==null)n.textContent=text;return n;};
  const draw = (svg,tag,attrs,text) => {const n=el(tag,attrs,text);svg.append(n);return n;};
  const label = (svg,x,y,text,attrs={}) => draw(svg,'text',{x,y,'class':'chart-label',...attrs},text);
  const median = a => {const s=[...a].sort((a,b)=>a-b);return s.length ? (s[Math.floor((s.length-1)/2)]+s[Math.floor(s.length/2)])/2 : null;};
  function stop() {clearInterval(state.timer);state.timer=null;$('play').textContent='Play recorded frames';}
  function updateFilters() {
    stop();
    const team=$('team').value, half=$('half').value, attacking=$('scope').value==='attacking', corroborated=$('corroboration').value==='yes';
    state.rows=state.data.transitions.filter(r=>(!team||r.losing_team===team)&&(!half||r.period===half)&&(!attacking||r.attacking_scope)&&(!corroborated||r.event_corroborated));
    const complete=state.rows.filter(r=>!r.censored);
    $('count').textContent=state.rows.length;
    $('median').textContent=fmt(median(state.rows.map(r=>r.behind_ball)),0);
    $('advanced').textContent=`${complete.filter(r=>r.progressed_10m).length} / ${complete.length}`;
    $('shots').textContent=`${complete.filter(r=>r.shot).length} / ${complete.length}`;
    $('denominator').textContent=`Outcome rates exclude ${state.rows.length-complete.length} censored windows. Each observation ends at the first regain, dead ball, incomplete tracking, half end or ten seconds.`;
    $('empty').hidden=state.rows.length>0;$('detail').hidden=!state.rows.length;$('download').disabled=!state.rows.length;
    const options=[...state.rows].sort((a,b)=>(b.vulnerability_score??-1)-(a.vulnerability_score??-1)||a.frame-b.frame);
    const picker=$('turnover');picker.replaceChildren();
    options.forEach(r=>{const option=document.createElement('option');option.value=r.transition_id;option.textContent=`${clock(r.clock_s)} · ${r.team_name} · score ${fmt(r.vulnerability_score)} · ${r.behind_ball} behind`;picker.append(option);});
    if(options.length){picker.value=options.some(r=>r.transition_id===state.selected)?state.selected:options[0].transition_id;selectTurnover();}
    scatter(complete.filter(r=>finite(r.vulnerability_score)));
  }
  function selected() {return state.rows.find(r=>r.transition_id===state.selected);}
  function selectTurnover() {
    stop();state.selected=$('turnover').value;
    const row=selected();if(!row)return;
    $('turnover-title').textContent=`${clock(row.clock_s)} · ${row.team_name} lose control`;
    $('anchor-age').textContent=`Snapshot ${fmt(row.snapshot_age_s,2)} s before loss`;
    $('frame').value='0';$('frame').max=String(Math.max(0,row.replay.length-1));
    const metrics=[['Outfield behind ball',row.behind_ball],['Goalkeeper behind ball',row.goalkeeper_behind],['Coverage margin',(row.coverage_margin>=0?'+':'')+row.coverage_margin],['Rest structure RMS',fmt(row.compactness_rms_m,1,' m')],['Rest width / depth',`${fmt(row.rest_width_m)} / ${fmt(row.rest_depth_m)} m`],['Central cells exposed',finite(row.central_exposed_fraction)?fmt(row.central_exposed_fraction*100,0,'%'):'Unavailable'],['Clear forward corridors',`${row.open_lanes} / ${row.counter_options}`],['Mean nearest-defender distance',fmt(row.nearest_option_mean_m,1,' m')],['Maximum nearest-defender distance',fmt(row.nearest_option_max_m,1,' m')],['Fixed diagnostic score',fmt(row.vulnerability_score)+' / 100']];
    const dl=$('measurements');dl.replaceChildren();metrics.forEach(([name,value])=>{const dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=name;dd.textContent=value;dl.append(dt,dd);});
    $('outcome-title').textContent=`${fmt(row.progress_m)} m forward ball movement`;
    $('outcome-text').textContent=`Observed ${fmt(row.observed_seconds,2)} s, ending at ${row.stop_reason.replaceAll('_',' ')}. Shot: ${row.shot?'yes':'no'}. ${row.censored?'Incomplete observation; excluded from outcome rates.':'Complete bounded observation.'}`;
    $('event-note').textContent=`Event corroboration: ${row.event_corroborated?'within ±2 s':'no winning-team action within ±2 s'}. Nearest event ${row.event_id}; offset ${fmt(row.event_delta_s,2)} s. Approximate UTC shot alignments in this window: ${row.approx_shots}.`;
    timeline(row);pitch();
  }
  function pitch() {
    const row=selected();if(!row)return;
    const svg=$('pitch');svg.replaceChildren();
    const replay=$('view').value==='replay';$('replay-controls').hidden=!replay;$('overlays').disabled=replay;
    const frame=replay?row.replay[Number($('frame').value)]:null;
    const ball=frame?frame.ball:[row.ball_x,row.ball_y];const players=frame?frame.players:row.snapshot;
    $('frame-time').textContent=frame?`${frame.time>=0?'+':''}${frame.time.toFixed(2)} s`:'';
    draw(svg,'title',{},replay?`Recorded player positions ${frame.time.toFixed(2)} seconds from turnover`:`Pre-loss structure ${row.snapshot_age_s.toFixed(2)} seconds before turnover`);
    const L=state.data.metadata.length,W=state.data.metadata.width;
    draw(svg,'rect',{x:-L/2,y:-W/2,width:L,height:W,fill:'none',stroke:'#67736c','stroke-width':.2});
    draw(svg,'line',{x1:0,y1:-W/2,x2:0,y2:W/2,stroke:'#67736c','stroke-width':.2});
    draw(svg,'circle',{cx:0,cy:0,r:9.15,fill:'none',stroke:'#67736c','stroke-width':.2});
    for(const side of [-1,1]){
      draw(svg,'rect',{x:side<0?-L/2:L/2-16.5,y:-20.16,width:16.5,height:40.32,fill:'none',stroke:'#67736c','stroke-width':.2});
      draw(svg,'rect',{x:side<0?-L/2:L/2-5.5,y:-9.16,width:5.5,height:18.32,fill:'none',stroke:'#67736c','stroke-width':.2});
      draw(svg,'circle',{cx:side*(L/2-11),cy:0,r:.25,fill:'#67736c'});
    }
    if(!replay&&$('overlays').checked){
      draw(svg,'line',{x1:ball[0],y1:-W/2,x2:ball[0],y2:W/2,stroke:INK,'stroke-width':.22,'stroke-dasharray':'1 1'});
      row.overlay.central.forEach(([x,y])=>{draw(svg,'path',{d:`M${x-.3},${-y-.3}l.6,.6m0,-.6l-.6,.6`,stroke:'#786f60','stroke-width':.18,opacity:.7});});
      row.overlay.lanes.forEach(([x,y])=>draw(svg,'line',{x1:ball[0],y1:-ball[1],x2:x,y2:-y,stroke:TEAL,'stroke-width':.45,'stroke-dasharray':'.6 .7'}));
    }
    players.forEach(([id,x,y])=>{
      const p=state.data.metadata.players[id];const losing=p.team===row.losing_team;const color=losing?RED:TEAL;
      const mark=losing?draw(svg,'circle',{cx:x,cy:-y,r:1.5,fill:color,stroke:'white','stroke-width':.18}):draw(svg,'path',{d:`M${x},${-y-1.9}l1.8,3.1h-3.6Z`,fill:color,stroke:'white','stroke-width':.18});
      mark.append(el('title',{},`${p.name}, #${p.number}, ${losing?'losing team':'counterattacking team'}`));
      if(p.is_gk)draw(svg,'rect',{x:x-2,y:-y-2,width:4,height:4,fill:'none',stroke:color,'stroke-width':.25});
      draw(svg,'text',{x,y:-y+.5,'text-anchor':'middle',fill:'white','font-family':'system-ui','font-size':1.45,'font-weight':700},p.number);
    });
    draw(svg,'circle',{cx:ball[0],cy:-ball[1],r:.8,fill:INK,stroke:'white','stroke-width':.25});
    draw(svg,'text',{x:-L/2,y:W/2+6,fill:INK,'font-size':2,'font-family':'system-ui'},`${replay?'Recorded frame':'Pre-loss snapshot'} · Losing team attacked right →`);
  }
  function timeline(row) {
    const svg=$('timeline');svg.replaceChildren();
    const low=Math.min(-5,...row.timeline.map(p=>p[1])),high=Math.max(15,...row.timeline.map(p=>p[1]));
    const x=t=>45+t/10*495,y=v=>190-(v-low)/(high-low)*165;
    [0,2,4,6,8,10].forEach(t=>{draw(svg,'line',{x1:x(t),y1:190,x2:x(t),y2:194,stroke:'#7c8981'});label(svg,x(t),212,t,{'text-anchor':'middle'});});
    [0,10,Math.ceil(high/10)*10].forEach(v=>{if(v>high)return;draw(svg,'line',{x1:45,y1:y(v),x2:540,y2:y(v),stroke:'#c3c9c0','stroke-dasharray':v===10?'3 3':'none'});label(svg,36,y(v)+4,v,{'text-anchor':'end'});});
    draw(svg,'polyline',{points:row.timeline.map(([t,v])=>`${x(t)},${y(v)}`).join(' '),fill:'none',stroke:TEAL,'stroke-width':2});
    label(svg,290,237,'Seconds since turnover',{'text-anchor':'middle'});label(svg,45,16,'Forward ball displacement (m)');
  }
  function scatter(rows) {
    const svg=$('scatter');svg.replaceChildren();const max=Math.max(20,...rows.map(r=>r.progress_m));
    const x=v=>60+v/100*810,y=v=>285-v/max*250;
    [0,20,40,60,80,100].forEach(v=>{label(svg,x(v),305,v,{'text-anchor':'middle'});});
    for(let v=0;v<=max;v+=20){draw(svg,'line',{x1:60,y1:y(v),x2:870,y2:y(v),stroke:'#d4d9d0'});label(svg,48,y(v)+4,v,{'text-anchor':'end'});}
    label(svg,470,336,'Pre-loss diagnostic score (0–100)',{'text-anchor':'middle'});label(svg,60,17,'Maximum forward ball displacement (m)');
    rows.forEach(r=>{
      const color=state.data.metadata.teams[r.losing_team].role==='home'?RED:TEAL;
      const attrs={fill:color,opacity:.8,tabindex:0,role:'button','class':'point','aria-label':`${clock(r.clock_s)} ${r.team_name}: score ${fmt(r.vulnerability_score)}, ball moved ${fmt(r.progress_m)} m${r.shot?', shot followed':''}`};
      const n=r.shot?draw(svg,'rect',{...attrs,x:x(r.vulnerability_score)-4,y:y(r.progress_m)-4,width:8,height:8}):draw(svg,'circle',{...attrs,cx:x(r.vulnerability_score),cy:y(r.progress_m),r:3.5});
      const describe=()=>{$('point-detail').textContent=n.getAttribute('aria-label')+'. Select to inspect the pre-loss structure.';};
      n.addEventListener('mouseenter',describe);n.addEventListener('focus',describe);
      const choose=()=>{$('turnover').value=r.transition_id;selectTurnover();$('turnover-title').scrollIntoView({behavior:'auto',block:'start'});};
      n.addEventListener('click',choose);n.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();choose();}});
    });
  }
  function download() {
    const fields=Object.keys(state.data.transitions[0]).filter(k=>!['overlay','snapshot','replay','timeline'].includes(k));
    const escape=v=>`"${String(v??'').replaceAll('"','""')}"`;
    const csv=[fields.join(','),...state.rows.map(r=>fields.map(k=>escape(r[k])).join(','))].join('\n')+'\n';
    const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download='rest-defence-selected.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  async function start() {
    try {
      const receipt=await fetch('release.json');if(!receipt.ok)throw new Error('Release manifest unavailable');const release=await receipt.json();
      const response=await fetch(release.snapshot);if(!response.ok)throw new Error('Snapshot download failed');
      if(!('DecompressionStream' in window))throw new Error('This browser needs gzip DecompressionStream support');
      const bytes=await new Response(response.body.pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
      const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),b=>b.toString(16).padStart(2,'0')).join('');
      if(hash!==release.sha256)throw new Error('Snapshot integrity mismatch');
      state.data=JSON.parse(new TextDecoder().decode(bytes));
      if(state.data.schema_version!==1||state.data.transitions.length!==293)throw new Error('Unexpected reviewed snapshot');
      $('match').textContent=state.data.metadata.title.replace(':',' vs ')+' · One complete historical match · 293 independently checked turnovers';
      Object.entries(state.data.metadata.teams).forEach(([id,team])=>{const o=document.createElement('option');o.value=id;o.textContent=team.name;$('team').append(o);});
      for(const id of ['team','half','scope','corroboration'])$(id).addEventListener('change',updateFilters);
      $('reset').addEventListener('click',()=>{for(const id of ['team','half','corroboration'])$(id).value='';$('scope').value='attacking';updateFilters();});
      $('turnover').addEventListener('change',selectTurnover);$('view').addEventListener('change',()=>{stop();pitch();});$('overlays').addEventListener('change',pitch);
      $('frame').addEventListener('input',()=>{stop();pitch();});$('download').addEventListener('click',download);
      $('play').addEventListener('click',()=>{if(state.timer){stop();return;}if(Number($('frame').value)>=Number($('frame').max))$('frame').value='0';$('play').textContent='Pause';state.timer=setInterval(()=>{const n=Number($('frame').value)+1;if(n>Number($('frame').max)){stop();return;}$('frame').value=String(n);pitch();},200);});
      $('status').hidden=true;$('application').hidden=false;updateFilters();
    } catch(error){$('status').textContent=`Could not load the verified analysis: ${error.message}. Reload over HTTPS or a local HTTP server, or download the project from GitHub to use the Python app.`;$('status').setAttribute('role','alert');}
  }
  start();
})();
