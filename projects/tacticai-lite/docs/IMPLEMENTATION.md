# Implementation and metric reference

## Pipeline and provenance

`data.py` reads the official competition catalogue and match lists, selects matches in date/ID order, and downloads event/360 JSON at a pinned Git revision. A bounded four-worker pool downloads independent matches. Requests have timeouts and three attempts. Every successful file gets an atomic raw-file write and a receipt containing URL, revision, retrieval time, size and SHA-256. Missing optional 360 files receive a cached 404 receipt for offline replay. Invalid/duplicate event IDs, event indices and frame IDs fail validation; orphan 360 joins are rejected. Unreceipted cache files are rejected instead of silently assigned a revision.

`pipeline.py` extracts one row per corner and stores local CSV/JSON artifacts under an ignored output directory. The manifest records selected matches, source receipts, metric thresholds, frame coverage, excluded player entries, cluster settings and censoring. The app reads these processed outputs and never downloads data.

## Event eligibility and time

A corner is an event of type Pass with `pass.type.name = Corner`, or a Shot with `shot.type.name = Corner`, in periods 1–4. Shootouts are excluded. Events are ordered by provider `index`. The period-relative timestamp is parsed to floating-point seconds, preserving fractional seconds. Display minutes are not used to compute elapsed time.

At the corner, begin an inclusive 0–15 second window. Keep events in provider order. Ignore negative elapsed times from overlapping annotations. A different period, possession ID, opposing possession team or new restart ends attribution before that event. A time later than 15 seconds ends the window. Ball-out flags, Half End, Offside, Injury Stoppage, Referee Ball-Drop, non-advantage fouls and goals terminate after that event. An opposition defensive action within the same attacking possession does not itself terminate the sequence.

The binary target is at least one same-team shot in that sequence. Multiple shots remain one positive corner. `shots` counts shot events; `first_shot_seconds` is the first shot delay; `xg_sum` sums StatsBomb shot xG if every observed shot has it. Missing xG stays unknown. No shots in a completely observed window or known terminal sequence is negative. A recording ending without a terminal event is unknown, not negative. A positive remains positive even if later recording is truncated. Period-end negatives describe the available same-period opportunity, not an uncensored counterfactual 15 seconds of play.

Directly shot corners are positive by construction and are excluded from the delivery comparison and predictor. They remain in the overall corner inventory and inspection view.

## Delivery descriptions

Short has priority when recorded `pass.length` is at most 15 standardized units. If length is missing, Euclidean distance between start/end points provides a fallback. Otherwise use recorded technique Inswinging, Outswinging or Straight. Missing techniques are Other / unknown. The system does not infer swing from foot preference. Both length and technique describe the observed delivery, so neither enters the at-kick frame classifier.

## Spatial features and units

Coordinates use the provider’s standardized 120×80 pitch, with the actor’s team already attacking toward x=120. If the corner starts below y=40, reflect width using y′=80−y. Do not rotate x or infer a direction from period. Invalid player coordinates outside the standardized pitch, NaNs and nonnumeric values are excluded and counted. Invalid corner origins make their spatial features unavailable; locations are not clamped into valid positions.

`teammate` is relative to the corner taker. Attacking outfield statistics exclude actor and keeper. Defenders include their keeper, subject to the provider’s documented keeper-flag caveat. The box is x=102–120 and y=18–62. Near/far zones are y<36 and y>44 inside that box, relative to the normalized corner side. Centroids and lateral population standard deviation use all valid visible attacking outfield players, not only players in the box. Mean nearest-defender distance averages each visible attacking outfielder’s nearest visible defender.

The visible polygon is intersected with the box using Sutherland-Hodgman rectangle clipping and the shoelace area formula. Density is defenders inside both the box and visible polygon, divided by visible box area, multiplied by 100. Its unit is defenders per 100 square coordinate units, not defenders per square metre. Manually placed players outside the camera polygon remain in visible-player counts but not the polygon-density numerator. Missing/zero-area polygons leave density and coverage unknown.

A usable configuration needs at least four valid visible players, including at least one non-actor attacking outfielder and one defender. Fewer players cannot support the required centroid/distance features. This eligibility rule does not imply complete tracking.

## Clustering and similarity

Features are visible attackers/defenders in the box, attacking near/far counts, attacker centroid and width spread, defender mean x, mean nearest-defender distance, box-visible fraction and visibility-adjusted density. Median imputation with missingness indicators and standard scaling precedes k-means (k=4, seed 2026, 20 starts). If fewer distinct configurations exist, reduce k; if fewer than two exist or fewer than k frames are available, skip clustering. Missing/insufficient frames are unassigned.

Clustering describes all eligible frames; outcomes are absent from fitting. Nearest-corner search uses Euclidean distances in the same fitted feature space. Labels such as C1 have no inferred football meaning. Camera framing can drive similarity. Model evaluation does not use these full-dataset cluster labels.

## Learned baseline

Pass-corners with observed targets and usable linked frames are eligible. Require at least eight matches and 50 corners. `GroupShuffleSplit(test_size=0.30, random_state=2026)` selects entire held-out matches. The actual corner percentage can differ from 30%. A one-class training fold prevents fitting.

Compare a training-prior DummyClassifier with logistic regression (C=1, max_iter=2000). The latter uses the spatial features above, with training-only median imputation, missingness indicators and scaling. Exclude identities, delivery, endpoints, cluster IDs, elapsed outcomes, xG and future events. Evaluate Brier score and log loss (lower is better), plus ROC AUC and average precision (higher is better). Discrimination metrics are unavailable for a one-class test set. No tuning occurs on the holdout. Teams can overlap across different matches; a new-team or temporal generalization claim is not supported.

## Comparisons and uncertainty

Rates recompute binary successes divided by observed corners. Unknown outcomes are excluded. Separate the two tournaments. Show descriptive 95% Wilson binomial intervals, which assume independent corners and do not account for within-match dependence. Overlap or non-overlap is not a causal or multiple-comparison test. The inspection outcome filter never restricts the comparison denominator. Exports use the same comparison population as the chart.

## Validation and scope

Unit tests use explicitly synthetic fixtures only to test invariants. Real-data tests replay two cached matches; the independent validator reconstructs all source labels and shot counts with pandas clocks without calling the main labeler. Its 10/15/20-second sensitivity retains the same possession/stoppage rules. This cross-check verifies implementation agreement, not video adjudication or the provider’s collection accuracy.

The deliverable is the requested Streamlit application and a reproducible Matplotlib chart/Markdown report. The Data skill’s React/Recharts shell was not adopted because the user explicitly selected Streamlit, mplsoccer and Plotly. No second frontend, hosting deployment, synthetic findings, graph neural network or optimization recommendation is included.
