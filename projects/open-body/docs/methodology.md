# Methodology

This is an observational, two-match pilot of incremental predictive information at reception. It cannot identify the causal value of opening the body, infer intention, measure head scanning, or rank players. The question, primary thresholds and evaluation criterion were written in `feasibility.md` and `configs/pilot.json` before the orientation models were fitted. This is an internal analysis plan, not a time-stamped external preregistration.

## Inputs and alignment

Use pinned SkillCorner/PySport match metadata, 10 Hz tracking, dynamic-event and phase CSVs, plus 25 Hz body-pose ZIPs. Exact revisions, URLs, SHA-256 checksums and bytes are recorded in `data/provenance.json`. The downloader verifies both pose archives against SkillCorner's manifest and resolves tracking Git LFS pointers. Only the supplied free data is used.

Pose coordinates are in metres with origin at pitch centre. `pose_frame / 25` and `tracking_frame / 10` are the same global video clock. The match's football clock has period offsets; never join on minute alone. Check period agreement and clock residuals at every exact 5-pose/2-tracking-frame alignment. Pose frames used as predictors always satisfy `pose_frame / 25 <= reception_frame / 10`; odd 10 Hz frames lie between pose frames, so selecting the nearest future pose would leak up to 20 ms. We use only the earlier eligible frames.

Event coordinates are normalized to a 105 by 68 m reference pitch and attacking direction. Multiply by actual pitch dimensions divided by those reference dimensions, then rotate both axes 180 degrees for right-to-left attacks when comparing with fixed tracking. Verify event direction against match metadata and measure XY residuals. Exclude receptions with more than 3 m disagreement. The two observed pitches use the reference dimensions, so non-unit scaling is implemented but not empirically tested by these games.

## Reception population and outcomes

Unit: `(match_id, event_id)` for `event_type=player_possession` and `start_type=pass_reception`. Retain matched starts; exclude explicit GK lineup roles, unknown possession ends and unlabelled pass outcomes. A successful pass with no destination coordinate is unknown and excluded. Verify possession duration against `(frame_end-frame_start)/10` to 110 ms tolerance. Tracking context requires a receiver, at least eight opponent positions, a same-period position 500 ms earlier, speed at most 12 m/s, and finite model features. Native tracking can be empty during broadcast interruptions; interpolated roster positions in the pose file must not substitute for missing native context.

Primary target is one if the possession ends in a vendor-labelled successful pass, release duration is at most 2 seconds, and receiver-at-reception X is at least 5 actual metres ahead of the current reception X. Gain includes the player's carry before releasing. All other known outcomes are zero. This target excludes carry-only progression, shots, longer possessions and later possession value. It is not a universal measure of a good reception. Event precision is 100 ms; do not interpret 25 Hz pose as more precise contact timing.

Descriptive outcomes are release duration, vendor EPV-for end minus start, and a limited retention proxy: 1 for successful pass/foul suffered, 0 for failed/offside pass or possession loss, unknown for shots/clearances/unknown ends. The retention denominator excludes unknowns. This is not possession survival at a fixed horizon. Model outputs are provider-derived annotations, not independent human ground truth.

## Baseline before orientation

Run `python -m open_body baseline` first. Save the eligible table, full input/exclusion audits, benchmark and model scores. The stage emits a hash-bound validation marker only after both directions run. A first-half/second-half smoke test on 1925299 confirmed execution before orientation implementation; that result is not used as match-separated evidence.

The baseline uses reception-time tracking X (towards attack), absolute Y, nearest-opponent distance, number of opponents within 5 m, and the receiver's backward-looking 500 ms speed. Opponents are identified from the lineup, with native tracking's on-pitch positions. A constant model predicts training prevalence. Models are `StandardScaler` plus scikit-learn L2 logistic regression, C=1, intercept, fixed settings. Fit all transforms and coefficients on the training match only. No test-set tuning, resampling by frame, player identity feature or outcome-based class balancing is used.

## Shoulder measurement

For left shoulder L and right shoulder R, compute forward proxy `v = (-(Ry-Ly), Rx-Lx)` and heading `atan2(vy,vx)`. This is the official tutorial's convention. Reject missing/invalid shoulders, horizontal shoulder width outside 0.20–0.70 m, either shoulder's estimated error above 15 cm, or a shoulder-midpoint to XY distance above 2 m. The latter is an additional alignment sanity gate. Geometry cannot certify left/right identities or validate the model against real body-heading ground truth.

Average unit vectors over the trailing 120 ms; require at least 3 valid samples, newest sample at most 80 ms old, no gap over 80 ms, and mean-vector length at least 0.8. This is causal circular smoothing, not centred smoothing or angle interpolation. A second such window ending 400 ms earlier supplies the absolute wrapped net heading change divided by 0.4 s. If unavailable, set the turning term to zero with an explicit missing indicator. This is average net turn rate, not instantaneous angular velocity or cumulative total rotation.

Augmented predictors are cosine/sine relative to attack, cosine alignment to the ball 200 ms before reception (relative to the receiver's reception position), cosine alignment to the nearest opponent at reception, pre-reception net turn rate and its missing flag. Both baseline and augmented models train and test on identical orientation-eligible rows. No post-reception heading, future movement, intended action, possession end, EPV, pass outcome or target-derived quantity enters either model.

For description only, group attack-relative shoulder heading into forward (<45 degrees), sideways (45–135), backward (>135). These categories are not observed technique labels. Report alignment with the next 500 ms movement only when displacement exceeds 0.25 m; this future-derived quantity is never a predictor.

## Evaluation and uncertainty

Primary chronological train/test: 1925299 / 1996435. Reverse train/test is a diagnostic. Report per-match sample size/prevalence, log loss, Brier, AUROC and five fixed calibration bins. Log loss is primary. Save every held-out probability and paired per-event loss difference. A negative augmented-minus-baseline difference favours orientation.

Conditional 95% intervals use 2,000 paired bootstrap resamples of non-overlapping five-minute blocks in the held-out global frame clock; resample entire blocks and keep the models fixed. These intervals address within-match temporal dependence approximately. They do not include uncertainty from training matches, pose estimation, vendor annotation errors, feature selection or unseen match populations. With only two matches, a match-cluster bootstrap is not meaningful. No population p-value is reported.

The pilot criterion requires a negative difference in both match directions and an upper interval bound below zero in the chronological holdout. Sensitivities are not candidates for selecting a winner: error gates 10/20 cm; raw single-frame or 240 ms smoothing; a feature cutoff 100 ms earlier; deterministic independent Gaussian heading noise with 15/30-degree SD; and a midfield-only rerun if both samples have at least 30 receptions and training contains both outcomes. Noise is an uncalibrated stress test, not a measurement-error confidence distribution. Sensitivity samples can change, so each compares baseline and orientation on its own identical rows.

Descriptive category fractions include Wilson intervals as unadjusted reference intervals, which assume independent Bernoulli observations and understate dependence. They cannot establish an orientation effect. Counts, EPV availability and retention-proxy denominators accompany category summaries. Report pose coverage among all roster frames, active-player frames and eligible receptions, plus location, pressure, visibility and outcome differences between retained and rejected receptions.

## Reuse and inspection

`data.py` streams files and validates tracking/events. `orientation.py` supplies geometry, causal windows and full-match pose audits. `models.py` fits fixed models and calculates metrics/paired intervals. `baseline.py` and `experiment.py` run the stages. Output caches are bound to pose hashes, baseline content, configuration and orientation code. Tests cover real label reconciliation, coordinates, angle wrapping, degenerate geometry, future-frame exclusion, missing windows, train-only transforms and independent metric calculations. The viewer and rendered demo consume saved results and real clips after calculation validation.

### Alignment repair identified during full-match validation

Before fitting any orientation outcome model, the first full pose scan reproduced the publisher's frame/pose totals and exact clock agreement but found a long tail of pose-XY versus native-tracking XY residuals (99th percentile about 9.74 m). The provider warns that the streams are generated separately. A small typical residual does not make the tail harmless. Each causal reception-window sample therefore additionally requires native tracking in the same period at the most recent earlier 10 Hz frame and pose XY within 2 m of that position. Missing native context is not filled from pose. This deterministic consistency gate was added as a data-quality repair before seeing orientation evaluation results. Full-frame shoulder-gate coverage is geometric; reception coverage additionally includes this native alignment gate. A residual does not uniquely diagnose a wrong identity or identify which stream is correct.

The provider's full temporal estimation pipeline is not open here. “Causal smoothing” describes this project's trailing feature windows; it is not a verified guarantee about SkillCorner's internal estimators or real-time availability.
