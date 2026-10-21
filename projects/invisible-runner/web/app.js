"use strict";
(() => {
  const $ = id => document.getElementById(id);
  const colors = {paper:"#faf8f1", ink:"#172b29", teal:"#12675c", rust:"#934323", muted:"#46554f"};
  const plotConfig = {displayModeBar:false, responsive:true};
  let data, release, currentRuns=[], selected=null, timer=null, frameIndex=0;
  const finite = n => typeof n === "number" && Number.isFinite(n);
  const number = (n, unit="", signed=false) => finite(n) ? `${signed && n>=0?"+":""}${n.toFixed(1)}${unit}` : "Unavailable";
  const percent = n => finite(n) ? `${Math.round(n*100)}%` : "Unavailable";
  const clock = n => `${String(Math.floor(n/60)).padStart(2,"0")}:${(n%60).toFixed(1).padStart(4,"0")}`;
  const safe = text => String(text).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;");
  const baseLayout = () => ({paper_bgcolor:colors.paper, plot_bgcolor:colors.paper,
    font:{family:"Arial, sans-serif",color:colors.ink,size:12}, margin:{l:45,r:12,t:15,b:45}});
  const filters = () => ({profile:$("profile").value,team:$("team").value,kind:$("kind").value,
    quality:$("quality").value,min_distance_m:Number($("distance").value)});

  function pause() { if(timer!==null) clearTimeout(timer); timer=null; $("play").textContent="Play run"; }
  function option(value,label) { const el=document.createElement("option"); el.value=value; el.textContent=label; return el; }
  function saveFile(text,name,type) {
    const url=URL.createObjectURL(new Blob([text],{type})); const link=document.createElement("a");
    link.href=url; link.download=name; document.body.append(link); link.click(); link.remove();
    setTimeout(()=>URL.revokeObjectURL(url),1000);
  }

  function updateFilters() {
    if(!$("distance").checkValidity()) { $("distance").reportValidity(); return; }
    pause(); const f=filters();
    currentRuns=data.profiles[f.profile].runs.filter(r =>
      r.distance_m>=f.min_distance_m && (f.team==="all" || String(r.team_id)===f.team) &&
      (f.kind==="all" || r[f.kind]===true) &&
      (f.quality==="all" || r.runner_detected_fraction===1) &&
      (f.quality!=="context" || (r.context_endpoint_detected_fraction===1 && r.ball_endpoint_detected===true)));
    const valid=currentRuns.filter(r=>finite(r.free_area_delta_m2));
    $("population").replaceChildren(); const strong=document.createElement("strong");
    strong.textContent=`${currentRuns.length} ${currentRuns.length===1?"run":"runs"}`;
    $("population").append(strong,` · ${valid.length} with space estimates · ≥${f.profile} m/s · ≥${f.min_distance_m} m`);
    $("empty").hidden=currentRuns.length>0; $("details-view").hidden=currentRuns.length===0;
    $("run").replaceChildren(...currentRuns.map(r=>option(r.run_id,`${r.player_name} · ${clock(r.start_clock_s)} · ${r.distance_m.toFixed(1)} m`)));
    if(currentRuns.length) {
      if(selected && currentRuns.some(r=>r.run_id===selected.run_id)) $("run").value=selected.run_id;
      chooseRun(); drawScatter(valid);
      if($("records").open) drawRecords();
    }
  }

  function chooseRun() {
    pause(); selected=currentRuns.find(r=>r.run_id===$("run").value); frameIndex=0;
    if(!selected) return;
    $("run-title").textContent=selected.player_name;
    $("run-facts").textContent=`${clock(selected.start_clock_s)} · ${number(selected.duration_s," s")} · ${number(selected.distance_m," m")}`;
    $("teammate").textContent=selected.teammate_name || "No eligible teammate";
    $("metrics").replaceChildren();
    const metrics=[["Free patch at start",number(selected.free_area_start_m2," m²")],
      ["Free patch at end",number(selected.free_area_end_m2," m²")],
      ["Patch change",number(selected.free_area_delta_m2," m²",true)],
      ["Runner separation change",number(selected.runner_separation_delta_m," m",true)],
      ["Nearby defenders",finite(selected.nearby_defender_count)?String(selected.nearby_defender_count):"Unavailable"],
      ["Mean defender displacement",number(selected.defender_displacement_m," m")]];
    for(const [label,value] of metrics) { const dt=document.createElement("dt"),dd=document.createElement("dd"); dt.textContent=label; dd.textContent=value; $("metrics").append(dt,dd); }
    $("visibility").textContent=`Runner detected: ${percent(selected.runner_detected_fraction)}. Context players detected at endpoints: ${percent(selected.context_endpoint_detected_fraction)}. Ball detected at both endpoints: ${selected.ball_endpoint_detected?"yes":"no"}.`;
    $("frame").max=String(selected.replay.length-1); $("frame").value="0";
    const layout=baseLayout(); layout.xaxis={title:{text:"Elapsed run time (s)"},fixedrange:true};
    layout.yaxis={title:{text:"Free patch (m²)"},rangemode:"tozero",fixedrange:true}; layout.margin={l:45,r:5,t:10,b:45};
    Plotly.react($("timeline"),[{x:selected.replay.map(f=>f.elapsed_s),y:selected.replay.map(f=>f.free_area_m2),
      mode:"lines+markers",line:{color:colors.teal,width:2},marker:{size:5},connectgaps:false,
      hovertemplate:"%{x:.1f} s · %{y:.0f} m²<extra></extra>"}],layout,plotConfig);
    drawFrame();
  }

  function drawFrame() {
    const f=selected.replay[frameIndex], m=data.metadata;
    $("frame").value=String(frameIndex);
    $("frame").setAttribute("aria-valuetext",`Frame ${f.frame}, ${f.elapsed_s.toFixed(1)} seconds into run`);
    $("time").textContent=`${f.elapsed_s.toFixed(1)} / ${selected.duration_s.toFixed(1)} s`;
    const traces=[];
    for(const [key,color,opacity] of [["stable",colors.teal,.16],["gained",colors.teal,.55],["lost",colors.rust,.45]]) {
      traces.push({x:f[key].map(p=>p[0]),y:f[key].map(p=>p[1]),mode:"markers",marker:{symbol:"square",size:7,color,opacity},hoverinfo:"skip"});
    }
    const path=selected.replay.slice(0,frameIndex+1).map(s=>s.players.find(p=>p[0]===selected.player_id)).filter(Boolean);
    traces.push({x:path.map(p=>p[1]),y:path.map(p=>p[2]),mode:"lines",line:{color:colors.ink,width:3},hoverinfo:"skip"});
    for(const team of [m.home_team.id,m.away_team.id]) for(const detected of [true,false]) {
      const players=f.players.filter(p=>m.players[p[0]].team_id===team && p[3]===detected);
      traces.push({x:players.map(p=>p[1]),y:players.map(p=>p[2]),mode:"markers",
        marker:{size:12,color:team===selected.team_id?colors.teal:colors.rust,symbol:detected?"circle":"circle-open",line:{width:2}},
        text:players.map(p=>`${safe(m.players[p[0]].short_name)} · ${detected?"detected":"extrapolated"}`),hovertemplate:"%{text}<extra></extra>"});
    }
    for(const [id,symbol,label] of [[selected.player_id,"star","Runner"],[selected.teammate_id,"diamond-open","Selected teammate"]]) {
      const p=f.players.find(p=>p[0]===id);
      traces.push({x:p?[p[1]]:[],y:p?[p[2]]:[],mode:"markers",marker:{size:22,symbol,color:colors.ink,line:{width:2}},
        text:p?`${label}: ${safe(m.players[id].short_name)}`:"",hovertemplate:"%{text}<extra></extra>"});
    }
    traces.push({x:[f.ball[0]],y:[f.ball[1]],mode:"markers",marker:{size:7,color:colors.ink,symbol:f.ball[2]?"circle":"circle-open"},hovertemplate:"Ball<extra></extra>"});
    traces.forEach(t=>t.showlegend=false);
    const length=m.pitch_length,width=m.pitch_width;
    const shapes=[{type:"rect",x0:-length/2,x1:length/2,y0:-width/2,y1:width/2},
      {type:"line",x0:0,x1:0,y0:-width/2,y1:width/2},{type:"circle",x0:-9.15,x1:9.15,y0:-9.15,y1:9.15}];
    for(const sign of [-1,1]) for(const [depth,halfWidth] of [[16.5,20.16],[5.5,9.16]])
      shapes.push({type:"rect",x0:sign*length/2,x1:sign*(length/2-depth),y0:-halfWidth,y1:halfWidth});
    shapes.forEach(s=>{s.line={color:"#77847d",width:1}; s.layer="below";});
    let direction=m.home_team_side[selected.period-1];
    if(selected.team_id!==m.home_team.id) direction=direction==="left_to_right"?"right_to_left":"left_to_right";
    const layout=baseLayout(); Object.assign(layout,{margin:{l:5,r:5,t:35,b:5},showlegend:false,dragmode:false,shapes,
      title:{text:`Frame ${f.frame} · attacking ${direction==="left_to_right"?"right":"left"} · free patch ${number(f.free_area_m2," m²")}`,font:{size:12},x:0},
      xaxis:{range:[-length/2-3,length/2+3],visible:false,fixedrange:true},
      yaxis:{range:[-width/2-3,width/2+3],visible:false,fixedrange:true,scaleanchor:"x",scaleratio:1}});
    Plotly.react($("pitch"),traces,layout,plotConfig);
    Plotly.relayout($("timeline"),{shapes:[{type:"line",xref:"x",yref:"paper",x0:f.elapsed_s,x1:f.elapsed_s,y0:0,y1:1,line:{color:colors.rust,width:1,dash:"dot"}}]});
  }

  function play() {
    if(timer!==null) { pause(); return; }
    if(frameIndex===selected.replay.length-1) {frameIndex=0; drawFrame();}
    $("play").textContent="Pause replay";
    function schedule() {
      const next=selected.replay[frameIndex+1];
      if(!next) {pause();return;}
      const delay=(next.elapsed_s-selected.replay[frameIndex].elapsed_s)*1000;
      timer=setTimeout(()=>{frameIndex++; drawFrame(); schedule();},delay);
    }
    schedule();
  }

  function drawScatter(valid) {
    const traces=[true,false].map(observed=>{
      const rows=valid.filter(r=>(r.runner_detected_fraction===1)===observed);
      return {x:rows.map(r=>r.distance_m),y:rows.map(r=>r.free_area_delta_m2),customdata:rows.map(r=>r.run_id),
        text:rows.map(r=>`${safe(r.player_name)} · ${clock(r.start_clock_s)}<br>Context detected: ${percent(r.context_endpoint_detected_fraction)}`),
        mode:"markers",name:observed?"Runner fully detected":"Runner includes extrapolation",
        marker:{size:8,color:observed?colors.teal:colors.rust,symbol:observed?"circle":"x",opacity:.75},
        hovertemplate:"%{text}<br>%{x:.1f} m · patch change %{y:+.0f} m²<extra></extra>"};
    });
    const layout=baseLayout(); Object.assign(layout,{legend:{orientation:"h",y:1.2},
      xaxis:{title:{text:"Run distance (m)"}},yaxis:{title:{text:"Fixed-patch change (m²)"}},
      shapes:[{type:"line",xref:"paper",x0:0,x1:1,y0:0,y1:0,line:{color:colors.ink,width:1}}]});
    if(!valid.length) layout.annotations=[{xref:"paper",yref:"paper",x:.5,y:.5,text:"No valid space estimates in this selection",showarrow:false}];
    Plotly.react($("scatter"),traces,layout,plotConfig);
    $("scatter").removeAllListeners("plotly_click");
    $("scatter").on("plotly_click",event=>{const id=event.points[0].customdata;if(id){$("run").value=id;chooseRun();$("run").focus();}});
  }

  function drawRecords() {
    $("rows").replaceChildren(...currentRuns.map(r=>{
      const tr=document.createElement("tr");
      for(const text of [r.player_name,clock(r.start_clock_s),number(r.distance_m),number(r.free_area_delta_m2,"",true),percent(r.runner_detected_fraction),percent(r.context_endpoint_detected_fraction)]) {
        const td=document.createElement("td");td.textContent=text;tr.append(td);
      } return tr;
    }));
  }

  async function init() {
    try {
      if(!window.Plotly) throw new Error("The local chart library could not load.");
      let response=await fetch("release.json"); if(!response.ok) throw new Error("Release metadata is unavailable."); release=await response.json();
      response=await fetch(release.snapshot); if(!response.ok) throw new Error("The reviewed snapshot is unavailable.");
      let bytes=await response.arrayBuffer();
      const magic=new Uint8Array(bytes);
      if(magic[0]===31 && magic[1]===139) {
        if(!window.DecompressionStream) throw new Error("This browser needs gzip stream support. Use a current browser or download the CSV below.");
        bytes=await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream("gzip"))).arrayBuffer();
      }
      const digest=Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",bytes)),b=>b.toString(16).padStart(2,"0")).join("");
      if(digest!==release.sha256) throw new Error("The snapshot checksum does not match the reviewed release.");
      data=JSON.parse(new TextDecoder().decode(bytes));
      const m=data.metadata; $("scope").textContent=`${m.home_team.short_name} vs ${m.away_team.short_name} · ${m.date_time.slice(0,10)} · full match · ${m.pitch_length} × ${m.pitch_width} m`;
      for(const team of [m.home_team,m.away_team]) $("team").append(option(String(team.id),team.short_name));
      $("source-note").textContent=`Historical snapshot of one match; sampled replays at 2 Hz, analytical calculations at 10 Hz. Positions are rounded to 1 mm for browser display. Source revision ${data.provenance.revision.slice(0,12)}. No account, API key or live feed.`;
      $("workbench").hidden=false; $("status").hidden=true; $("provenance").disabled=false;
      $("filters").addEventListener("submit",e=>e.preventDefault());
      for(const id of ["profile","team","kind","quality","distance"]) $(id).addEventListener("change",updateFilters);
      $("distance").addEventListener("input",()=>{if($("distance").checkValidity()) updateFilters();});
      $("run").addEventListener("change",chooseRun); $("play").addEventListener("click",play);
      $("rewind").addEventListener("click",()=>{pause();frameIndex=0;drawFrame();});
      $("frame").addEventListener("input",()=>{pause();frameIndex=Number($("frame").value);drawFrame();});
      $("reset").addEventListener("click",()=>{$("filters").reset();selected=null;updateFilters();});
      $("records").addEventListener("toggle",()=>{if($("records").open) drawRecords();});
      $("download").addEventListener("click",()=>{
        const fields=Object.keys(data.profiles["5.0"].runs[0]).filter(k=>k!=="replay");
        const csvCell=value=>value===null || value===undefined?"":`"${String(value).replaceAll('"','""')}"`;
        const csv=[fields.join(","),...currentRuns.map(r=>fields.map(k=>csvCell(r[k])).join(","))].join("\n")+"\n";
        saveFile(csv,`invisible-runner-${m.id}-${$("profile").value}-filtered.csv`,"text/csv;charset=utf-8");
      });
      $("provenance").addEventListener("click",()=>saveFile(JSON.stringify({baseline_provenance:data.provenance,
        selected_profile_config:data.profiles[$("profile").value].config,filters:filters(),filtered_run_count:currentRuns.length,
        snapshot_sha256:release.sha256},null,2)+"\n","invisible-runner-view-provenance.json","application/json"));
      updateFilters();
    } catch(error) {
      $("workbench").hidden=true; $("status").hidden=false; $("status").setAttribute("role","alert");
      $("status").textContent=`The analysis could not load: ${error.message} Reload the page, or use the chart, source code and methods below.`;
    }
  }
  init();
})();
