# Technical results

The two-match pilot found lower out-of-match log loss after adding shoulder orientation, but both conditional intervals include zero. The predeclared pilot criterion was not met. Midfield-only results are mixed. The project demonstrates a reproducible measurement pipeline; it does not establish the causal value of receiving with an open body.

## Main comparison

Target: successful pass that gains at least 5 m from the current reception location and is released within 2 seconds. Population: matched outfield pass receptions with tracking context and reliable, causal shoulder windows. Model: fixed L2 logistic regression with training-only standardization.

| Metric | Chronological baseline | Chronological + orientation | Reverse baseline | Reverse + orientation |
|---|---:|---:|---:|---:|
| Training receptions | 665 | 665 | 647 | 647 |
| Test receptions | 647 | 647 | 665 | 665 |
| Log loss | 0.5751 | 0.5599 | 0.5256 | 0.5168 |
| Brier | 0.1913 | 0.1864 | 0.1746 | 0.1733 |
| AUROC | 0.6269 | 0.6745 | 0.6584 | 0.6859 |

Chronological train 1925299 / test 1996435: paired log-loss change −0.0151913, conditional 95% interval [−0.0291172, +0.0009032]. Reverse: −0.0088084, interval [−0.0190842, +0.0016590]. Lower values favour orientation. The held-out constant benchmark has log loss 0.5771 on the chronological matched sample.

The interval resamples five-minute test-match blocks (20 chronological, 21 reverse), with 2,000 replicates and fixed fitted models. It does not quantify generalisation to unseen matches. Treat two games as two environments, not 1,312 independent experiments.

![Paired conditional uncertainty](../outputs/results.png)

## Baseline first and sample accounting

The baseline on all eligible tracking receptions used 689 training / 662 test receptions. Chronological baseline log loss was 0.5792 versus 0.5799 for training prevalence; reverse baseline was 0.5186 versus 0.5476. These are different samples from the orientation ablation and must not be compared as if pose alone changed the scores.

Across the two games, 1,455 pass-reception events became 1,368 label-eligible outfield matched receptions after excluding 28 unmatched starts, 57 goalkeeper receptions and 2 unknown outcomes. Tracking context and event-location consistency left 1,351 baseline receptions. Orientation/context gates retained 1,312 (665 and 647). The 39 rejected baseline receptions remain in the coverage audit.

The first match's median event/native-XY residual before the 3 m gate was 0.180 m; the second's was 0.166 m. Pose/native-XY exact clocks agreed, but the first match had 30,641 of 527,318 matched player comparisons above 2 m; the second had 11,385 of 478,918. This is evidence of stream disagreement, not proof of which stream is wrong. A backward-looking 2 m agreement gate is applied to reception-window pose samples before modelling.

## Coverage and selection

| Measurement | 1925299 | 1996435 |
|---|---:|---:|
| Pose frames | 153,252 | 144,052 |
| All-roster player-frames with joints | 1,540,715 / 4,902,560 (31.4%) | 1,571,830 / 4,320,150 (36.4%) |
| Active-player frames with joints | 1,540,699 / 3,370,402 (45.7%) | 1,571,536 / 3,168,006 (49.6%) |
| Baseline receptions with usable orientation/context | 665 / 689 (96.5%) | 647 / 662 (97.7%) |

In 1925299, retained receptions have mean nearest-opponent distance 7.72 m versus 5.22 m among excluded rows; target prevalence is 24.2% versus 4.2%. Only 24 rows are excluded, so these descriptive differences are imprecise, but treating missing pose as random would be unjustified. In 1996435, the 15 excluded rows also differ in location and visibility. Full selected/rejected tables and role-specific coverage are in `outputs/coverage.json`.

## Sensitivities and tactical interpretation

Error gates, smoothing windows and a feature cutoff 100 ms earlier retain negative log-loss point changes in both directions. Angular-noise stress tests attenuate the chronological point change: about −0.0107 with 15-degree SD noise and −0.0032 with 30-degree SD noise. These are one fixed-seed stress run each, not estimates of angular-error uncertainty.

The midfield-only comparison worsens chronological log loss by **+0.0156** (181 training / 237 test receptions) and improves the reverse by **−0.0147**. The original midfielder-specific question remains unresolved. Do not select the more favourable split.

Forward-facing shoulder categories have higher unadjusted fast-progression fractions in these games than backward-facing categories, but category groups differ in context and role. Possession-duration medians, the limited pass/foul retention proxy and vendor EPV-for changes are exported with denominators in `outputs/orientation_categories.csv`. Those descriptions do not establish a benefit or make the categories equivalent to observed half-turn techniques.

No conclusion about gaze, head scanning, intention, player quality or a causal coaching intervention follows. The practical next step is more independent matches and a manually checked sample of reception timing and body heading. The full [methodology](methodology.md) and [limitations](limitations.md) delimit the claims.

## Provenance

All results above are generated from the pinned public SkillCorner/PySport release. Exact input URLs and SHA-256 hashes are in `data/provenance.json`. Per-reception held-out probabilities and paired losses are in `outputs/heldout_predictions.csv`; aggregate results and all sensitivity runs are in adjacent JSON files. Source research is in [related work](related-work.md). No paper's reported effect is presented as a result of this implementation.
