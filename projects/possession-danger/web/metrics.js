(function (root, factory) {
  const metrics = factory();
  if (typeof module === "object" && module.exports) module.exports = metrics;
  else root.PossessionMetrics = metrics;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";
  const sum = (rows, key) => rows.reduce((total, row) => total + (Number.isFinite(row[key]) ? row[key] : 0), 0);
  const mean = (rows, key) => { const values = rows.map(r => r[key]).filter(Number.isFinite); return values.length ? values.reduce((a, b) => a + b, 0) / values.length : null; };
  function aggregateTeams(rows) {
    return [...new Set(rows.map(r => r.team))].map(team => {
      const r = rows.filter(row => row.team === team), possessions = sum(r, "possessions");
      return { team, matches: r.length, possession: mean(r, "possession_pct"), tilt: mean(r, "field_tilt"), threat: mean(r, "threat_share"),
        positive_xt: sum(r, "positive_xt"), net_xt: sum(r, "net_xt"), possessions, shots: sum(r, "shots"), xg: sum(r, "xg"),
        xt_per_100: possessions ? 100 * sum(r, "positive_xt") / possessions : null };
    }).sort((a, b) => b.xt_per_100 - a.xt_per_100);
  }
  function aggregateStates(rows) {
    const groups = new Map();
    for (const row of rows) {
      const key = JSON.stringify([row.team, row.score_state]);
      if (!groups.has(key)) groups.set(key, { team: row.team, state: row.score_state, active_seconds: 0, positive_xt: 0, shots: 0, xg: 0 });
      const group = groups.get(key);
      for (const key of ["active_seconds", "positive_xt", "shots", "xg"]) group[key] += row[key] || 0;
    }
    return [...groups.values()].map(row => ({ ...row, active_minutes: row.active_seconds / 60, rate: row.active_seconds > 0 ? row.positive_xt / row.active_seconds * 60 : null }));
  }
  function classify(row, duration = 30, ceiling = .01) {
    if ((row.elapsed_seconds >= duration || row.passes >= 10) && row.positive_xt < ceiling && row.shots === 0) return "High volume / low threat";
    if (row.elapsed_seconds <= 15 && row.passes <= 4 && row.positive_xt >= .05) return "Direct / high threat";
    return "Other";
  }
  return Object.freeze({ aggregateTeams, aggregateStates, classify });
});
