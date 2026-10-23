# Source audit before implementation

Inspected 22 October 2026, before analytical code was written. Source: Hudl/StatsBomb Open Data revision `4b73468fc5b0f1950f9f66fada70ad3a4f9327cb`.

## Availability and fields

- UEFA Euro 2024: competition 55, season 282, 51 matches.
- UEFA Women's Euro 2025: competition 53, season 315, 31 matches.
- Official match lists advertise 360 availability for both. Per-match downloads and event joins must still be audited.
- Events v4.0.0: `id`, `index`, `period`, period-relative `timestamp`, `minute`, `second`, `possession`, team/player IDs, `location`, `under_pressure`, and nested `pass` fields including `recipient`, `length`, `angle`, `end_location`, `height`, `body_part`, `type`, `outcome`.
- 360 v1.0.0: `event_uuid` joins to event `id`; `visible_area` is a closed polygon, sometimes empty; `freeze_frame` players have `location`, `teammate`, `actor`, `keeper`. There are **no player identifiers** except the actor flag.
- Coordinates are 120 by 80 StatsBomb units, y increasing down the diagram; the event actor's team attacks x=120. Frames already share the linked event orientation. Do not rotate halves again. Units are normalized coordinates, not surveyed metres.
- Inspected real events and 360 for Germany vs Scotland, match 3930158: 3,372 events, 3,090 frames. These counts describe this pinned file, not an expected count for every match.

## Terms

Read upstream README and the entire 8 September 2023 Public Data User Agreement in `source/LICENSE.pdf`. This is freely accessible research data, **not an OSI open-source data license**. Analysis may be shared; the agreement restricts commercial exploitation and redistribution of raw data (sections 1.2 and 7). Publications must credit StatsBomb with its logo (1.4). The agreement asks users to register their interest. Keep raw downloads and row-level derived datasets local and out of Git. Publish code, aggregate findings and attributed charts; do not bundle raw snapshots or training tables. The code license does not relicense the data. Dependencies will be open source; no paid APIs or scraping.

## Limitations fixed before coding

1. Broadcast frames omit off-camera players; empty visibility and manually placed players outside the visible polygon occur. Unseen defenders are not zero defenders. Missing/malformed frames and joins need explicit counts. Final raw-coordinate inspection also found finite player locations just beyond touchlines: retain those positions for defender geometry, count them separately, and withhold off-pitch candidate probabilities.
2. Snapshots are not tracking: no velocities, off-ball trajectories, pass speed, defender reaction or certainty about intended targets. Anonymous candidates cannot be named reliably.
3. Recorded endpoints, pass length/angle derived from endpoints, outcomes, duration, future receipts and future events must not enter prediction features. Endpoints are permitted only for actual-lane display and descriptive statistics.
4. Strict event-context models use origin and period; collector pressure is display-only because its timing may overlap event duration. The 360 addition uses pre-pass spatial context. Neither model alone distinguishes candidate targets.
5. An experimental target model may use the named intended recipient solely to assign a training target from **earlier** same-team event origins and the current anonymous frame: short age, tight distance, clear nearest-neighbor margin. Never use an endpoint or future event. This proxy is not verified identity and selects a biased subset, including more recent ball participants. Report counts and success rates of retained and excluded attempts. Target geometry is therefore not a pure event-only feature set.
6. Candidate target predictions use current visible teammate positions, assume a ground pass and stationary receiver, and need training-support flags. They are hypothetical estimates outside the observed choice policy, not validated counterfactuals or proven missed opportunities.
7. Forward coordinate gain is territorial progress, not expected threat, goal value or tactical quality. Defensive-line breaking, offside, body orientation and coach intent cannot be established here.
8. Partition entire matches, stratified by tournament. Fit transforms and target-support ranges on training only. Fixed logistic regression first; fixed gradient boosting second. Disable boosting's random row validation. Keep holdout games out of the app's training model and evaluation selection.
9. Small samples cannot support player rankings, stable tactical claims, tournament generalization or calibrated claims about alternative passes. Report metrics with match-cluster uncertainty where sufficient held-out matches exist.

## Primary sources

- https://github.com/hudl/open-data/tree/4b73468fc5b0f1950f9f66fada70ad3a4f9327cb
- https://github.com/hudl/open-data/blob/4b73468fc5b0f1950f9f66fada70ad3a4f9327cb/LICENSE.pdf
- https://github.com/hudl/open-data/blob/4b73468fc5b0f1950f9f66fada70ad3a4f9327cb/doc/Open%20Data%20Events%20v4.0.0.pdf
- https://github.com/hudl/open-data/blob/4b73468fc5b0f1950f9f66fada70ad3a4f9327cb/doc/Open%20Data%20360%20Frames%20v1.0.0%20(1).pdf
- Conor Sharpe, Hudl, 17 June 2025: https://www.hudl.com/blog/xpass-360-upgrading-expected-pass-xpass-models . Conceptual reference only; this project does not reproduce Hudl's proprietary imputed targets or model.
