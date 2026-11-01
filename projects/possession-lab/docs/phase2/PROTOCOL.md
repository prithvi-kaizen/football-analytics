# Phase 2 protocol: event information versus simulator leakage

Written before evaluation. No fitting, search, public-label tuning, restricted-data ingestion or
actual-match tag generation. Phase 1 source, tests, configuration and every historical output
are hashed in `phase1_freeze.json`. New code is additive; historical runs reproduce into separate
directories so original timing tables and artifacts are not overwritten.

## Critical design review

Tags copied from H/A/D boundaries would be a second answer key, not a useful experiment. Instead,
generate visible actions and private referee decisions first; rules produce state labels, while
a separate sensor sees action cues only. Its API cannot accept truth, state boundaries, private
permission flags or dead-span durations. Signal cues can be advisory, restart attempts cancelled,
and passes misclassified. Observed intervals are independently jittered windows around actions,
not dead-ball intervals. False positives use the same confidence convention as detections.

This still assumes an extra action channel that can contain information absent from coordinates.
It tests conditional value under that assumption, not whether Metrica's real automatic tagging
contains such information. Same-video correlated errors, an alternative generator, and null
controls challenge it. No simulator can establish real-data sensor calibration.

The public DATA.md does not promise referee/whistle stoppage annotations. The synthetic
`stoppage signal` category is an explicitly hypothetical extra cue, not an official field.
A restart-only ablation removes it; any gain requiring it is not evidence for the actual
Smart Tagging export. Source categories/team semantics still need human-run validation.

## Minimum experiment

Two action-clock families use different schedules and movement/occlusion mechanisms, sharing
only the stated football rule engine. One samples live/dead episodes with action clutter; the
other is an independent renewal action process with permission/cancellation decisions. Both
include live freezes, moving players during stoppages, missed ball observations and wrong cues.
Identical-tracking twins have H/D alternatives and additional action cues with noisy visibility.
They are causal existence tests, not ordinary independent matches.

Annotator regimes: moderate noise, high corruption, shared-view loss, and broad/delayed timing.
Include missing detections, independent false positives, category confusion, unknown/wrong teams,
duplicates and conflicts. Separate RNG streams for world, tracking and annotations. No exact
event IDs, latent correctness flags, simulator family or private rulings enter fusion. Confidence
is unknown for every observed annotation; no origin-dependent score reveals false positives.

Models A/B: unchanged original HMM/hierarchy. C: bounded probabilistic state evidence only from
corroborating stop/restart reports. D: bounded mixture evidence from individual uncertain reports,
plus weak conditional team evidence. Both use the frozen joint temporal model. Empty/disabled
tag evidence returns the original hierarchy exactly. An explicitly labelled common event-coverage
policy can allow predictions during ball occlusion; an ablation retains the old ball-only mask,
so improvements from changing abstention cannot be mistaken for changed state evidence.

Negative controls: independently shuffled event times within each period (preserving counts,
categories, widths and team hints), period-local cyclic time shifts, and uninformative random
tags generated independently of each world's truth. On twin worlds the random/shuffled donor
tags are exactly shared; tracking-plus-null inputs are therefore identical. Mere improvement
over tagless operation is insufficient: require paired aligned-minus-control comparisons.
Random D-biased evidence may improve an imperfect model without adding conditional information.

Ablations: no team hints, no restart reports, no timing localization (shift control), and the
original missing-ball output mask. Hyperparameters are fixed transparent priors, not estimated
sensor probabilities. Report all regimes/families and failed hypotheses, not a selected winner.

## Evaluation and uncertainty

Use new trial IDs (not Phase 1's 8001..8012), 12 per family/regime. Matched methods see the same
tracking and the same aligned annotations. Whole-trial paired 95% percentile bootstrap, 2,000
draws, with the same resampled IDs per comparison. Twins are resampled as paired worlds; report
balanced target frame accuracy and its difference from tagless operation. Shared null twins
must never exceed 50% balanced target accuracy. This bound is not a spellF1/macroF1 bound.
Also report target accuracy after the official temporal X filling: random tags can reduce an
imperfect model's abstentions and improve raw accuracy without adding information. A raw gain
below the 50% null ceiling must not be called ambiguity resolution. Show both quantities.

Report official-style spellF1 and macroF1, D precision/recall with undefined denominators explicit,
typed possession start/end boundary errors, timing, abstention, and wall cost. Measure tag-related
false D on live frames and wrong-team errors. Include direct D-to-live restart timing errors as
an additional diagnostic. Intervals are conditional on these simulators and are exploratory,
not multiplicity-adjusted or football-population guarantees.

Inspect failure traces selected by a declared rule: largest harm from corrupted tags and largest
benefit under occlusion, alongside the first twin pair. Save observations and latent actions
separately for auditing; only the observation projection is available to the fusion function.

## Integration boundary

Design an XML ingestion plan from the public DATA.md and existing in-memory PhaseInterval
contract, but do not implement file loading or open a gated asset. Real category likelihoods,
timing offsets, dependencies and Team semantics remain unknown. No automatic competition use
or transfer of synthetic performance is justified. No frontend or paid API is needed.
