# Evaluation and sensitivity report

No primary candidates were retrieved. Gap-duration and recovery-time distributions are unavailable, not zero. There are no ground-truth tactical labels; no accuracy or precision is estimated.

| Match / population | Eligible team-seconds | Steps | Step-seconds | Instantaneous baseline flags | Candidates |
|---|---:|---:|---:|---:|---:|
| 1925299 development / primary | 1891.6 | 49 | 143.9 | 0 | 0 |
| 1925299 development / observed_only | 311.1 | 8 | 14.5 | 0 | 0 |
| 1996435 held_out / primary | 1389.9 | 44 | 106.9 | 2 | 0 |
| 1996435 held_out / observed_only | 563.8 | 22 | 44.2 | 1 | 0 |

Episode durations include the one-second movement window and merged overlapping step windows. These are not all defensive steps in either match. The observed-only rerun changes eligibility and segments; its episodes are not a matched subset.

## Geometric distributions (all eligible team-frames)

| Match | Metric | Q25 | Median | Q75 | Q90 | Maximum |
|---|---|---:|---:|---:|---:|---:|
| 1925299 | gap_quantiles_m | 0.850 | 1.460 | 2.440 | 3.780 | 11.050 |
| 1925299 | spread_quantiles_m | 1.860 | 3.030 | 4.790 | 7.020 | 12.000 |
| 1925299 | step_duration_quantiles_s | 2.000 | 2.600 | 4.000 | 4.500 | 5.600 |
| 1996435 | gap_quantiles_m | 1.020 | 1.710 | 2.790 | 4.070 | 11.680 |
| 1996435 | spread_quantiles_m | 2.105 | 3.480 | 5.290 | 7.630 | 12.000 |
| 1996435 | step_duration_quantiles_s | 1.500 | 2.100 | 3.425 | 3.970 | 5.200 |

Gap here is the maximum per-frame peer-median deviation, measured in metres, not a candidate duration. Step durations are seconds. Full quantiles, censor counts and line-size counts are in the result JSONs. No five-player line is accepted in these two matches.

## Threshold sensitivity

| Match | Tolerance (m) | Persistence (s) | Steps | Candidates | Recovered | Censored |
|---|---:|---:|---:|---:|---:|---:|
| 1925299 | 2.0 | 0.3 | 49 | 1 | 1 | 0 |
| 1925299 | 2.0 | 0.5 | 49 | 1 | 1 | 0 |
| 1925299 | 2.0 | 0.8 | 49 | 1 | 1 | 0 |
| 1925299 | 3.0 | 0.3 | 49 | 0 | 0 | 0 |
| 1925299 | 3.0 | 0.5 | 49 | 0 | 0 | 0 |
| 1925299 | 3.0 | 0.8 | 49 | 0 | 0 | 0 |
| 1925299 | 4.0 | 0.3 | 49 | 0 | 0 | 0 |
| 1925299 | 4.0 | 0.5 | 49 | 0 | 0 | 0 |
| 1925299 | 4.0 | 0.8 | 49 | 0 | 0 | 0 |
| 1996435 | 2.0 | 0.3 | 44 | 0 | 0 | 0 |
| 1996435 | 2.0 | 0.5 | 44 | 0 | 0 | 0 |
| 1996435 | 2.0 | 0.8 | 44 | 0 | 0 | 0 |
| 1996435 | 3.0 | 0.3 | 44 | 0 | 0 | 0 |
| 1996435 | 3.0 | 0.5 | 44 | 0 | 0 | 0 |
| 1996435 | 3.0 | 0.8 | 44 | 0 | 0 | 0 |
| 1996435 | 4.0 | 0.3 | 44 | 0 | 0 | 0 |
| 1996435 | 4.0 | 0.5 | 44 | 0 | 0 | 0 |
| 1996435 | 4.0 | 0.8 | 44 | 0 | 0 | 0 |

Eligibility, step windows and peer-shape tolerance remain fixed. The developmental 2 m candidate is not the primary result. No threshold was selected using held-out candidates. Recovery summaries conditional on detected candidates cannot establish general recovery behaviour.

## Three real examples

These are comparisons and near-misses because no primary candidates exist. The selection rule was recorded after the zero result: include both held-out baseline flags chronologically, then the largest remaining search-window gap. This replaces the planned candidate-only selection because its population is empty. The all-detected Adelaide example is the default replay and video subject.

| ID | Step start | Defending team | Inspected player | Peak search gap (m) | Line coordinates detected | Failed rules at peak |
|---|---|---|---|---:|---:|---|
| 1996435-005 | 17:12.5 | Sydney FC | J. Courtney-Perkins | 3.010 | 29.7% | growth, relative_motion |
| 1996435-042 | 66:58.5 | Adelaide United | F. Talladira | 3.530 | 100.0% | relative_motion |
| 1996435-006 | 17:17.0 | Sydney FC | J. Courtney-Perkins | 2.970 | 63.5% | gap, growth |

Peak-frame failures explain those snapshots; the full detector also tests persistence for every identity across the search window. The first Sydney flag crosses 3 m by only 0.01 m, within plausible tracking uncertainty. The comparison clip ends after 1.2 s because eligibility breaks; do not infer later behaviour.

## Coverage and exclusions

Exclusions are sequential and exclusive within each of the two team-frame scans. Even in-possession and unavailable-phase frames are included in that audit denominator, so reasons sum to twice the raw frame count. Eligibility is defending-team time, never player-time.

### 1925299

```json
{
  "no_consistent_phase": 51318,
  "unknown_or_conflicting_possession": 12900,
  "in_possession": 29192,
  "excluded_phase": 4165,
  "ambiguous_line": 6084,
  "eligible": 18916,
  "missing_ball": 27
}
```

Detected fraction of valid player positions: 57.8867%; empty period frames: 13,340. Source frame/player rows and all validation exclusions are in outputs/audit-1925299.json.

### 1996435

```json
{
  "no_consistent_phase": 51018,
  "unknown_or_conflicting_possession": 11536,
  "eligible": 13899,
  "excluded_phase": 3757,
  "in_possession": 26344,
  "ambiguous_line": 8466,
  "missing_ball": 222
}
```

Detected fraction of valid player positions: 65.8004%; empty period frames: 14,071. Source frame/player rows and all validation exclusions are in outputs/audit-1996435.json.

## Interpretation limits

Role-backed lines omit midfield cover and advanced fullbacks. Short phase boundaries and missing geometry censor potential gaps. Starting from a compact line selects orderly shapes. Broadcast extrapolation and identity errors can alter gaps; detection flags are not identity verification. Only two convenience-selected matches are used, and the author had previously inspected this holdout dataset for another project. There is no independent tactical annotation or causal outcome analysis.

Observed recovery is defined and unit-tested but has no primary real-data sample. A useful next study would label eligible and rejected steps independently before revising thresholds. The current zero result is not evidence of absence of coordination problems.
