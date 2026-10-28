'use strict';
(() => {
const $=id=>document.getElementById(id), state=$('state');
let D, clip, index=0, playing=false, last=0, accumulator=0;
const num=(x,n=4)=>Number(x).toFixed(n), signed=(x,n=4)=>(x>=0?'+':'')+num(x,n);
const text=(ctx,value,x,y,size=18,color='#202b27')=>{ctx.font=`${size}px -apple-system,BlinkMacSystemFont,Segoe UI,sans-serif`;ctx.fillStyle=color;ctx.fillText(value,x,y);};
function line(ctx,a,b,color,width=2){ctx.beginPath();ctx.moveTo(...a);ctx.lineTo(...b);ctx.strokeStyle=color;ctx.lineWidth=width;ctx.stroke();}
function circle(ctx,x,y,r,fill,stroke,width=2){ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);ctx.fillStyle=fill;ctx.fill();ctx.strokeStyle=stroke;ctx.lineWidth=width;ctx.stroke();}
function drawPitch(frame){
 const ctx=$('pitch').getContext('2d'), W=1000,H=680;ctx.clearRect(0,0,W,H);ctx.fillStyle='#204f3d';ctx.fillRect(0,0,W,H);
 const scale=Math.min(940/clip.pitch_length,600/clip.pitch_width),px=x=>W/2+x*scale,py=y=>H/2-y*scale;
 ctx.strokeStyle='#e7eee5';ctx.lineWidth=2;ctx.strokeRect(px(-clip.pitch_length/2),py(clip.pitch_width/2),clip.pitch_length*scale,clip.pitch_width*scale);
 line(ctx,[px(0),py(-clip.pitch_width/2)],[px(0),py(clip.pitch_width/2)],'#e7eee5');
 ctx.beginPath();ctx.arc(px(0),py(0),9.15*scale,0,Math.PI*2);ctx.stroke();
 for(const side of [-1,1]){const goal=side*clip.pitch_length/2;ctx.strokeRect(px(side<0?goal:goal-16.5),py(20.16),16.5*scale,40.32*scale);ctx.strokeRect(px(side<0?goal:goal-5.5),py(9.16),5.5*scale,18.32*scale);circle(ctx,px(goal-side*11),py(0),2,'#e7eee5','#e7eee5');}
 const small=$('pitch').getBoundingClientRect().width<500, radius=small?18:11;
 for(const p of frame.players){const selected=p.id===clip.player_id,x=px(p.x),y=py(p.y),fill=selected?'#ffac62':p.detected?(p.home?'#164b87':'#ffffff'):'#204f3d';circle(ctx,x,y,selected?radius+3:radius,fill,selected?'#202b27':'#ffffff',3);if(!selected&&p.home)circle(ctx,x,y,radius-2,fill,'#164b87',2);if(p.detected||selected){ctx.textAlign='center';text(ctx,String(p.number),x,y+6,small?21:16,selected||!p.home?'#202b27':'#ffffff');ctx.textAlign='left';}}
 const selected=frame.players.find(p=>p.id===clip.player_id);
 if(selected){const x=px(selected.x),y=py(selected.y);if(frame.heading!==null){const ex=x+Math.cos(frame.heading)*42,ey=y-Math.sin(frame.heading)*42;line(ctx,[x,y],[ex,ey],'#ffac62',6);line(ctx,[ex,ey],[ex-Math.cos(frame.heading-.5)*13,ey+Math.sin(frame.heading-.5)*13],'#ffac62',5);line(ctx,[ex,ey],[ex-Math.cos(frame.heading+.5)*13,ey+Math.sin(frame.heading+.5)*13],'#ffac62',5);}ctx.textAlign=x>800?'right':'left';text(ctx,clip.player_name,x+(x>800?-20:20),Math.max(65,y-18),small?26:21,'#ffffff');ctx.textAlign='left';}
 if(frame.ball)circle(ctx,px(frame.ball[0]),py(frame.ball[1]),6,'#fff','#202b27',2);
 text(ctx,`Attack ${clip.attack_sign===1?'→':'←'} · Period ${clip.period}`,32,27,23,'#ffffff');
}
function drawSkeleton(frame){
 const ctx=$('skeleton').getContext('2d');ctx.clearRect(0,0,600,680);ctx.fillStyle='#edece5';ctx.fillRect(0,0,600,680);
 text(ctx,'Player-centred 3D pose',24,38,25);const yaw=Number($('yaw').value)*Math.PI/180;
 const project=v=>{const a=Math.cos(yaw)*v[0]-Math.sin(yaw)*v[1],b=Math.sin(yaw)*v[0]+Math.cos(yaw)*v[1];return [300+a*190,370+b*65-v[2]*210];};
 const origin=project([0,0,0]);for(const [axis,v] of [['X',[.6,0,0]],['Y',[0,.6,0]],['Z',[0,0,.6]]]){const p=project(v);line(ctx,origin,p,'#69766d',2);text(ctx,axis,p[0]+7,p[1],19,'#49554f');}
 if(!frame.joints){text(ctx,'Pose missing in this frame',65,565,24);return;}
 for(const [a,b] of D.skeleton){if(frame.joints[a]&&frame.joints[b])line(ctx,project(frame.joints[a]),project(frame.joints[b]),a==='lShoulder'&&b==='rShoulder'?'#a44208':'#204f3d',a==='lShoulder'&&b==='rShoulder'?9:5);}
 for(const [name,v] of Object.entries(frame.joints)){const p=project(v);circle(ctx,...p,name.includes('Shoulder')?6:3,name.includes('Shoulder')?'#a44208':'#204f3d','#edece5',1);}
 text(ctx,`Yaw ${$('yaw').value}°`,24,647,20,'#49554f');
}
function draw(){
 const f=clip.frames[index];if(!f)return;
 $('frame').value=index;$('time').textContent=`${signed(f.t,2)} s · ${f.t<0?'before reception':'after reception'}`;
 $('pose-status').textContent=`Pose status: ${f.pose_status}. Pose frame ${f.pose_frame}; tracking frame ${f.tracking_frame}.`;
 drawPitch(f);drawSkeleton(f);
}
function stop(){playing=false;$('play').textContent='Play';}
function selectClip(){stop();clip=D.clips[Number($('clip').value)];index=0;$('frame').max=clip.frames.length-1;
 $('clip-info').textContent=`${clip.fixture} · ${clip.player_name} · event ${clip.event_id} · period ${clip.period}`;
 $('outcome').textContent=`Observed possession: ${clip.end_type.replaceAll('_',' ')}${clip.pass_outcome?' ('+clip.pass_outcome+')':''}, released after ${num(clip.duration,1)} s. Primary fast-progressive target: ${clip.target?'yes':'no'}.`;
 draw();
}
function drawIntervals(){
 const canvas=$('intervals'),small=window.innerWidth<680;canvas.width=small?600:1100;canvas.height=small?360:280;
 const ctx=canvas.getContext('2d'),rows=[D.results.primary,D.results.reverse_diagnostic];ctx.clearRect(0,0,canvas.width,canvas.height);
 let lo=Math.min(-.02,...rows.map(r=>r.delta_log_loss_95ci.low))-.006,hi=Math.max(.01,...rows.map(r=>r.delta_log_loss_95ci.high))+.006;
 const x=v=>(small?55:260)+(v-lo)/(hi-lo)*(small?490:700);
 if(small){
  line(ctx,[x(0),60],[x(0),300],'#7b827a',2);
  rows.forEach((r,i)=>{const y=105+i*145,c=r.delta_log_loss_95ci;text(ctx,i?'Reverse diagnostic':'Chronological holdout',20,y-35,25);line(ctx,[x(c.low),y],[x(c.high),y],'#204f3d',5);for(const v of [c.low,c.high])line(ctx,[x(v),y-10],[x(v),y+10],'#204f3d',3);circle(ctx,x(r.delta_log_loss),y,7,'#a44208','#a44208');text(ctx,`Change ${signed(r.delta_log_loss)}`,20,y+38,23);});
  for(const v of [lo,0,hi])text(ctx,num(v,3),x(v)-20,325,21,'#49554f');text(ctx,'Orientation minus baseline log loss',85,355,23,'#49554f');return;
 }
 line(ctx,[x(0),35],[x(0),210],'#7b827a',2);
 rows.forEach((r,i)=>{const y=80+i*83,c=r.delta_log_loss_95ci;line(ctx,[x(c.low),y],[x(c.high),y],'#204f3d',5);for(const v of [c.low,c.high])line(ctx,[x(v),y-10],[x(v),y+10],'#204f3d',3);circle(ctx,x(r.delta_log_loss),y,7,'#a44208','#a44208');text(ctx,i?'Reverse diagnostic':'Chronological holdout',12,y+6,22);text(ctx,signed(r.delta_log_loss),980,y+6,22);});
 for(const v of [lo,0,hi]){text(ctx,num(v,3),x(v)-22,235,20,'#49554f');}text(ctx,'Orientation − baseline log loss',360,274,21,'#49554f');
}
function addRow(tbody,values){const tr=document.createElement('tr');for(const value of values){const td=document.createElement('td');td.textContent=value;tr.appendChild(td);}tbody.appendChild(tr);}
function renderResults(){
 const r=D.results.primary,reverse=D.results.reverse_diagnostic;
 const bothIncludeZero=[r,reverse].every(row=>row.delta_log_loss_95ci.low<=0&&row.delta_log_loss_95ci.high>=0);
 $('finding').textContent=`Log loss ${r.orientation.log_loss<r.baseline.log_loss?'falls':'rises'} from ${num(r.baseline.log_loss)} to ${num(r.orientation.log_loss)} on ${r.baseline.n} held-out receptions. ${bothIncludeZero?'Both conditional intervals include zero. ':''}The pilot criterion is ${D.results.pilot_criterion_met?'met':'not met'}; these two matches do not establish a general benefit.`;
 for(const [name,key] of [['Training prevalence','constant'],['Position + pressure','baseline'],['Position + pressure + orientation','orientation']]){const m=r[key];addRow($('scores'),[name,num(m.log_loss),num(m.brier),num(m.auroc,3)]);}
 for(const [name,row] of [['Chronological',r],['Reverse diagnostic',reverse]]){const p=document.createElement('p');p.textContent=`${name}: Δ ${signed(row.delta_log_loss)}; conditional 95% interval [${signed(row.delta_log_loss_95ci.low)}, ${signed(row.delta_log_loss_95ci.high)}], ${row.train_n} training / ${row.baseline.n} test receptions.`;$('interval-text').appendChild(p);}
 $('coverage').textContent='Reception pose coverage after all gates: '+Object.entries(D.coverage).map(([m,c])=>`${m}: ${c.orientation_n}/${c.baseline_n} (${num(100*c.orientation_reception_coverage,1)}%)`).join('; ')+'. Off-camera and crowded receptions can be selected out.';
 const midfield=D.sensitivity.filter(x=>x.case==='midfield_only');$('midfield').textContent='Midfield-only sensitivity: '+midfield.map(x=>`held-out ${x.test_match}, Δ log loss ${signed(x.delta_log_loss)}`).join('; ')+'. Results are mixed and do not support a midfielder-specific claim.';
 for(const c of D.categories)addRow($('categories'),[c.match_id,c.category,c.n,num(c.fast_progressive_fraction*100,1)+'%',num(c.median_release_duration_s,1)+' s',signed(c.mean_vendor_epv_delta_for,4),num(c.successful_pass_or_foul_fraction_among_known*100,1)+'% ('+c.retained_proxy_n+')']);
 for(const c of D.sensitivity)addRow($('sensitivities'),[c.case.replaceAll('_',' '),c.test_match,c.status?'unavailable':`${c.train_n} / ${c.baseline.n}`,c.status||signed(c.delta_log_loss)]);
 drawIntervals();
}
function tick(now){
 if(playing){accumulator+=(now-last)/1000*Number($('speed').value);while(accumulator>=.04){accumulator-=.04;index++;if(index>=clip.frames.length){index=clip.frames.length-1;stop();break;}}draw();}last=now;requestAnimationFrame(tick);
}
try{
 D=JSON.parse($('dataset').textContent);if(!Array.isArray(D.clips)||!D.clips.length){state.textContent='No eligible clips were exported. Run the validated orientation stage and rebuild the viewer.';return;}
 D.clips.forEach((c,i)=>{const o=document.createElement('option');o.value=i;o.textContent=c.fixture+' · '+c.player_name;$('clip').appendChild(o);});
 $('workspace').hidden=false;state.textContent='';renderResults();selectClip();
 $('clip').addEventListener('change',selectClip);$('frame').addEventListener('input',()=>{stop();index=Number($('frame').value);draw();});$('yaw').addEventListener('input',draw);
 $('reception').addEventListener('click',()=>{stop();index=clip.frames.reduce((best,f,i)=>Math.abs(f.t)<Math.abs(clip.frames[best].t)?i:best,0);draw();});
 $('play').addEventListener('click',()=>{if(playing){stop();return;}if(index===clip.frames.length-1)index=0;playing=true;accumulator=0;last=performance.now();$('play').textContent='Pause';});
 window.addEventListener('resize',()=>{draw();drawIntervals();});requestAnimationFrame(tick);
}catch(err){$('workspace').hidden=true;state.textContent='The included clip data could not be read. Rebuild with python -m open_body viewer. '+err.message;console.error(err);}
})();
