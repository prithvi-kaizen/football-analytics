"use strict";
(() => {
  const $ = id => document.getElementById(id);
  const TEAL = "#006b68", RUST = "#a34526", PAPER = "#faf8f3", INK = "#252a28";
  let snapshot, data, scopeRows = [], phaseRows = [], teamRows = [], matchRows = [], view = "comparison";
  const sum = (rows, key) => rows.reduce((s, row) => s + (Number.isFinite(row[key]) ? row[key] : 0), 0);
  const mean = (rows, key) => { const values = rows.map(r => r[key]).filter(Number.isFinite); return values.length ? values.reduce((s, v) => s + v, 0) / values.length : null; };
  const fmt = (value, places = 1) => Number.isFinite(value) ? value.toFixed(places) : "Not observed";
  const unique = (rows, key) => [...new Set(rows.map(row => row[key]))];
  const { aggregateTeams, aggregateStates } = PossessionMetrics;
  const mobile = matchMedia("(max-width: 850px)");
  const scopeDisclosure = () => { $("scope-details").open = !mobile.matches; };
  scopeDisclosure(); mobile.addEventListener("change", scopeDisclosure);
  const text = (tag, value, className) => { const el = document.createElement(tag); el.textContent = value; if (className) el.className = className; return el; };

  function options(id, values, preferred, label = value => value) {
    const current = preferred ?? $(id).value;
    $(id).replaceChildren(...values.map(value => { const option = document.createElement("option"); option.value = String(value); option.textContent = label(value); return option; }));
    $(id).value = values.map(String).includes(String(current)) ? String(current) : String(values[0] ?? "");
  }

  function table(id, rows, columns, empty = "No observations in this selection.") {
    const holder = $(id); holder.replaceChildren();
    if (!rows.length) { holder.append(text("p", empty, "empty")); return; }
    const wrap = document.createElement("div"); wrap.className = "table-wrap"; wrap.tabIndex = 0; wrap.setAttribute("role", "region"); wrap.setAttribute("aria-label", `${id} data table`);
    const el = document.createElement("table"), head = document.createElement("thead"), tr = document.createElement("tr");
    for (const [, label] of columns) { const th = text("th", label); th.scope = "col"; tr.append(th); }
    head.append(tr); el.append(head);
    const body = document.createElement("tbody");
    for (const row of rows) { const line = document.createElement("tr"); for (const [key, , precision] of columns) line.append(text("td", typeof row[key] === "number" ? fmt(row[key], precision ?? 2) : row[key] ?? "Not observed")); body.append(line); }
    el.append(body); wrap.append(el); holder.append(wrap);
  }

  function plot(id, traces, layout = {}, height = 430) {
    return Plotly.react($(id), traces, { paper_bgcolor: PAPER, plot_bgcolor: PAPER, font: { family: "system-ui, sans-serif", size: 13, color: INK },
      height, margin: { l: 60, r: 20, t: 25, b: 65 }, hovermode: "closest", showlegend: true,
      legend: { orientation: "h", y: 1.12 }, ...layout }, { responsive: true, displaylogo: false, scrollZoom: false, modeBarButtonsToRemove: ["lasso2d", "select2d"] });
  }

  function setScope(resetTeam = false) {
    data = snapshot.datasets.find(d => d.id === $("dataset").value);
    const competitions = unique(data.team_matches, "competition").sort();
    options("competition", competitions);
    scopeRows = data.team_matches.filter(row => row.competition === $("competition").value && ($("split").value === "all" || row.split === $("split").value));
    const names = unique(scopeRows, "team").sort();
    options("focus", names, resetTeam ? names.find(n => n.includes("Barcelona")) ?? names[0] : undefined);
    const matchIds = new Set(scopeRows.map(row => row.match_id));
    phaseRows = data.phases.filter(row => matchIds.has(row.match_id));
    teamRows = aggregateTeams(scopeRows);
    const dates = scopeRows.map(row => row.date).sort();
    $("scope").textContent = `${$("competition").value} · ${matchIds.size} fixtures · ${dates[0]} to ${dates.at(-1)} · source ${data.provenance.source_revision.slice(0, 10)}`;
    const warnings = [];
    if (data.sample) warnings.push("Smoke-test sample: these selected fixtures demonstrate the pipeline and cannot support season-level conclusions.");
    if ($("split").value !== "test") warnings.push("Descriptive view containing training matches. Use held-out matches for the primary comparison.");
    $("warning").hidden = warnings.length === 0; $("warning").textContent = warnings.join(" ");
    const params = new URLSearchParams({ dataset: data.id, split: $("split").value, competition: $("competition").value, team: $("focus").value, view });
    history.replaceState(null, "", `${location.pathname}?${params}`);
    if (view === "comparison") renderComparison();
    if (view === "match") renderMatchList();
    if (view === "methods") renderMethods();
  }

  function renderComparison() {
    const focus = $("focus").value, selected = scopeRows.filter(row => row.team === focus);
    $("focus-title").textContent = `${focus}: where the ball goes matters`;
    $("metrics").replaceChildren(...[["Active possession-time share", mean(selected, "possession_pct")], ["Final-third pass share", mean(selected, "field_tilt")], ["Positive move xT share", mean(selected, "threat_share")]].map(([label, value]) => {
      const div = document.createElement("div"); div.append(text("span", label, "metric-label"), text("span", `${fmt(value)}%`, "metric-value")); return div;
    }));
    $("metric-caption").textContent = `Means of match-level shares over ${selected.length} fixtures. Active time unions recorded action durations; field tilt counts completed passes starting in the final third.`;
    const metric = $("scatter-metric").value;
    const traces = [false, true].map(highlight => {
      const rows = scopeRows.filter(row => (row.team === focus) === highlight);
      return { x: rows.map(r => r.possession_pct), y: rows.map(r => r[metric]), type: "scatter", mode: "markers", name: highlight ? focus : "Other teams",
        marker: { color: highlight ? TEAL : RUST, opacity: .8, size: highlight ? 12 : 8, symbol: highlight ? "diamond" : "circle" },
        text: rows.map(r => `${r.team}<br>${r.date} · match ${r.match_id}`), hovertemplate: "%{text}<br>Possession %{x:.1f}%<br>Comparison share %{y:.1f}%<extra></extra>" };
    });
    traces.unshift({ x: [0, 100], y: [0, 100], mode: "lines", line: { color: "#777a73", dash: "dash", width: 1 }, hoverinfo: "skip", showlegend: false });
    plot("scatter", traces, { xaxis: { title: { text: "Active possession-time share (%)" }, range: [0, 100], fixedrange: false },
      yaxis: { title: { text: metric === "threat_share" ? "Positive move xT share (%)" : "Final-third completed-pass share (%)" }, range: [0, 100] } }, 500);
    const ranked = [...teamRows].reverse();
    plot("ranking", [{ x: ranked.map(r => r.xt_per_100), y: ranked.map(r => r.team), type: "bar", orientation: "h", marker: { color: ranked.map(r => r.team === focus ? TEAL : RUST) },
      hovertemplate: "%{y}<br>%{x:.3f} positive xT / 100 possessions<extra></extra>" }],
      { showlegend: false, margin: { l: Math.min(220, window.innerWidth * .35), r: 20, t: 15, b: 60 }, xaxis: { title: { text: "Positive move xT / 100 analytical possessions" }, rangemode: "tozero" }, yaxis: { automargin: true } }, Math.max(350, 32 * ranked.length));
    table("team-table", teamRows, [["team", "Team"], ["matches", "Fixtures", 0], ["possession", "Possession %"], ["tilt", "Field tilt %"], ["threat", "xT share %"], ["xt_per_100", "+xT / 100"], ["net_xt", "Net move xT"], ["shots", "Shots", 0], ["xg", "Shot xG"]]);
    const ids = new Set(scopeRows.map(r => r.match_id));
    const states = aggregateStates(data.score_states.filter(row => ids.has(row.match_id)));
    const teams = teamRows.map(row => row.team), labels = ["winning", "drawing", "losing"];
    plot("states", [{ z: teams.map(team => labels.map(state => states.find(r => r.team === team && r.state === state)?.rate ?? null)), x: labels, y: teams, type: "heatmap", colorscale: "YlGnBu", zmin: 0,
      hoverongaps: false, texttemplate: "%{z:.2f}", hovertemplate: "%{y}<br>%{x}: %{z:.3f} xT / active minute<extra></extra>", colorbar: { title: { text: "xT/min" }, thickness: 12 } }],
      { margin: { l: Math.min(220, window.innerWidth * .35), r: 40, t: 20, b: 45 }, yaxis: { autorange: "reversed", automargin: true } }, Math.max(350, teams.length * 34));
    table("state-table", states, [["team", "Team"], ["state", "State"], ["active_minutes", "Active minutes"], ["positive_xt", "Positive xT"], ["rate", "xT / active min", 3], ["shots", "Shots", 0], ["xg", "Shot xG"]]);
  }

  function renderMatchList() {
    const ids = new Set(scopeRows.filter(row => row.team === $("focus").value).map(row => row.match_id));
    const fixtures = data.fixtures.filter(f => ids.has(f.match_id)).sort((a, b) => a.date.localeCompare(b.date) || a.match_id - b.match_id);
    options("match-select", fixtures.map(f => f.match_id), undefined, id => { const f = fixtures.find(f => f.match_id === id); return `${f.date} · ${f.home} vs ${f.away} · ${id}`; });
    renderMatch();
  }

  function classify(row) {
    return PossessionMetrics.classify(row, +$("duration").value, +$("ceiling").value);
  }

  function renderMatch() {
    const mid = +$("match-select").value, fixture = data.fixtures.find(f => f.match_id === mid);
    if (!fixture) return;
    $("scoreline").textContent = `Final score: ${fixture.home} ${fixture.home_score}–${fixture.away_score} ${fixture.away}`;
    const all = phaseRows.filter(row => row.match_id === mid).sort((a, b) => a.clock - b.clock), focus = $("focus").value;
    const start = Math.min(130, Math.max(0, +$("window-start").value || 0));
    const end = Math.min(140, Math.max(start + 1, +$("window-end").value || 120));
    $("window-start").value = start; $("window-end").value = end;
    const teams = [focus, ...unique(all, "team").filter(name => name !== focus)];
    plot("timeline", teams.map((team, i) => { let cumulative = 0; const rows = all.filter(row => row.team === team), y = rows.map(r => cumulative += r.positive_xt);
      return { x: rows.map(r => r.clock / 60), y, mode: "lines+markers", type: "scatter", name: team, line: { color: i ? RUST : TEAL, shape: "hv" }, marker: { size: 4 },
        text: rows.map(r => `P${r.period} · ${r.sequence_key}<br>${r.passes} passes · started ${r.score_state}`), hovertemplate: "%{text}<br>Cumulative +xT %{y:.3f}<extra></extra>" }; }),
      { xaxis: { title: { text: "Elapsed playing clock (minutes)" }, range: [start, end] }, yaxis: { title: { text: "Cumulative positive move xT" }, rangemode: "tozero" } });
    matchRows = all.filter(row => row.clock >= start * 60 && row.clock <= end * 60);
    const duration = +$("duration").value, ceiling = +$("ceiling").value;
    $("duration-value").textContent = duration; $("ceiling-value").textContent = ceiling.toFixed(3);
    const quiet = matchRows.filter(row => row.elapsed_seconds >= duration && row.positive_xt < ceiling && row.shots === 0).sort((a, b) => b.elapsed_seconds - a.elapsed_seconds);
    table("quiet-table", quiet, [["team", "Team"], ["sequence_key", "Sequence"], ["period", "Period", 0], ["elapsed_seconds", "Elapsed s"], ["active_seconds", "Active s"], ["passes", "Passes", 0], ["positive_xt", "Positive xT", 4], ["score_state", "Start state"]], "No possessions meet these duration, xT, no-shot and time-window rules.");
    const labels = ["High volume / low threat", "Direct / high threat", "Other"], colors = [TEAL, RUST, "#68736c"];
    plot("styles", labels.map((label, i) => ({ x: teams, y: teams.map(team => matchRows.filter(r => r.team === team && classify(r) === label).length), type: "bar", name: label, marker: { color: colors[i] } })),
      { barmode: "stack", yaxis: { title: { text: "Analytical possessions" } }, margin: { l: 60, r: 20, t: 60, b: 85 } }, 360);
    $("style-definition").textContent = `High volume / low threat: elapsed ≥ ${duration}s OR ≥ 10 passes, positive xT < ${ceiling.toFixed(3)}, no shot. Direct / high threat: ≤ 15s, ≤ 4 passes, positive xT ≥ 0.05. Everything else is Other.`;
    const sorted = [...matchRows].sort((a, b) => b.elapsed_seconds - a.elapsed_seconds);
    options("sequence", sorted.map(r => r.sequence_key), undefined, key => { const r = sorted.find(row => row.sequence_key === key); return `${r.team} · P${r.period} · ${fmt(r.elapsed_seconds)}s · +xT ${fmt(r.positive_xt, 3)} · ${key}`; });
    renderSequence();
  }

  function renderSequence() {
    const row = matchRows.find(r => r.sequence_key === $("sequence").value), holder = $("sequence-detail"); holder.replaceChildren();
    if (!row) { holder.append(text("p", "No possession starts in this clock window. Widen it to inspect a sequence.", "empty")); return; }
    holder.append(text("p", `${row.team} · started ${row.score_state} · home-away score ${row.home_score_before}–${row.away_score_before} · ${classify(row)}`));
    const grid = document.createElement("div"); grid.className = "detail-grid";
    for (const [label, value] of [["Elapsed duration", `${fmt(row.elapsed_seconds)}s`], ["Active duration", `${fmt(row.active_seconds)}s`], ["Passes attempted / completed", `${row.passes} / ${row.completed_passes}`],
      ["Progression (coordinate units)", fmt(row.progression)], ["Positive / net move xT", `${fmt(row.positive_xt, 4)} / ${fmt(row.net_xt, 4)}`], ["Shots / shot xG", `${row.shots} / ${fmt(row.xg, 3)}`]]) { const div = document.createElement("div"); div.append(text("span", label, "small"), text("strong", value)); grid.append(div); }
    holder.append(grid);
  }

  function renderMethods() {
    plot("model", [{ z: data.model.value, x: Array.from({ length: data.model.nx }, (_, i) => 5 + i * 10), y: Array.from({ length: data.model.ny }, (_, i) => 5 + i * 10), type: "heatmap", colorscale: "YlGnBu", zmin: 0,
      colorbar: { title: { text: "xT" } }, hovertemplate: "x=%{x}, y=%{y}<br>xT %{z:.4f}<extra></extra>" }],
      { xaxis: { title: { text: "Attacking right: x coordinate" }, range: [0, 120] }, yaxis: { title: { text: "y coordinate" }, range: [80, 0], scaleanchor: "x", scaleratio: 1 } }, 430);
    $("validation").textContent = JSON.stringify({ coverage: data.summary.coverage, train_matches: data.summary.train_matches, test_matches: data.summary.test_matches, model: data.summary.model, cleaning: data.summary.cleaning, checks: data.summary.checks }, null, 2);
    $("provenance").textContent = JSON.stringify({ classification: snapshot.classification, ...data.provenance }, null, 2);
  }

  function selectView(next) {
    view = ["comparison", "match", "methods"].includes(next) ? next : "comparison";
    for (const id of ["comparison", "match", "methods"]) $(id).hidden = id !== view;
    for (const button of document.querySelectorAll("[data-view]")) button.setAttribute("aria-pressed", String(button.dataset.view === view));
    setScope();
  }

  function csv(rows) {
    const keys = Object.keys(rows[0] || {});
    const quote = value => { let v = value == null ? "" : String(value); if (typeof value === "string" && /^[=+\-@]/.test(v)) v = `'${v}`; return `"${v.replaceAll('"', '""')}"`; };
    return [keys.map(quote).join(","), ...rows.map(row => keys.map(k => quote(row[k])).join(","))].join("\r\n");
  }

  async function init() {
    try {
      const releaseResponse = await fetch("release.json"); if (!releaseResponse.ok) throw new Error("Release manifest is unavailable.");
      const release = await releaseResponse.json();
      if (!/^snapshot\.[a-f0-9]{16}\.json\.gz$/.test(release.snapshot)) throw new Error("Invalid snapshot path.");
      const response = await fetch(release.snapshot); if (!response.ok) throw new Error("Research snapshot is unavailable.");
      if (!("DecompressionStream" in window)) throw new Error("This browser lacks gzip decoding. Use a current browser or the downloadable report.");
      const decoded = await new Response(response.body.pipeThrough(new DecompressionStream("gzip"))).arrayBuffer();
      const hash = Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", decoded)), byte => byte.toString(16).padStart(2, "0")).join("");
      if (hash !== release.sha256) throw new Error("Snapshot integrity check failed.");
      snapshot = JSON.parse(new TextDecoder().decode(decoded));
      for (const dataset of snapshot.datasets) dataset.phases = dataset.phases.map(row => Object.fromEntries(dataset.phase_columns.map((key, i) => [key, row[i]])));
      const params = new URLSearchParams(location.search);
      options("dataset", snapshot.datasets.map(d => d.id), params.get("dataset") || "liga-f", id => id === "liga-f" ? "Liga F 2023/24 · full season" : "Five leagues · smoke samples");
      if (["test", "train", "all"].includes(params.get("split"))) $("split").value = params.get("split");
      data = snapshot.datasets.find(d => d.id === $("dataset").value);
      options("competition", unique(data.team_matches, "competition").sort(), params.get("competition") || "Liga F");
      options("focus", unique(data.team_matches.filter(r => r.competition === $("competition").value), "team").sort(), params.get("team") || "Barcelona WFC");
      $("filters").disabled = false; $("application").hidden = false; $("status").hidden = true;
      for (const id of ["dataset", "split", "competition", "focus"]) $(id).addEventListener("change", () => setScope(id === "dataset" || id === "competition"));
      $("scatter-metric").addEventListener("change", renderComparison);
      for (const id of ["match-select", "window-start", "window-end", "duration", "ceiling"]) $(id).addEventListener("change", renderMatch);
      $("sequence").addEventListener("change", renderSequence);
      for (const button of document.querySelectorAll("[data-view]")) button.addEventListener("click", () => selectView(button.dataset.view));
      $("export-teams").addEventListener("click", () => { const url = URL.createObjectURL(new Blob([csv(teamRows)], { type: "text/csv;charset=utf-8" })); const a = document.createElement("a"); a.href = url; a.download = "possession-team-comparison.csv"; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); });
      selectView(params.get("view") || "comparison");
    } catch (error) { $("status").setAttribute("role", "alert"); $("status").textContent = `Could not load the dashboard: ${error.message} The findings report and chart are available from the project on GitHub.`; }
  }
  init();
})();
