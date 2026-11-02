# Phase 2: can imperfect events resolve tracking ambiguity?

Synthetic event-channel experiment only. No training, tuning, restricted input, real-match
tag creation or competition-performance claim. All Phase 1 implementations and historical
results remain frozen. The complete protocol is in `../../docs/phase2/PROTOCOL.md`.

## Leakage audit and scope

Actions and private referee permissions precede the labels. Two different action-clock
processes generate worlds; a rule engine derives state, while the noisy sensor receives only
visible action projections, timeline and optional shared-view visibility. Cancelled attempts
and advisory signals prevent a cue from being equivalent to a label. No private ruling,
true dead interval, label array, latent correctness bit or simulator-family ID enters fusion.
False positives and detections both carry unknown confidence. Source actions and observed
annotations are saved separately. Unit tests change private permissions while holding visible
cues fixed and require identical annotation streams.

This does not eliminate simulator assumptions. The extra action channel is assumed to see
some officiating/attempt cues absent from 2D coordinates. The synthetic stoppage-signal code
is hypothetical: public DATA.md does not promise it in the real export. The restart-only
ablation removes that cue. Shared-view loss, corruption, null tags and a second action process
challenge the assumptions; none establish real sensor calibration or conditional information.

## Fixed experiment and optional fusion

2,376 method runs across 18 world/regime cases with 12 trials each.
Episode worlds and renewal worlds differ in action schedules and movement/occlusion generation
but share football-rule semantics. No parameters were searched or selected on these trials.
Annotation regimes include missing detections, false positives, timing offsets/broad windows,
category errors, unknown/wrong teams, repeated/conflicting tags and shared-camera failures.
A/B are the unchanged HMM and hierarchy. C accepts only corroborating stop/restart reports.
D combines bounded probabilistic context from individual reports, with weak conditional team
hints for restart reports only. Event time is uniform within its uncertain annotation window.
Context decays rather than assigning an entire phase to a hard label; overlapping evidence
is averaged and capped, exact duplicates deduplicated. Declared semantic probabilities are
engineering priors, not calibrated likelihoods of the real export. Generic phase teams are
ignored because they may refer to a defending side. The joint decoder and tracking evidence
are imported from frozen Phase 1. Empty/disabled evidence reproduces the hierarchy exactly.

The default event-coverage policy may permit output during ball occlusion. The ball-mask
ablation restores the old ball-only abstention rule; read it separately from state inference.
Negative controls shuffle event times or shift them within periods, preserving ordinary
world tag counts, widths, categories and teams. Random tags are independent of actions.
For twins the donor control stream is exactly shared across worlds, selected independently
of which world is evaluated. These paired nulls have no conditional information.

## Per-family results

Intervals are 95% whole-trial paired percentile bootstrap intervals (2,000 draws).
They are conditional on these generators and unadjusted for multiple exploratory comparisons.
Tables and confidence.csv include defined-trial counts for D precision/recall and latency.

| Family / regime | HMM spell | Hierarchy spell | Conservative spell | Probabilistic spell [95%] | Probabilistic macro [95%] |
|---|---:|---:|---:|---:|---:|
| episodes:corrupt | 0.557 | 0.519 | 0.644 | 0.598 [0.549, 0.649] | 0.614 [0.572, 0.655] |
| episodes:delayed | 0.557 | 0.519 | 0.662 | 0.661 [0.576, 0.741] | 0.697 [0.649, 0.741] |
| episodes:moderate | 0.557 | 0.519 | 0.729 | 0.700 [0.643, 0.754] | 0.722 [0.696, 0.750] |
| episodes:occluded | 0.423 | 0.382 | 0.481 | 0.412 [0.332, 0.482] | 0.562 [0.516, 0.604] |
| episodes:shared_view | 0.423 | 0.382 | 0.405 | 0.468 [0.430, 0.506] | 0.590 [0.546, 0.628] |
| renewal:corrupt | 0.747 | 0.604 | 0.558 | 0.671 [0.609, 0.741] | 0.737 [0.673, 0.802] |
| renewal:delayed | 0.747 | 0.604 | 0.651 | 0.771 [0.699, 0.834] | 0.795 [0.735, 0.852] |
| renewal:moderate | 0.747 | 0.604 | 0.728 | 0.766 [0.694, 0.824] | 0.800 [0.743, 0.851] |
| renewal:occluded | 0.594 | 0.498 | 0.549 | 0.481 [0.419, 0.559] | 0.620 [0.553, 0.688] |
| renewal:shared_view | 0.594 | 0.498 | 0.476 | 0.465 [0.392, 0.544] | 0.593 [0.521, 0.659] |

All eleven methods, including every negative control and ablation, are in `comparison.md`.
`paired_deltas.csv` reports model minus hierarchy; `alignment_deltas.csv` reports aligned
probabilistic fusion minus each control. Gains over tagless alone do not establish information:
a random D-biased cue can improve an imperfect baseline by changing its prior or abstention.

| Family / regime | Probabilistic D precision / recall | Restart recall | Boundary missed / spurious | Matched boundary MAE (frames) |
|---|---:|---:|---:|---:|
| episodes:corrupt | 0.852 / 0.155 | 0.095 | 10.1 / 4.1 | 1.1 |
| episodes:delayed | 0.851 / 0.336 | 0.241 | 8.3 / 4.2 | 1.5 |
| episodes:moderate | 0.861 / 0.366 | 0.306 | 7.8 / 4.1 | 2.1 |
| episodes:occluded | 0.494 / 0.508 | 0.254 | 15.8 / 6.7 | 5.6 |
| episodes:shared_view | 0.519 / 0.449 | 0.131 | 14.7 / 7.8 | 5.2 |
| renewal:corrupt | 0.668 / 0.445 | 0.310 | 8.1 / 2.2 | 1.3 |
| renewal:delayed | 0.777 / 0.543 | 0.374 | 6.4 / 1.9 | 1.2 |
| renewal:moderate | 0.747 / 0.534 | 0.415 | 6.4 / 1.8 | 1.8 |
| renewal:occluded | 0.391 / 0.557 | 0.244 | 12.1 / 5.5 | 5.9 |
| renewal:shared_view | 0.393 / 0.462 | 0.133 | 12.4 / 4.8 | 4.8 |

Restart timing matches only D-to-H/A transitions by destination within +/-25 frames and
within each graded block. Possession boundary diagnostics count typed starts/ends and omit
known period edges. Both use the official temporal X filling. A matched-only latency must
be read with recall/missed counts; n/a is retained when its denominator is zero.

## Alignment controls and ablations

Below: equal-weight ordinary scenarios averaged within each trial ID before paired
bootstrap, preserving correlation across regimes. These are descriptive synthetic averages,
not a general ranking. Difference is method minus tagless hierarchy.

| Method / ablation | SpellF1 delta [95%] | macroF1 delta [95%] | D recall delta [95%] |
|---|---:|---:|---:|
| conservative | +0.075 [+0.028, +0.126] | +0.116 [+0.090, +0.146] | +0.568 [+0.505, +0.625] |
| probabilistic | +0.086 [+0.041, +0.135] | +0.143 [+0.115, +0.173] | +0.435 [+0.377, +0.493] |
| tags_shuffled | +0.024 [-0.018, +0.063] | +0.102 [+0.080, +0.126] | +0.374 [+0.333, +0.419] |
| tags_shifted | +0.027 [-0.016, +0.066] | +0.089 [+0.067, +0.111] | +0.355 [+0.303, +0.406] |
| tags_uninformative | +0.040 [+0.011, +0.073] | +0.086 [+0.060, +0.111] | +0.266 [+0.202, +0.332] |
| no_team | +0.094 [+0.049, +0.141] | +0.157 [+0.129, +0.186] | +0.458 [+0.401, +0.516] |
| no_restarts | +0.015 [-0.046, +0.069] | +0.074 [+0.053, +0.093] | +0.780 [+0.733, +0.823] |
| restart_only | +0.037 [+0.007, +0.071] | +0.056 [+0.029, +0.082] | +0.150 [+0.100, +0.202] |
| ball_mask | +0.086 [+0.041, +0.134] | +0.140 [+0.112, +0.169] | +0.423 [+0.364, +0.479] |

## Identical tracking: informative versus null tags

Twin worlds have the same full tracking history/future and opposite H/D target truth. Their
additional action cues differ, and the annotator observes them imperfectly. They test the
conditional hypothesis that another modality supplies information; they do not prove the real
tagging product observes such a modality. Shared null inputs must produce the same predictions
and cannot exceed 50% balanced target accuracy. This bound also holds for randomized rules
in expectation and is not a macroF1/spellF1 bound.

Both raw and official-temporally-filled target accuracies are saved. Null tags may reduce X
and increase raw accuracy below chance without adding information. The filled result removes
that particular abstention artifact; require a gain above the paired null ceiling to claim
synthetic ambiguity resolution. The paired worlds are resampled together, never as two
independent matches.

| Pair family / regime | Hierarchy filled accuracy | Conservative filled accuracy | Probabilistic filled accuracy [95%] | Random tags filled accuracy |
|---|---:|---:|---:|---:|
| twins_invisible:moderate | 0.500 | 0.667 | 0.631 [0.434, 0.812] | 0.460 |
| twins_invisible:shared_view | 0.500 | 0.542 | 0.594 [0.431, 0.761] | 0.460 |
| twins_static:moderate | 0.500 | 0.648 | 0.676 [0.528, 0.819] | 0.500 |
| twins_static:shared_view | 0.500 | 0.648 | 0.676 [0.528, 0.819] | 0.500 |

All 240 declared tagless/shared-null pair checks passed the identical-output and <=50% tests.

## Failures, costs and recommendation

Do not suppress negative control gains, harmful category/team errors or missed restarts.
Use both generator families and each regime when assessing robustness. Dependence on the
hypothetical stoppage cue, assumed timing kernel or event-coverage policy is a limitation
until validated on independent, legitimately labelled other matches. The restart-only and
ball-mask ablations are essential to that interpretation. Real phase intervals can span
multiple possessions and real set-piece codes need not imply the exact dead/live boundary.

Cost includes common tracking feature extraction plus decoder/fusion wall time, after warm-up
and counterbalanced method order on this host. I/O/scoring/plotting and annotation generation
are excluded. Synthetic annotation generation cost is not a cost estimate for video tagging.

| Method | Feature ms | Decoder/fusion ms | Total ms |
|---|---:|---:|---:|
| hmm | 33.1 | 8.8 | 41.9 |
| hierarchical | 33.1 | 19.1 | 52.2 |
| conservative | 33.1 | 19.5 | 52.6 |
| probabilistic | 33.1 | 19.9 | 53.0 |

Recommended real integration remains disabled/zero-weight until category semantics, temporal
uncertainty, false positives and dependence on tracking are validated externally. The design
is in `../../docs/phase2/INTEGRATION.md`; no gated XML reader was run or added. Public ground
truth is not used to fit/select this model. Reproduce with `bash scripts/reproduce_phase2.sh`.

Figures: `alignment.png`, `ablations.png`, `twins.png` (when pairs are present), and
`failure_cases.png`. Failure cases use declared selection rules, not only favourable examples.
