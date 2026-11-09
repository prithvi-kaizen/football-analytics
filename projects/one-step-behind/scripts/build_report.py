"""Generate exact denominators and sensitivity tables from recorded results."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
results=[json.loads((ROOT/f'outputs/results-{mid}.json').read_text()) for mid in [1925299,1996435]]
lines=['# Evaluation and sensitivity report','', 'No primary candidates were retrieved. Gap-duration and recovery-time distributions are unavailable, not zero. There are no ground-truth tactical labels; no accuracy or precision is estimated.','',
'| Match / population | Eligible team-seconds | Steps | Step-seconds | Instantaneous baseline flags | Candidates |', '|---|---:|---:|---:|---:|---:|']
for d in results:
 for kind in ['primary','observed_only']:
  r=d[kind];lines.append(f"| {d['match_id']} {d['split']} / {kind} | {r['eligible_team_seconds']:.1f} | {r['stepping_episodes']} | {r['stepping_seconds']:.1f} | {r['baseline_steps']} | {r['candidate_steps']} |")
lines+=['','Episode durations include the one-second movement window and merged overlapping step windows. These are not all defensive steps in either match. The observed-only rerun changes eligibility and segments; its episodes are not a matched subset.','',
'## Geometric distributions (all eligible team-frames)','','| Match | Metric | Q25 | Median | Q75 | Q90 | Maximum |','|---|---|---:|---:|---:|---:|---:|']
for d in results:
 for key in ['gap_quantiles_m','spread_quantiles_m','step_duration_quantiles_s']:
  q=d['primary'][key]; lines.append(f"| {d['match_id']} | {key} | "+' | '.join(f'{q[str(v)]:.3f}' for v in [.25,.5,.75,.9,1])+' |')
lines+=['','Gap here is the maximum per-frame peer-median deviation, measured in metres, not a candidate duration. Step durations are seconds. Full quantiles, censor counts and line-size counts are in the result JSONs. No five-player line is accepted in these two matches.','',
'## Threshold sensitivity','','| Match | Tolerance (m) | Persistence (s) | Steps | Candidates | Recovered | Censored |','|---|---:|---:|---:|---:|---:|---:|']
for d in results:
 for r in d['sensitivity']: lines.append(f"| {d['match_id']} | {r['gap_m']} | {r['persistence_s']} | {r['steps']} | {r['candidates']} | {r['recovered']} | {r['censored']} |")
lines+=['','Eligibility, step windows and peer-shape tolerance remain fixed. The developmental 2 m candidate is not the primary result. No threshold was selected using held-out candidates. Recovery summaries conditional on detected candidates cannot establish general recovery behaviour.','',
'## Three real examples','','These are comparisons and near-misses because no primary candidates exist. The selection rule was recorded after the zero result: include both held-out baseline flags chronologically, then the largest remaining search-window gap. This replaces the planned candidate-only selection because its population is empty. The all-detected Adelaide example is the default replay and video subject.','',
'| ID | Step start | Defending team | Inspected player | Peak search gap (m) | Line coordinates detected | Failed rules at peak |','|---|---|---|---|---:|---:|---|']
replays=json.loads((ROOT/'outputs/replays.json').read_text())
for e in replays['examples']:
 lines.append(f"| {e['id']} | {e['clock']} | {e['team_name']} | {e['highlight_name']} | {e['peak_search_gap_m']:.3f} | {e['line_observed_fraction']:.1%} | {', '.join(k for k,v in e['peak_conditions'].items() if not v)} |")
lines+=['','Peak-frame failures explain those snapshots; the full detector also tests persistence for every identity across the search window. The first Sydney flag crosses 3 m by only 0.01 m, within plausible tracking uncertainty. The comparison clip ends after 1.2 s because eligibility breaks; do not infer later behaviour.','',
'## Coverage and exclusions','','Exclusions are sequential and exclusive within each of the two team-frame scans. Even in-possession and unavailable-phase frames are included in that audit denominator, so reasons sum to twice the raw frame count. Eligibility is defending-team time, never player-time.','']
for d in results:
 lines += [f"### {d['match_id']}",'', '```json',json.dumps(d['primary']['eligibility'],indent=2),'```','']
 audit=json.loads((ROOT/f"outputs/audit-{d['match_id']}.json").read_text())
 lines += [f"Detected fraction of valid player positions: {audit['detection_fraction']:.4%}; empty period frames: {audit['player_count_distribution'].get('0',0):,}. Source frame/player rows and all validation exclusions are in outputs/audit-{d['match_id']}.json.",'']
lines += ['## Interpretation limits','','Role-backed lines omit midfield cover and advanced fullbacks. Short phase boundaries and missing geometry censor potential gaps. Starting from a compact line selects orderly shapes. Broadcast extrapolation and identity errors can alter gaps; detection flags are not identity verification. Only two convenience-selected matches are used, and the author had previously inspected this holdout dataset for another project. There is no independent tactical annotation or causal outcome analysis.','',
'Observed recovery is defined and unit-tested but has no primary real-data sample. A useful next study would label eligible and rejected steps independently before revising thresholds. The current zero result is not evidence of absence of coordination problems.']
(ROOT/'docs/results.md').write_text('\n'.join(lines)+'\n')
print(ROOT/'docs/results.md')
