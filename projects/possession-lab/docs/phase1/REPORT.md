# Phase 1 findings

Completed with **130 passing tests**, 1,680 method runs, and 108 legacy truth/prediction CSVs
reproduced byte-for-byte. Original feature/model/generator files and all official tracked files
remain unchanged. No fitting or public-label tuning was performed. Results below are synthetic
stress tests and do not establish competition improvements.

The implementation and prospective [protocol](PROTOCOL.md) are reproducible with
`bash scripts/reproduce_phase1.sh`. The [full report](../../outputs/phase1/report.md),
[per-scenario comparison](../../outputs/phase1/comparison.md),
[trial metrics](../../outputs/phase1/metrics.csv) and
[paired deltas](../../outputs/phase1/paired_deltas.csv) contain the audit trail.

## What caused the old failure

Inspection and tracing confirmed the cause rather than attributing it to temporal smoothing.
The stationarity feature uses trailing medians of ball/player speeds and accumulates time below
0.8 m/s. `evidence()` first recognizes H/A control, then overwrites it with D after 1.2 s of
stationarity. In the original stationary-live trial, 89.3% of live frames crossed that threshold
and 2,000 control observations were overwritten despite no ball being out of bounds. Recurrent
D observations kept resetting the state machine's age and repeatedly favoured D in the HMM.

## What changed

A separate hierarchy estimates live/dead evidence and conditional home/away evidence, then
decodes four joint states with Viterbi and computes normalized forward/backward marginals.
The two dead states carry latent owner memory but both output D. Missing quantities contribute
no observation evidence; prolonged unreliable ball observation causes an explicit X output.
Stationarity is weak evidence, not an override. All probabilities use declared, uncalibrated
engineering priors. [MODEL.md](MODEL.md) specifies the factorization and limitations.

Controlled ablations independently remove stationarity, replace missing ball observations with
static evidence, remove live/dead durations, or remove team continuity. Two additional variants
remove only stationarity from copies of the legacy features. The originals remain callable.

## What the new evaluation found

Each scenario has 12 randomized synthetic matches, with varying schedules, durations and spatial
layouts. Mechanisms include burst loss, state-dependent loss, camera cropping, moving dead-ball
players, live freezes, invisible stoppages, outliers and short spells. Intervals bootstrap whole
trials, not frames. Paired model comparisons retain the same match and observations.

| Scenario | Original SM spellF1 | Original HMM spellF1 | Hierarchy spellF1 [95% interval] |
|---|---:|---:|---:|
| stationary live | 0.054 | 0.041 | 0.851 [0.802, 0.897] |
| IID visibility loss | 0.879 | 0.935 | 0.845 [0.794, 0.894] |
| camera cropping | 0.219 | 0.302 | 0.331 [0.216, 0.460] |
| moving dead-ball players | 0.719 | 0.768 | 0.776 [0.713, 0.824] |
| invisible stoppages | 0.718 | 0.760 | 0.761 [0.691, 0.818] |

The hierarchy is a useful stationary-live countermeasure, **not a universal replacement**.
On IID trials the original HMM's paired spellF1 advantage was 0.090 [0.050, 0.141]. Both moving-dead
and invisible-stoppage D recall remained **zero** for the hierarchy. Reasonable spellF1 therefore
does not demonstrate successful stoppage detection. D precision/recall, typed boundary errors,
matched latency, missed/spurious counts and computational cost are reported for every method
and scenario in the full comparison. Undefined D precision is n/a, not a perfect score.

Failed or unsupported hypotheses are retained. Removing weak stationarity barely changed the
hierarchy's aggregate spellF1. The unsafe missing-as-static variant increased macroF1 by about
0.005 [0.003, 0.007], contrary to a consistent benefit from masking; its spellF1 delta included
zero. This suite cannot establish a superior missingness policy. Removing duration priors
increased frame macroF1 slightly but reduced spellF1 by about 0.387, even hurting short-spell
trials. Removing owner continuity reduced spellF1 by about 0.743. These are generator-dependent,
paired exploratory results, not corrected multiple-hypothesis tests or real-match guarantees.

## What tracking cannot identify

Static and invisible counterexample pairs have identical complete tracking observations but
opposing H/D truth in a target interval. Common motion before/after can be a live pass in one
world and a restart in the other. All 240 method/pair checks produced identical outputs across
the opposing worlds. Their two target frame accuracies sum to at most one; an equal-prior
choice between the worlds has at most 50% expected target accuracy. This bound applies to
frame decisions, not to macroF1 or spellF1. Temporal context cannot recover an absent referee
decision when the full observation sequences are equal.

Keep both legacy baselines and these negative controls. Further work needs independently labelled
other matches and better observation mechanisms before calibration or model selection. The
[Smart Tagging interface](SMART_TAGGING.md) preserves uncertain phase intervals, unknown teams
and conflicts; it neither creates actual-match tags nor converts phases into truth. No tags were
fused here. Restricted integration stays outside Codex-accessible environments.
