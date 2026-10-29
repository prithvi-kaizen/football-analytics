# Methodology

## Target and analysis population

The estimand is an algorithmic change of plausible covering defender for an off-ball attacker in central receiving space. It is not a change of known coaching responsibility. The question, splits, thresholds and hypotheses are recorded in `feasibility.md` and `configs/pilot.json`.

We use both halves of development match 1925299 and held-out match 1996435 at the native 10 Hz. Provider `build_up`, `create` and `finish` phases define settled-possession contexts. For each opposing outfield player, require all of:

- Attacker is in the central two-thirds of pitch width.
- Attack-normalized x is within 25 m in front of, or 3 m beyond, the second-deepest opposing outfield defender. This is a receiving-space proxy, not a measured midfield/back-line zone or offside rule.
- Ball coordinates are finite; attacker is over 3 m from the ball and is not the named carrier.
- Tracking possession and provider phase possession are both known and agree. Tracking and phase periods agree.
- Exactly ten opposing outfield players have valid positions and velocities. Goalkeepers never enter the analytic marking graph.
- Attacker position and velocity are valid. Reject positions more than 5 m outside the pitch; reject both ends of consecutive speed steps above 12.5 m/s.

No empty frame, missing observation or possession conflict is imputed. A causal velocity estimate uses displacement over the previous 0.3 s, with all four observations present, clean and in the same period. Extrapolated positions are permitted in the primary analysis and flagged. A separate detected-only sensitivity requires the attacker and all ten defenders to be detected at all four velocity-support frames.

Each attacker is segmented into contiguous eligible frames with the same provider phase, period, possession and defensive lineup. Segment boundaries reset all state. This is conservative: some real transfers crossing phase labels will be lost. Multiple attackers contribute at once, so attacker-minutes exceed team possession minutes.

## Baseline

At every eligible attacker-frame, select the opposing outfield player at minimum Euclidean distance, breaking ties by stable player ID. This baseline always supplies a defender, even at very large separation. It makes no claim of marking responsibility. Independently check one uniformly chosen observation from each of 500 randomly ordered eligibility segments per match using scalar `math.hypot` on raw coordinates. This is an engineering check, not a uniform frame sample or tactical accuracy estimate.

## Graph and edge scoring

For attacker position a, defender position d, attack sign s, velocities va and vd:

```
r = d - a
distance = ||r||
radial_separation = dot(vd - va, r) / max(distance, 1e-6)
predicted_distance = ||r + 0.4 * (vd - va)||
goal_margin = s * (dx - ax)
local_line_depth = median x of defender + two nearest outfield teammates
line_offset = |ax - local_line_depth|
score = distance + 0.35 * clip(radial_separation, -3, 6)
                 + 0.12 * line_offset
```

Positive radial separation means the pair is moving apart. Positive goal margin means the defender is closer to the defended goal along x. The local median is a simple structural reference; it does not infer an actual formation line or a coach-defined zone. It can shift when nearest teammates change. Its term is deliberately small and is ablated in sensitivity tests.

Store directed weighted bipartite edges within 8 m. A plausible entry edge requires distance <=6 m, goal margin >=-1.5 m and predicted distance <=8 m. A retained assignment can remain to 7.5 m while satisfying the same goal-side and prediction gates. Scores use metres-equivalent units, not probabilities or calibrated responsibility confidence. Positive scores are ranked within an attacker, never interpreted as defensive value.

Each attacker independently selects a covering defender. This permits a defender to be the best option for several attackers, which is tactically plausible but not proof of capacity. Record an explicit shared-incoming flag instead of enforcing arbitrary one-to-one matching.

## Causal assignment and hysteresis

An unassigned attacker enters a state only when the best plausible defender persists for five consecutive bins. While assigned, a challenger must have a score at least 0.75 m-equivalent lower for five bins. Invalid retention releases the defender immediately; the new candidate must then satisfy entry confirmation. Five 0.1 s bins represent 0.5 s of exposure, with 0.4 s between the first and fifth sample timestamps.

Assignments use only present and preceding samples. A prefix-invariance test verifies that changing later scores cannot change earlier assignments. Event extraction is retrospective: it requires at least five bins of incoming stability. It must not be described as an online anticipation model.

## Candidate transfer and gap definitions

Use outgoing and incoming assigned runs of at least five bins, with different defender IDs. Permit one intervening unassigned run of at most 20 bins. Never bridge unknown or ineligible data. Require at least 2 m net attacker displacement between the local two-second flanks, truncated to the eligible segment. This excludes stationary reassignment and may miss curved runs returning to the same position.

The transfer measurement window comprises up to the last five outgoing bins, all intervening unassigned bins, and the first five incoming bins. At each bin, ask whether **any** of the ten outfield defenders meets the entry geometry. The gap is independent of which defender hysteresis selects. Sum zero-cover bins for total gap time and measure the longest consecutive zero-cover run.

Categories are `continuous` (no zero-cover bin), `brief_gap` (some zero-cover bins but longest run <0.4 s), and `gap` (longest run >=0.4 s). They are descriptive geometric labels. Unassigned time is reported separately and can be positive even when cover is continuous. No estimate of hidden defender positions or coaching intention is added.

An ambiguity flag indicates less than 1 m-equivalent between the two best plausible scores at the incoming confirmation frame. This is a heuristic separation flag, not an accuracy or confidence estimate. Events with only one plausible entry edge have no alternative-score margin; absence of a flag does not establish clarity.

## Evaluation and uncertainty

The baseline was implemented and validated before the scorer. Parameters were recorded before proposed-method evaluation and saved with SHA-256 in `outputs/frozen-config.json`. The held-out data are never used to choose a winning threshold. All diagnostic sensitivity settings are reported, including the 8 m radius bundle which also increases release and prediction radii so entry remains usable.

Operational metrics on the same eligible population:

- Identity changes include changes between distinct assigned defenders across an unassigned interval within a segment. A return to the same defender is not a change. Report direct adjacent changes separately.
- Interior assigned runs shorter than five bins exclude first/last segment runs, which are censored by eligibility.
- Assignment availability is assigned frames divided by eligible frames. Geometry support is the selected defender meeting entry geometry, conditional on assignment. Retention deliberately permits some assignments outside entry geometry.
- Candidate counts and durations describe the detector output; they are not annotated handoff incidence or defensive mistake rates.
- Baseline disagreement is conditional on the proposed method assigning a defender; do not silently treat abstentions as agreements.

Within held-out match 1996435, resample whole provider phases jointly across players and methods (2,000 replicates, seed 20261028), recomputing rates from summed counts and exposure. Report 95% percentile intervals for proposed-minus-nearest changes. Dependence between adjacent phases can remain, so these intervals may still be optimistic; they are not between-match generalization intervals.

Synthetic evaluation reserves seeds 1000-1099, with four scenarios per seed: stationary ambiguity, smooth crossing, delayed geometric cover and a missing interval through the crossing. Coordinates receive independent 0.15 m Gaussian noise. Ground truth uses noiseless instantaneous nearest geometry within 6 m, and unknown intervals reset identity. Match identity-change events one-to-one within 1.5 s, in temporal order. Report precision/recall/F1, excess switch counts, signed/absolute latency and longest-gap error. Seed-cluster bootstrap retains the four correlated scenarios per seed. These are noise robustness checks for deliberately simple trajectories, not estimates of professional-match tactical accuracy.

## Leakage and selection limits

No shot/goal outcomes, future EPV, provider run outcomes or other projects' labels enter the model. Present-tense provider phases and possession are derived context and may themselves use the provider's offline processing. Thus causal feature code does not make the upstream measurements an online feed. Metadata and quality of both matches were inspected before fitting any method; this is an operational holdout, not a blinded external benchmark.

The sample is two convenience-selected matches from one competition and season. Clips are conditioned on detected assignment changes, movement, eligibility and stable observations, producing survivorship and visibility bias. Every catalogue row is retained. Video examples use a documented deterministic selection rule and are illustrative, not representative. Tracking animation inspection is not video or coaching validation.
