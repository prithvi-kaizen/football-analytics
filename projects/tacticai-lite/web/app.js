'use strict';
const $=id=>document.getElementById(id);
const percent=value=>(100*value).toFixed(1)+'%';
const shortName=value=>value.startsWith("Men's")?'Men':'Women';
let data=null,current=[];
function node(tag,text,className){const element=document.createElement(tag);if(text!==undefined)element.textContent=text;if(className)element.className=className;return element;}
function cell(row,text,header=false){row.append(node(header?'th':'td',String(text)));}
function svgNode(tag,attrs){const element=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const [key,value] of Object.entries(attrs))element.setAttribute(key,value);return element;}
function svgLine(svg,x1,y1,x2,y2,color,width=1){svg.append(svgNode('line',{x1,y1,x2,y2,stroke:color,'stroke-width':width}));}
function filteredRows(){const group=$('dimension').value,query=$('search').value.trim().toLowerCase();const minimum=Math.max(1,Number($('minimum').value)||1);return data[group].filter(r=>($('tournament').value==='all'||r.tournament===$('tournament').value)&&r.corners>=minimum&&String(r[group==='delivery'?'delivery':'cluster']).toLowerCase().includes(query));}
function render(){
  current=filteredRows();const dimension=$('dimension').value,key=dimension==='delivery'?'delivery':'cluster';
  const labels=[...new Set(current.map(r=>r[key]))];const count=current.reduce((sum,r)=>sum+r.corners,0),shots=current.reduce((sum,r)=>sum+r.shots_created,0);
  $('scope').textContent=`${count} observed pass-corners · ${shots} produced a shot · ${labels.length} pattern${labels.length===1?'':'s'} in view. Direct shots excluded (4 in the full dataset).`;
  $('cluster-note').hidden=dimension!=='clusters';
  $('chart').replaceChildren();$('rates').replaceChildren();$('download').disabled=!current.length;
  if(!current.length){$('chart').append(node('p','No patterns match these filters. Clear the search or lower the minimum corner count.','empty'));return;}
  const legend=node('div',undefined,'legend');
  for(const tournament of [...new Set(current.map(r=>r.tournament))]){const item=node('span');item.append(node('i',undefined,'key'+(shortName(tournament)==='Women'?' women':'')),node('span',tournament));legend.append(item);}
  $('chart').append(legend);
  const axis=node('div',undefined,'axis');axis.append(node('span'));const ticks=node('div',undefined,'axis-ticks');for(const value of [0,25,50,75,100])ticks.append(node('span',value+'%'));axis.append(ticks,node('span','Shots / corners','counts-label'));$('chart').append(axis);
  for(const label of labels){
    const rows=current.filter(r=>r[key]===label);const row=node('div',undefined,'pattern');row.append(node('div',label,'pattern-label'));
    const plot=node('div',undefined,'pattern-chart');plot._rows=rows;plot.dataset.pattern=label;row.append(plot);
    const counts=node('div',undefined,'pattern-counts');for(const r of rows)counts.append(node('div',`${shortName(r.tournament)}: ${r.shots_created}/${r.corners} (${percent(r.rate)})`));row.append(counts);$('chart').append(row);
  }
  for(const r of current){const row=node('tr');for(const value of [r.tournament,r[key],r.shots_created,r.corners,percent(r.rate),percent(r.low)+' to '+percent(r.high)])cell(row,value);$('rates').append(row);}
  drawCharts();
}
function drawCharts(){for(const plot of document.querySelectorAll('.pattern-chart')){
  const rows=plot._rows,width=Math.max(100,Math.round(plot.getBoundingClientRect().width)),height=Math.max(54,rows.length*34+14),x=value=>16+value*(width-32);
  const svg=svgNode('svg',{viewBox:`0 0 ${width} ${height}`,width,height,role:'img','aria-label':plot.dataset.pattern+': '+rows.map(r=>`${r.tournament}, ${percent(r.rate)}, ${r.shots_created} of ${r.corners} corners; interval ${percent(r.low)} to ${percent(r.high)}`).join('. ')});
  for(const value of [0,.25,.5,.75,1])svgLine(svg,x(value),0,x(value),height,'#d9ddd7');
  rows.forEach((r,i)=>{const y=24+i*34,color=shortName(r.tournament)==='Women'?'#915c12':'#176044';svgLine(svg,x(r.low),y,x(r.high),y,color,2);svgLine(svg,x(r.low),y-4,x(r.low),y+4,color,2);svgLine(svg,x(r.high),y-4,x(r.high),y+4,color,2);
    const point=shortName(r.tournament)==='Women'?svgNode('path',{d:`M ${x(r.rate)} ${y-6} L ${x(r.rate)+6} ${y} L ${x(r.rate)} ${y+6} L ${x(r.rate)-6} ${y} Z`,fill:color}):svgNode('circle',{cx:x(r.rate),cy:y,r:5,fill:color});svg.append(point);});
  plot.replaceChildren(svg);
}}
function download(){if(!current.length)return;const key=$('dimension').value==='delivery'?'delivery':'cluster',columns=['tournament',key,'corners','shots_created','rate','low','high'];const quote=value=>'"'+String(value).replaceAll('"','""')+'"';const csv=[columns.join(','),...current.map(r=>columns.map(c=>quote(r[c])).join(','))].join('\r\n')+'\r\n';const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));const anchor=node('a');anchor.href=url;anchor.download='tacticai-lite-aggregate-summary.csv';document.body.append(anchor);anchor.click();anchor.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
async function start(){try{
  const response=await fetch('data.json');if(!response.ok)throw new Error('Release data could not be loaded.');data=await response.json();
  if(data.schema_version!==1||!Array.isArray(data.delivery)||!data.inventory.length)throw new Error('The aggregate release has an unsupported format.');
  const corners=data.inventory.reduce((sum,r)=>sum+r.corners,0),matches=data.inventory.reduce((sum,r)=>sum+r.matches,0),frames=data.inventory.reduce((sum,r)=>sum+r.frames,0);
  $('inventory').replaceChildren();for(const [label,value] of [['Dataset',`${matches} matches · ${corners} corners`],['Linked 360 frames',`${frames}/${corners} (${percent(frames/corners)})`],['Scope','Euro 2024 + Women’s Euro 2025']])$('inventory').append(node('dt',label),node('dd',value));
  for(const item of data.inventory){const option=node('option',item.tournament);option.value=item.tournament;$('tournament').append(option);}
  $('split').textContent=`${data.split.train_matches} training matches (${data.model.train_corners} corners), ${data.split.test_matches} different holdout matches (${data.model.test_corners} corners). Frame features only; preprocessing fitted on training data.`;
  for(const [label,metrics] of Object.entries(data.model.metrics)){const row=node('tr');for(const value of [label==='constant'?'Constant training rate':'Logistic regression',metrics.brier.toFixed(4),metrics.log_loss.toFixed(4),metrics.roc_auc===null?'Unavailable':metrics.roc_auc.toFixed(4)])cell(row,value);$('models').append(row);}
  $('model-finding').textContent='Logistic regression '+(data.model.metrics.logistic.brier<data.model.metrics.constant.brier?'improved':'did not improve')+' Brier score over the constant baseline on this split. One fixed holdout is exploratory; visibility selection and team overlap across matches limit generalization.';
  for(const item of data.inventory){const row=node('tr');cell(row,item.tournament);for(const seconds of [10,15,20]){const value=data.sensitivity.find(r=>r.tournament===item.tournament&&r.horizon_seconds===seconds);cell(row,percent(value.rate)+` (${value.shot_created}/${value.corners})`);}$('sensitivity').append(row);}
  $('audit').textContent=`Reconciled ${data.audit.corners_checked} corner labels and shot counts against the source events: ${data.audit.mismatches} mismatches. Source revision ${data.source_revision.slice(0,12)}. This check is not video adjudication.`;
  $('status').textContent='';$('analysis').hidden=false;render();
  $('filters').addEventListener('input',render);$('filters').addEventListener('change',render);$('filters').addEventListener('submit',event=>event.preventDefault());$('filters').addEventListener('reset',()=>requestAnimationFrame(render));$('download').addEventListener('click',download);
  new ResizeObserver(drawCharts).observe($('chart'));
}catch(error){$('status').textContent='Could not load the reviewed findings. Reload the page; if the problem continues, use the linked GitHub report. '+error.message;$('status').setAttribute('role','alert');}}
start();
