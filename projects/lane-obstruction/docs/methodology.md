# Model and evaluation

## Population and timing

One row is a provider `player_possession` start, keyed by match/event ID. Require an exact frame/period join; an in-play phase whose team agrees with tracking; provider carrier equal to tracking carrier; a finite ball within 3 m of that player, z<=1 m and on pitch; all 22 current positions (11 per team); at least two targets; and six consecutive frames ending at the snapshot for each defender. Reject raw defender steps above 12.5 m/s. These filters define a narrow convenience population, not all defensive actions. Exclusions use a first-failing-reason waterfall.

All coordinates come from tracking in the match's native metres. No standardized event coordinates or future pass endpoint are inputs. Velocities use `(position[f]-position[f-5])/0.5 s`; each intermediate frame must be present and in the same half. There is no centred smoothing. Rejecting missing history is preferable to borrowing future positions. Event boundaries are retrospectively supplied, so this remains an event-conditioned retrospective study, not a real-time possession detector.

## Candidate lanes

At the snapshot, enumerate outfield teammates 5–40 m from the ball, excluding the carrier. Exclude off-pitch targets. A simple offside screen retains signed target x <= max(0, signed ball x, second-highest signed opponent x), with positive x oriented toward the attacking goal. This ignores exemptions, body parts and uncertainty; it is a candidate heuristic. Goalkeepers remain in the defending team. Candidate generation never reads vendor `passing_option`, targeted, received, xPass, EPV, pressure or ease fields.

The origin is the ball's current location and the destination is a teammate's current location. The model assumes an immediate straight ground pass to that fixed point. Excluding 2 m at each end reduces conflation with immediate carrier pressure and receiver marking. It also deliberately discards real interception opportunities at the endpoints. All summaries give each eligible target equal weight; threat, centrality and pass preference are not modelled.

## Baseline, implemented first

For a segment of length L with unit direction u, compute defender projection `a=(d-b) dot u`. Mark obstructed when `2 <= a <= L-2` and perpendicular distance is <=1 m. This has flat ends. A lane is blocked if any defender satisfies it. Possession obstruction is the fraction of candidate lanes blocked. `outputs/baseline_validation.json` records the real-data development gate and configuration hash; the proposed experiment refuses to run without a matching passed gate.

## Arrival heuristic

Sample each interior segment at <=0.5 m spacing. The assumed ball arrival at point q is `t_ball=distance(b,q)/15` seconds. Each defender's past velocity is capped in magnitude at the configured movement speed (default 5 m/s). Predict the position after a fixed reaction interval: `r=d+v_capped*0.7`. Approximate arrival as `0.7+max(0, distance(r,q)-0.5)/5` seconds. If q is already within 0.5 m of the defender's current position, arrival is zero. There is no acceleration, turning or control-time model.

The best interception margin is `M_dj=max_q(t_ball(q)-t_defender(q))`. A positive margin means the assumed defender arrival precedes the assumed ball arrival somewhere along the corridor. Convert it to the bounded index `O_dj=sigmoid(M_dj/0.25)`. The transition is a modelling choice, not a fitted uncertainty distribution. **O is not an interception probability.** Do not report 0.8 as an 80% chance of an interception.

For target j, team obstruction `O_j=max_d O_dj`; lane availability `A_j=1-O_j`. The max aggregator avoids an independence assumption or inflated union of correlated defender scores, but loses joint pressure effects. Team obstruction is the mean across candidate targets.

## Defensive Lane Obstruction (DLO)

For defender d at this snapshot:

`DLO_d = mean_j[ max_k O_kj - max_{k != d} O_kj ]`.

The indicator lies in [0,1]. It measures exclusive marginal obstruction within this model, with all other players fixed. Shared blocking is intentionally discounted: two equally strong blockers can both have DLO zero. It is not a fair allocation of all team defensive work. It is not causal value, prevented passes, goals saved, player quality or a simulated response to a defender disappearing. The CSV additionally records each defender's mean individual obstruction to distinguish low marginal credit from lack of reachability. No seasonal player leaderboard is produced.

## Temporal analysis

Choose the first three chronological development possessions lasting >=3 seconds with a valid continuous 2 Hz replay. They are not selected for dramatic closures or test agreement. Retain initial target identities throughout each replay, so score changes cannot arise just from dropping a target. Positions are sampled, not interpolated. The viewer shows the same precomputed Python scores; controls never silently refit the model.

At each replay frame, also score current ball/targets with every defender's position **and velocity** frozen to the first frame. `current O - frozen O` measures sensitivity to the observed defender state under fixed current attacking geometry. It is not an identified effect of a defender's decision. The observed timeline includes carrier/receiver movement and changing velocities; this fixed-state comparison makes that distinction explicit. Fixed initial targets may later fail a snapshot range/offside screen; replay is a controlled illustration, while evaluation recomputes candidates at each independent start.

## Evaluation and leakage

Configuration and feasibility protocol were written before baseline scoring. Development match 1886347 supplied engineering checks and replays. Evaluation matches 1925299 and 1996435 were not used for parameter tuning in this implementation; they were previously cached by another project. They are pipeline holdouts, not a pristine future validation set. No supervised fitting or calibration occurs.

Compare mean obstruction to **possession-level** passing difficulty at the same start. Explicitly map very_easy..very_hard to 1..5 and validate text against supplied IDs. Overall pressure is separately ordered no_pressure..very_high_pressure. Higher scores mean more constrained. Missing labels remain missing; paired comparisons use the identical jointly labelled rows. Report tie-aware Spearman correlations and their paired difference, never classification accuracy or AUC against an invented pass label.

Bootstrap provider possession-phase clusters within each match, preserving all rows in a selected cluster and recomputing ranks on every resample. Use 1,000 paired resamples with seed 31415. The pooled sample size of each match varies with cluster lengths; the number of sampled clusters per match is fixed. Report percentile 95% intervals, phase count and valid repetitions. A five-minute temporal-block sensitivity retains longer local dependence; blocks are based on absolute frame bins within each period and may be partial at half boundaries. Neither bootstrap accounts for league-level match variation with only two matches.

Support for the primary hypothesis requires positive correlation differences in both matches and a pooled interval wholly above zero. All alternatives are reported descriptively: zero-velocity arrival; ball speed 12/18; defender speed 4/6; reaction 0.4/1.0; width 0.75/1.5; spatial step 0.25/1.0; target range 30 m; strict all-player-plus-ball-detected subset. Sensitivity is not validation or parameter selection. The all-detected filter covers current snapshots; it does not independently verify tracking history even if a usable subset exists.

Neither provider ease nor pressure is independent ground truth: both are proprietary model outputs based on shared tracking. Their definitions, retrospective event selection and hidden processing can explain association. Completion outcomes exist for attempted passes, but cannot label unattempted targets or establish deterrence. Independent expert annotations, multiple unseen matches and calibrated attempted ground-pass outcomes would be needed for stronger validity claims.
