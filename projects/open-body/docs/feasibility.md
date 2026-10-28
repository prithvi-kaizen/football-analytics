# Feasibility assessment, before modelling

Assessed 28 October 2026. Proceed as a two-match, observational pilot. Do not promise an improvement or causal conclusion.

## Verified release and permitted use

The [SkillCorner Hugging Face dataset](https://huggingface.co/datasets/SkillCorner/opendata-bodypose) is public and ungated. Its metadata and dataset card declare MIT. The [upstream repository](https://github.com/SkillCorner/opendata) contains an MIT licence with SkillCorner copyright; retain that notice and credit SkillCorner and PySport in derived work. Snapshots are in `docs/source`; exact download URLs, revisions, sizes and SHA-256 hashes are written to `data/provenance.json`. Code and data notices are separate.

Two full matches are available: Brisbane Roar v Perth Glory (1925299, 21 December 2024), and Sydney FC v Adelaide United (1996435, 1 February 2025). ZIP sizes from the publisher's manifest are 623,408,231 and 644,327,811 bytes, each about 3.3 GB uncompressed. Stream the ZIP members rather than extracting them or materialising joint tables. A 309-frame tutorial sample exists but is not an adequate evaluation dataset.

## Actual schema

Pose is JSON Lines: `frame`, `timestamp`, `period`, `ball_data`, `possession`, `image_corners_projection`, `player_data`. Player rows contain `player_id`, `x`, `y`, `is_detected`, and nullable `joints`. Each of 29 named joints has `xyz` in metres and `p90_mae_cm`. This is an estimated error, not a probability or a calibrated angular confidence interval. The sample has separate left/right shoulders and hips. Z is meaningful relative to the player, not as absolute height above the pitch.

Tracking has the same frame-level structure at 10 Hz. Pose is at 25 Hz, and the documented global-video-frame relation is `pose_frame = 2.5 * tracking_frame`. Match metadata contains period boundaries, lineup player IDs, pitch dimensions and home attacking direction by period. Clock timestamps reset/offset by period relative to global video frames, so joins must use both global frame and period and audit timestamps. Pose XY values are interpolated from 10 Hz tracking, not independent 25 Hz observations. The tracking URLs in raw GitHub initially return Git LFS pointers; resolve their actual media and verify pointer hashes.

Dynamic events are a wide CSV. `event_id` is unique only within a match. Relevant observed fields include `event_type=player_possession`, `start_type=pass_reception`, `frame_start`, `frame_end`, `duration`, `attacking_side`, `player_id`, `team_id`, `end_type`, `pass_outcome`, `player_targeted_x_reception`, pressure start fields, and possession EPV start/end/delta fields. Events use attack-normalized coordinates. Tracking uses fixed pitch coordinates. Match metadata must control pitch scaling and direction conversion; validate against real matched receptions, not just the documentation.

## Limits that affect the question

* The publisher reports joints for 31.4% of all roster player-frames in match 1925299. This is not a reception coverage estimate or an on-pitch denominator. Measure both. Many player rows refer to substituted/off-pitch roster members.
* Pose requires visibility and separability in broadcast video. Missingness is related to location, crowding and play, so complete-case orientation samples are selected. Compare baseline on all eligible rows and on the exact orientation subset.
* Tracking identities can be wrong; the publisher reports about 97% identity accuracy, not independently verified here. Pose and XY are produced separately and can disagree. Gating cannot prove correct left/right identity or body direction.
* Joint errors, left/right swaps, occlusion, collapsed shoulder width, angle wrap and jitter can distort orientation and turn rate. Gate width/error, smooth unit vectors causally, reject incoherent windows and avoid filling long gaps.
* No independent body-heading ground truth, gaze, head-scanning labels, intentions, first-touch annotations or controlled matching are supplied. Shoulder heading is a proxy. Do not rename an orientation category as a proven half-turn technique.
* Vendor pressure and EPV are model outputs with incompletely open training methods. Compute a transparent nearest-opponent baseline and use EPV descriptively, never as an input to predict its own change.
* Two matches mean two independent match environments, not thousands of independent experiments. Resampling receptions cannot quantify new-match generalisation. No causal estimate, player ranking or population-level significance claim is warranted.

## Football question and falsifiable hypothesis

Among matched outfield pass receptions with tracking context and reliable shoulder pose at/before reception, does adding shoulder orientation to a position-and-pressure model reduce held-out log loss for a successful pass that gains at least 5 m within 2 s? H0: held-out log-loss difference (orientation minus baseline) is nonnegative. H1: it is negative. A practically promising pilot requires negative differences in both match directions and a conditional 95% paired block-bootstrap interval below zero in the chronological holdout. This is a predeclared pilot criterion, not a population test. Failure or mixed results are publishable.

The primary population includes all outfield roles to preserve a viable sample; a midfield-only sensitivity is explicitly exploratory. Outcomes come from event labels. Successful pass gain is receiver-at-reception X minus current reception X in the event's normalized pitch direction, scaled to actual metres. Missing successful-pass destination labels are excluded, not negatives. Other end types are negatives except unknown outcomes, which are excluded. Duration is validated against frame difference. Failed/offside passes are negatives. This does not measure every form of progression or long-term retention.

## Baseline-first protocol

Fixed ridge logistic regression, trained only on match 1925299 and tested on 1996435. Standardization is fitted on training rows only. Baseline: tracking X, absolute Y, nearest opponent distance, count of opponents within 5 m, pre-reception speed. Add a training-prevalence constant benchmark. Validate all-eligible baseline first and record it before deriving pose features or fitting the proposed model. Then fit baseline and augmented models on identical complete-case train/test rows.

Primary metric: log loss. Secondary: Brier score, AUROC, calibration bins and event prevalence. Record per-reception predictions and paired loss differences. Conditional uncertainty: paired 5-minute time-block bootstrap within the held-out match, 2,000 replicates with fixed seed. Include reverse-match evaluation, a midfield subset where viable, strict/loose shoulder-error gates, no/longer smoothing, a 100 ms earlier feature cutoff and angular-noise stress tests. Do not tune or choose a configuration after inspecting holdout results.

All model inputs must exist no later than reception. Future heading, next-action direction, turn after receiving, possession end fields, vendor EPV and outcome flags are excluded. Post-reception movement alignment, duration, retention proxy and EPV changes may be descriptive only. They cannot be used to claim an ex-ante prediction gain. Match-separated evaluation avoids adjacent-frame/within-possession leakage, but pre-trained vendor model dependencies and selection remain unresolved.

## Smallest end-to-end build

Download pinned inputs, validate full matches, form reception rows, run baseline, then derive causal pose windows and the paired comparison. Export machine-readable audits, predictions, sensitivity results, descriptive orientation-category summaries and a small real reception clip. Only after these calculations pass tests, build a local offline 2D/3D viewer and a 20–40-second demo. The viewer must show missing pose explicitly and display conditional uncertainty and the two-match limitation beside results.

### Full-match validation update

The 1925299 full scan reproduces the published frame and pose counts. Native clock alignment is exact, but pose XY and native XY show substantial outliers despite typical sub-metre agreement. Before any orientation outcome model was fitted, reception-window samples gained a same-period, backward-looking native-tracking consistency gate at 2 m. This repair and its audit are documented in methodology. The PDF linked from the upstream event documentation returned HTTP 403; the implementation instead checks the actual event columns, metadata, duration/frame identities and coordinate residuals directly. General scaling to non-reference pitch sizes remains unverified by these two reference-sized pitches.
