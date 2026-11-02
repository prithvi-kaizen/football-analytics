# Feasibility assessment, 28 October 2026

Decision before model implementation: proceed with a three-match, ground-pass prototype. It is feasible to measure modelled obstruction and compare proxy agreement. It is **not** feasible to validate passes prevented, tactical intent, or causal defensive value from this release alone.

## Source and coverage

[SkillCorner Open Data](https://github.com/SkillCorner/opendata), released with PySport, exists and is publicly accessible. Use revision `4340d274572876239c154c90bc507a9b3250a656`. The pinned match index lists **20** matches, although the README describes ten. This discrepancy is retained. Three full tracking files already exist in this workspace with source receipts; the new loader must verify their SHA-256 hashes against a separate source lock. This avoids paying for or scraping any data. The live repository was also checked on 28 October; the project deliberately uses the recorded revision, without claiming it is the latest commit.

The repository MIT licence permits reuse with its copyright and permission notice retained. Keep `docs/source/SkillCorner-LICENSE`, credit SkillCorner and PySport on figures and in the viewer. No footage is used. Player-season aggregates and body-pose data are outside scope.

Development: Auckland FC vs Newcastle, 30 November 2024 (1886347). Held-out evaluation: Brisbane FC vs Perth Glory, 21 December 2024 (1925299), and Sydney FC vs Adelaide United, 1 February 2025 (1996435). These are convenience samples already cached by earlier projects, not randomly sampled league matches or globally unseen data. Holdout means excluded from model development in this implementation.

## Actual inspected schema

Tracking JSONL has `frame`, `timestamp`, `period`, `player_data`, `ball_data`, `possession` and camera projection. Player entries contain `player_id`, `x`, `y`, `is_detected`. Join these IDs to metadata `players[].id`. Coordinates are centred metres; pitch dimensions are match-specific. Sampling is 10 Hz. Null-period rows occur. Use frame and period keys, not timestamp multiplication: frame 10 starts each first half at 00:00.0. Match metadata supplies period start/end frames and home attacking direction. Dynamic-event x/y coordinates are not substituted for tracking coordinates.

The event CSV has **322 columns**. In match 1925299 it has 5,222 rows: 2,734 passing options, 1,054 player possessions, 936 on-ball engagements and 498 off-ball runs. Crucially, `passing_option_ease_start` and `overall_pressure_start` are possession-level categories, not labels for each candidate lane. In the three matches, ease is missing on 80/990, 118/1,054 and 107/1,005 possession events respectively. Ease IDs run from 1=very_easy to 5=very_hard; pressure IDs from 1=no_pressure to 5=very_high_pressure. The README documents the order; the actual text/ID pairs were inspected. Use explicit text mappings and validate agreement with IDs.

Events have `event_id`, `frame_start`, `frame_end`, `period`, `player_id`, `team_id`, `phase_index`. Event IDs are unique only within a match. Phases have frame intervals and possession team. Use half-open phase intervals and exact tracking joins. Audit missing joins and exclusions, rather than imputing labels or coordinates.

## Research context

1. [Spearman et al., Physics-Based Modeling of Pass Probabilities in Soccer (2017), author-uploaded paper](https://www.researchgate.net/publication/315166647_Physics-Based_Modeling_of_Pass_Probabilities_in_Soccer). Uses arrival and control times to model passes. Establishes the physical basis; this project does not reproduce its fitted ball-control probabilities.
2. [Spearman, Beyond Expected Goals (2018), Hudl paper](https://static.hudl.com/craft/downloads/SSAC2018_Beyond_Expected_Goals.pdf). Values off-ball positioning through pitch control and scoring opportunities. This project concerns defensive lanes and supplies no goal-value conversion.
3. [Laurie Shaw, Friends of Tracking pitch-control implementation](https://github.com/Friends-of-Tracking-Data-FoTD/LaurieOnTracking/blob/master/Metrica_PitchControl.py). Public code uses reaction-position projection followed by constant-speed arrival and a logistic uncertainty function. Our reaction-time and maximum-speed defaults are motivated by this implementation; our transition scale is an explicitly uncalibrated modelling choice. No code is copied.
4. [Dick, Link and Brefeld (2022), Who can receive the pass?](https://link.springer.com/article/10.1007/s10618-022-00827-2). Models receiver availability, including interception along a trajectory, pass variation and learned player motion. Evaluates on 58 matches. Maximising interception along a path is established; we use a much simpler transparent surrogate and no learned motion model.
5. [Touchline Theory, Uncovering the Cover Shadow](https://touchlinetheory.com/uncovering-the-cover-shadow/). Tactical motivation for marking the route between carrier and receiver and for changing passing angles. It is an explanation, not a quantitative validation study. The image-proxy URL in the brief was inaccessible; the original article was located and read.

Contribution: a reproducible public-data engineering study that contrasts a finite corridor baseline with an arrival-time surrogate, exposes single-defender removal effects, decomposes temporal changes with fixed defender states, and reports sensitivity and provider-label agreement honestly. Neither cover shadows nor arrival-time interception are new methods. The original contribution is this bounded implementation and audit, not a claim of research priority.

## Question and falsifiable protocol fixed before scoring

Football question: at possession starts with at least two plausible ground-pass targets, does defender reachability explain constraints that a narrow static corridor misses?

Primary hypothesis: the arrival-time model's mean obstruction across candidate lanes has a higher positive Spearman association with provider passing difficulty than the baseline's fraction of obstructed corridors, on the held-out matches. Report each match and a pooled within-match, possession-phase-cluster bootstrap of the paired correlation difference. Support requires a positive difference in both matches and a pooled 95% interval entirely above zero. Failure is a legitimate result. This evaluates proxy agreement, not independent football accuracy.

Baseline first: a target lane is obstructed when any defender is within 1 m of the finite line segment, excluding 2 m at either end. Proposed model only after real-data baseline range, geometry and coverage checks pass: sample that segment at <=0.5 m spacing, compare assumed ball travel time with approximate defender arrival using only past velocities, then map the best margin to a bounded score. It is not a calibrated probability.

Candidate targets come from teammates' current locations (5–40 m, outfield, on pitch), excluding the carrier and players clearly beyond the ball and second-last defender in the attacking half. This is an approximate snapshot offside screen, not adjudication. Goalkeepers remain eligible defenders. Use a confirmed carrier, all 22 positions, a nearby low ball, a matching in-play phase and valid past-only defender velocities. Do not select candidates using provider passing options, targeted players or pass outcomes.

Metrics: coverage/exclusions and visibility; Spearman correlations against difficulty and pressure; paired clustered uncertainty; model disagreement; per-defender marginal obstruction on the same target set. Secondary checks: zero-velocity arrival, ball speeds 12/18 m/s, defender speeds 4/6 m/s, reaction times 0.4/1.0 s, corridor widths 0.75/1.5 m, spatial sampling 0.25/1 m, narrower target range, and an all-detected subset. Do not choose a winning parameter setting from test results.

## Quality risks and limits

- High: off-camera players and the ball can be extrapolated. Preserve flags and quantify a strict observed subset. Extrapolated coordinates are not missing observations recovered with certainty.
- High: proprietary categories are derived from the same tracking and may use related geometry. Association can reflect shared inputs. They are not independent ground truth.
- High: only three selected matches; temporal dependence and shared teams/players defeat naive frame-level confidence intervals. Cluster by match/phase; intervals condition on these two test matches and do not estimate league generalisation.
- Medium: identity errors, missing carrier IDs, substitutions, gaps and unrealistic jumps. Reject incomplete frames and invalid past windows, log exclusions, never smooth across gaps or halves.
- Medium: ground-pass assumption, fixed receiver positions, uniform reaction/speed, no orientation, curved passes, ball deceleration or technical skill. Restrict interpretation to the model.
- Medium: selecting possession starts uses a provider event boundary, potentially at reception. Features can only use tracking at/before that frame; this is retrospective event-conditioned analysis, not a live detector. No end fields or future frames enter scoring.
- Critical for causal claims: unattempted passes have no observed completion outcome or intent. Removal is a mathematical ablation, not a behavioural counterfactual. Do not call obstruction goals saved, prevented passes or player quality.

## Smallest end-to-end acceptance criteria

Verified source lock; executable audit; separately validated real-data baseline; independent model/data tests; frozen configuration; held-out results with conditional uncertainty and sensitivity; a small pitch replay with timeline and visible assumptions; 20–40 second demonstration; source-backed README/methodology/results post. Keep all work inside this new project and preserve unrelated workspace changes.
