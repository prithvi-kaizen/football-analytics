# Phase 2 findings: imperfect event evidence

**Answer:** an additional noisy action channel can resolve some synthetic tracking ambiguities.
This result depends on what that channel observes. It does not establish that the actual Smart
Tagging export provides equivalent information, nor that restart tags alone solve the problem.

Implemented and tested: **154 tests pass**, 2,376 method runs across 18 world/regime cases with
12 trials each. Historical reproduction recovered 108 legacy CSVs byte-for-byte and all 1,680
Phase 1 non-timing score rows. All 408 frozen Phase 1 files and 34 official tracked files remain
unchanged. No fitting, public-label tuning, restricted asset access or actual-match tag generation.

## Why the experiment is not just another answer key

Visible actions and private referee rulings are generated first. Rules derive game state, while
the annotator sees only public action projections. Cancelled attempts and advisory signals make
cues fallible even before detection errors. Missing annotations, false positives, jitter/bias,
interval uncertainty, category/team errors, unknown teams, duplicates and conflicts are then added.
No truth array, dead duration, private permission, correctness score or latent identity enters
fusion. Tests vary permissions without changing cues and require identical observed tags.

The remaining assumption is substantial: the sensor sees some action cues not contained in 2D
tracking. This is an explicit hypothetical extra modality, not proof of real sensor independence.
Two temporal/kinematic generators, shared-view failures and alignment/null controls challenge
it. Source actions and noisy observations are saved separately. See the prospective
[protocol](PROTOCOL.md) and [implementation specification](MODEL.md).

## Results and failed hypotheses

The original HMM and hierarchy are unchanged. Conservative fusion uses corroborating uncertain
stop/restart reports; probabilistic fusion uses bounded context from individual reports with weak
conditional team hints. Empty/disabled tags reproduce the original hierarchy exactly.

| Moderate-noise generator | HMM spellF1 | Hierarchy | Conservative events | Probabilistic events | Aligned minus shuffled [95% interval] |
|---|---:|---:|---:|---:|---:|
| episode actions | 0.557 | 0.519 | 0.729 | 0.700 | +0.126 [+0.061, +0.190] |
| renewal actions | 0.747 | 0.604 | 0.728 | 0.766 | +0.088 [+0.027, +0.163] |

Intervals resample whole trials with matched methods, not frames. They are conditional on these
generators, exploratory and unadjusted for multiple comparisons. The generators share football
rule semantics; they are not independently validated football simulators. Regimes sharing a
trial ID are not pooled as independent matches.

The controls change the interpretation. Random tags also improved an imperfect hierarchy on
ordinary scenarios: its D bias and abstention policy can improve without new conditional
information. Aligned-minus-shuffled comparisons are therefore more informative than gains over
tagless operation alone. Under corrupted renewal annotations the spellF1 alignment advantage
was -0.023 [-0.085, +0.046], consistent with no advantage. Corruption robustness is not established.

Adding events did not uniformly improve possession recovery under occlusion. In occluded renewal
worlds, probabilistic fusion had spellF1 0.481 versus 0.498 for the hierarchy and 0.594 for the HMM,
even while its D recall increased from zero to 0.557. Better dead-ball detection can coexist with
worse team/spell structure. The ball-mask ablation isolates the effect of permitting event-supported
outputs during missing-ball spans. All settings, including poor ones, remain in the tables.

Incorrect team hints were not consistently useful: removing them improved the declared aggregate
spellF1 from 0.599 to 0.607 and macroF1 from 0.673 to 0.688. These are descriptive equal-weight
scenario means, not a statistically established universal preference. No parameters were changed
after observing these results.

## What the ambiguity pairs establish

Both worlds of each pair have exactly the same complete tracking sequence. Informative noisy
tags differ because the extra action cues differ; shared null tags are exactly identical.

| Pair / moderate noise | Hierarchy filled target accuracy | Conservative | Probabilistic [95%] | Shared shuffled tags |
|---|---:|---:|---:|---:|
| static live versus dead | 0.500 | 0.648 | 0.676 [0.528, 0.819] | 0.500 |
| invisible live versus dead | 0.500 | 0.667 | 0.631 [0.434, 0.812] | 0.500 |

The probabilistic static result supports conditional ambiguity resolution under this synthetic
channel; its invisible-pair interval includes chance. Conservative fusion had an invisible-pair
interval of [0.542, 0.792]. Shared-view loss weakened the invisible results. Every one of **240
tagless/shared-null checks** produced identical outputs in the opposing worlds and stayed at or
below 50% balanced target accuracy. Raw and temporal-X-filled accuracy are both saved, preventing
reduced abstention below chance from being described as information gain.

The strongest cue is also the largest transfer limitation: public DATA.md does not promise a
referee/whistle `stoppage signal` field. The restart-only ablation reached **0.500** on the static
twins. This implementation did not resolve those pairs from set-piece reports alone. That does
not prove restart information is intrinsically useless; it limits what this experiment supports.

## Deliverables and recommendation

The [full report](../../outputs/phase2/report.md) and
[comparison tables](../../outputs/phase2/comparison.md) report per-scenario spellF1, macroF1,
D precision/recall, possession/restart boundary errors, missed/spurious counts, occluded accuracy,
abstention and cost. Undefined rates/timing retain n/a and defined-trial counts. A matched-only
latency is never treated as evidence that missed boundaries were recovered.

Figures: [alignment controls](../../outputs/phase2/alignment.png),
[ablations](../../outputs/phase2/ablations.png), [paired ambiguities](../../outputs/phase2/twins.png),
and [failure cases](../../outputs/phase2/failure_cases.png). Failure examples follow fixed selection
rules: largest corrupted-tag macroF1 harm, largest occluded benefit, and first declared dead twin.

Keep the HMM and tagless hierarchy as controls. Real event weights should remain disabled until
category meanings, timing uncertainty, dependency on tracking and team attribution are validated
on legitimately labelled other matches. Do not invent an official stoppage channel from unrelated
phase codes. The [gated integration design](INTEGRATION.md) describes a human-run XML adapter outside
Codex access; no gated reader was implemented or run. No competition improvement is claimed.

Reproduce from the package directory with `bash scripts/reproduce_phase2.sh`. Individual command:
`.venv/bin/python -m possession_lab.phase2_experiments`. The pinned environment is unchanged.
