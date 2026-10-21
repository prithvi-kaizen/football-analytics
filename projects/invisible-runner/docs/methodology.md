# Methodology

## Population and coordinate frame

Analyze specified match IDs from the pinned public SkillCorner revision. Default smoke scope is the first 3,000 source lines, equivalent to source frames 0–2999 at 10 Hz, including ten pre-match null-period frames. It contains valid player frames 10–2999, not a complete five minutes of in-play football. Full-match scope is an explicit option. The current source index contains twenty fixtures although its README describes ten. This implementation supports explicit IDs rather than silently selecting a different population.

Join tracking `player_id` to match `players[].id`. Preserve centred, physical-metre coordinates and each match's pitch dimensions. No rescaling to 105 by 68 m. For attacking progress use `sign*x`, where sign is +1 for left-to-right and −1 otherwise; rotate neither the display nor the underlying tracking. `home_team_side[period-1]` determines direction; opponents use the inverse. Validate each phase's direction against it.

Join events and phases on frame and period. Frame indexes include offsets: use `(frame - match_periods.start_frame)/10 + (period-1)*2700` for display clock. Second-half match clocks can overlap first-half stoppage-time clocks, so they are never join keys. Phases use [start, end); provider player-possession intervals use inclusive endpoints to conservatively exclude touches.

## Stage 1: ingestion and cleaning

Downloads stream from pinned GitHub raw/LFS URLs. The sample stops after the requested lines rather than downloading a full match and trimming locally. Event and phase CSVs remain complete to preserve interval joins. Each cache entry records URL, revision, SHA-256, size and prefix limit; validate hashes on reuse. Full and partial files have different paths. Writes use a temporary file and atomic rename. A source connection failure leaves no partial final file.

Fail on malformed JSON, duplicate/reversed frames, duplicate players within a frame, invalid match IDs, reversed intervals, overlapping phases or direction conflicts. Skip pre-match null periods, unknown players, nonfinite/missing positions and positions more than 5 m outside the physical pitch; count these exclusions. Preserve all detected/extrapolated flags.

For each player and period, find contiguous frame segments. Flag both ends of a raw one-frame jump exceeding 12.5 m/s **before** smoothing; leave their smoothed coordinates missing. Break again at every gap. Do not interpolate missing data. Apply a seven-frame, order-two Savitzky-Golay smoother per valid segment. Central finite differences estimate speed at 0.1 s spacing; path distance is the sum of Euclidean smoothed steps. Exclude the first/last three frames of each segment from detection and reject candidate intervals touching those exclusions. Smoothing uses later positions; this is retrospective analysis.

## Stage 2: run detection

The default candidate is a maximal contiguous interval satisfying all of these:

- Outfield runner with smoothed speed between 5 and 12.5 m/s; no threshold hysteresis or gap bridging.
- In-play phase confirms their team in possession. If tracking supplies a team, it agrees with that phase.
- Tracked carrier is not the runner, no provider `player_possession` interval covers the runner, and tracked ball distance is at least 3 m. Ball coordinates may be extrapolated; report endpoint ball detection and fraction of run frames with known carrier identity.
- Runner remains inside the pitch and away from trajectory segment boundaries.

Retain intervals lasting at least 1 s, travelling at least 5 m, and progressing at least 3 m toward goal. Duration is `(last_frame-first_frame)/10`, not number of samples divided by ten. No learned model or outcome prediction is used. Missing carrier identities, noisy ball locations and threshold crossings can fragment or misclassify runs.

Provider off-ball-run labels, EPV, future receptions, goals and season aggregates are never detector inputs. Provider possession intervals supply only an exclusion of on-ball movement. No machine-learning split is needed for this deterministic baseline. Any later fitted model must split whole matches before tuning, fitting preprocessing or constructing comparison groups; keep the test matches untouched. Season aggregates computed across test matches cannot become predictors.

## Stage 3: geometry and defender response

Endpoint context must have the same opponent IDs at both endpoints and the same continuous tracking segment for each. At least eight opponents must be present; in real match data, their IDs must also exactly match the full active opponent roster from metadata playing intervals at both frames. Substitution transitions or missing opponents invalidate context metrics rather than inflate free space. If the preselected teammate is missing or crosses a segment boundary, teammate metrics are missing. Extrapolation remains allowed but disclosed. Missing metrics remain missing, never zero.

| Output | Definition | Interpretation limit |
| --- | --- | --- |
| Distance | Sum of smoothed inter-frame Euclidean steps, metres | Sensitive to smoothing and identity errors |
| Progress | End minus start x, signed toward the opponent goal | Forward displacement, not tactical value |
| Runner separation change | End minus start distance to nearest opponent | Nearest opponent may change identity |
| Behind line | Runner starts ≥0.5 m before and ends >0.5 m beyond the moving second-deepest **outfield** opponent | Defensive-line proxy; not a true line model or offside ruling |
| Wide channel | Ends at absolute y ≥0.3 × pitch width, with ≥2 m outward movement | Outer 20% on either side; other wide runs excluded |
| Toward space | Nearest-opponent clearance increases ≥2 m during a qualifying forward run | No intent or reachability inference |
| Nearby defender count | Opponents within 10 m of runner at start | Preselected cohort; can be zero |
| Defender displacement | Mean start-to-end displacement of that same nearby cohort | Cannot attribute motion to runner |
| Defender toward endpoint | Mean defender displacement projected toward runner's final position, using direction from each defender's start | Signed response proxy; no causal interpretation |
| Teammate clearance change | End minus start nearest-opponent distance at the teammate's current positions | Includes receiver movement |
| Free receiving patch | Fixed grid-cell area near the teammate's **start** position, outside opponents' 3 m discs | Geometric opportunity proxy; ignores ball/pass accessibility |

Run types overlap; unknown behind-line/toward-space status remains missing when contextual tracking fails. A receiver is selected before measuring change: nearest same-team outfield player other than the runner, no more than 10 m behind in attack-normalized x. No future maximum-space-gain selection.

The patch contains 1 m grid-cell centres within a 6 m radius of this starting receiver location, clipped to pitch bounds. A centre is free if its distance from **every** opponent is at least 3 m. Area equals number of free centres × 1 m². Compare precisely the same centres at start/end. This grid approximation has no statistical error bar and is not a probability, pitch-control model, Voronoi area or reachable passing region. The time-resolved replay applies the same definition and leaves invalid frames missing.

`runner_detected_fraction` covers every runner frame. `context_endpoint_detected_fraction` covers all opponent and selected teammate observations at both endpoints only, including goalkeeper. It does not describe visibility between endpoints. The strict UI quality filter also requires the tracked ball detected at both endpoints. Fully observed endpoints do not rule out extrapolation inside a continuous context trajectory.

## Validation and denominators

Unit fixtures are explicitly synthetic and exist only in tests. Exact tests verify metre distances, linear speed, period offsets, direction reversal, inclusive possession exclusions, half-open phases, stationary-defender zero changes, fixed-cell area, jumps, missing context and cache corruption. Real-data tests execute the sample pipeline and full-match direction/timing checks. AppTest exercises controls and threshold recomputation. Browser inspection checks rendered charts and responsive layout.

Descriptive provider comparison: same-player, same-period temporal intersection-over-union ≥0.3, considering provider runs fully contained within loaded frame bounds. A baseline run can overlap multiple provider labels and vice versa; counts are not precision/recall. Provider annotations derive from the same tracking and have different thresholds. They cannot independently establish accuracy.

Report the number of all qualifying runs, number with valid patch estimates, detected-runner count and full endpoint-context visibility separately. Runs can overlap in time and share teammates or defenders. Do not use their count as an independent statistical sample or add space gains as if they were unique square metres created. Sensitivity repeats the detector at 4.5, 5 and 5.5 m/s with all other settings fixed.

## Causal stretch goal

Not implemented. A later comparison could match situations on **pre-run** ball position, possession phase, attacking direction, player spacing and match context, with controls drawn from separate possessions and match-level held-out validation. Unmeasured tactical intent and camera extrapolation would still prevent a causal interpretation without stronger identification. The current project deliberately reports measurable associations, without inventing a counterfactual or assigning player credit.
