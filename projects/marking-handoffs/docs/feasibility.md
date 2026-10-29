# Feasibility assessment, 28 October 2026

## Decision

Proceed with a two-match, reproducible pilot. Public tracking can support **candidate handoffs and geometric coverage gaps**. It cannot establish coaching responsibility, communication failure, defensive mistakes or causal consequences. No marking ground truth or synchronized match video is supplied. A successful-looking transfer remains a geometric candidate.

This assessment precedes implementation of the baseline and proposed detector. The raw-data loader and audit have run; no handoff results were available when this protocol was written.

## Verified source and coverage

- Source: [SkillCorner Open Data](https://github.com/SkillCorner/opendata), revision `4340d274572876239c154c90bc507a9b3250a656`.
- The pinned README advertises 10 matches, while the actual catalogue and Git tree list **20 matches and 20 tracking LFS pointers**. This is an inventory count, not proof that every asset is complete. Saved catalogue/tree receipts are in `docs/source/`.
- The two selected tracking files were matched against upstream LFS SHA-256 and byte counts. Metadata and phase CSVs were checked against upstream Git blob hashes. Six files verified. Selection used an existing local cache for economy, not random sampling; no other project's analytical labels are imported.
- Development: 1925299, Brisbane Roar v Perth Glory, 21 December 2024. Held-out operational check: 1996435, Sydney FC v Adelaide United, 1 February 2025. These are distinct teams and matches. The second match's schema/quality audit is already visible; it is an algorithm holdout within this project, not an externally blinded dataset.
- Upstream publishes [MIT terms](https://github.com/SkillCorner/opendata/blob/4340d274572876239c154c90bc507a9b3250a656/LICENSE). Preserve that notice and credit SkillCorner. Include the notice with derived clips. Raw files are downloaded separately, not committed. No broadcast footage, paid API or additional dataset is used.

## Actual schema inspected

The raw JSONL grain is one video frame (10 Hz); player observations nest inside the frame. Frame keys are `frame`, `timestamp`, `period`, `ball_data`, `possession`, `image_corners_projection`, `player_data`. Null-period records exist. Player records contain `player_id`, `x`, `y`, `is_detected`. Positions use metres, a centre origin, length on x and width on y. Both inspected pitches are 105 x 68 m. No explicit marker or handoff labels exist.

Metadata supplies team membership, player roles, substitutions/playing intervals, pitch dimensions, half directions and half start/end frames. Frames run continuously through the halves; use half metadata for the match clock, not `frame / 10` alone. Phase CSVs contain start/end frames, period, team in possession and phase type. Join as half-open intervals. Treat provider phase and possession labels as inferred context, not independently verified truth. Do not consume shot, goal, EPV or future possession-outcome columns as detector features.

| Audit | Development | Held-out |
|---|---:|---:|
| Source frames | 61,301 | 57,621 |
| Null-period frames | 19 | 19 |
| Player observation rows | 1,054,724 | 957,682 |
| Detected / valid position rows | 57.8867% | 65.8004% |
| Period frames with no player positions | 13,340 | 14,071 |
| Out-of-bounds player rows (5 m tolerance) | 151 | 20 |
| Consecutive speed steps >12.5 m/s | 0 | 3 |
| Phase frames inconsistent with tracking period | 85 | 72 |
| Phase/tracking possession conflicts, known both sides | 5,080 | 5,000 |

Counts come from `outputs/audit-*.json` and `scripts/inspect_data.py`. Detection fractions exclude rejected positions. Empty tracking frames also lack ball coordinates. All inconsistent phase frames are quarantined, including records that wrongly label the opening seconds of half two as half one. Unknown possession is excluded; conflicting labels are excluded. Out-of-bounds observations and both endpoints of implausible speed steps are excluded. No interpolation bridges missing positions.

## Football question and pre-specified hypotheses

In central, off-ball receiving space near the defensive block during settled possession, which changes of plausible covering defender remain stable, and which contain at least 0.4 seconds with no geometrically plausible cover?

Scope: provider `build_up`, `create`, `finish` phases; central two-thirds of pitch width; attacker no more than 25 m in front of, or 3 m beyond, the second-deepest outfield defender in attack-normalized x. Require known, agreeing possession, ball position, off-ball distance >3 m, complete ten-outfield-player defensive positions and valid causal velocity estimates. This is a spatial sample of all outfield attackers, not a striker-only or proven between-lines sample. No manual role-change labels are implied.

H1, falsifiable engineering hypothesis on held-out synthetic trajectories: relative to framewise nearest defender, a distance/motion/structure score plus 0.5 s confirmation and a 0.75 m-equivalent switching margin reduces excess switches by at least 25%, with event recall no more than 0.05 lower and median confirmed-change latency <=1.0 s. Report each clause separately, including failures. Synthetic labels reflect specified noiseless geometry, not tactical truth.

H2, descriptive real-data check: the method reduces short assignment runs (<0.5 s) on the held-out match, while reporting assignment availability, geometric support and disagreement. This is not evidence of higher tactical accuracy; smoothing mechanically changes persistence. A later independent annotation study is required to test real handoff precision/recall.

## Baseline and protocol

1. Implement unrestricted Euclidean nearest opposing outfield defender on the exact same eligible attacker frames. Stable ID breaks ties. Validate sampled real outputs against an independent scalar distance computation before implementing the proposed scorer.
2. Add weighted bipartite edges within 8 m, causal 0.3 s velocities, goal-side geometry and a local teammate-depth reference. Per-attacker assignments permit many-to-many coverage; avoid inventing one-to-one marking capacity. Flag shared-defender situations.
3. Confirm changes only after sustained evidence; leave an explicit unassigned state. Reset at half, phase, possession, tracking, eligibility and attacker discontinuities. Never join a handoff through unknown data.
4. Candidate events need >=0.5 s outgoing and incoming stable runs, different defender IDs, <=2 s intervening unassigned time and >=2 m attacker movement over the local event window. A gap is a count of actual 0.1 s eligible bins with zero plausible cover, independent of hysteresis delay. Report unknown bins separately. Continuous coverage means zero zero-cover bins; 0.1-0.3 s is brief-gap, >=0.4 s is gap candidate. These are rule labels, not coaching success/failure.
5. Freeze parameters in `configs/pilot.json`; development match first, full held-out match second. Report both, with held-out inference emphasized. No event or outcome-driven tuning on held-out data. A threshold sensitivity grid is diagnostic and never used to select a winning test result.
6. Compare switch rate per eligible attacker-minute, short-run rate, assignment availability, geometric support, event counts, gap duration and baseline disagreement. Use paired **phase-cluster bootstrap** on the held-out match for switch-rate differences; frames and players are not independent samples. With one held-out match, intervals describe within-match phase resampling only.
7. Synthetic known-change tests cover stationary ambiguity, smooth crossing, delayed cover and missing data; reserve distinct seeds. Report event precision/recall/F1, excess switches, localization latency and gap error. Add translation/mirror invariance and reset tests.
8. Inspect a deterministic stratified sample of continuous, gap and ambiguous examples, including extrapolation and shared defenders. Store observations, not invented adjudications. Generate no real-world precision estimate without independent labels.

## Smallest end-to-end deliverable

Python modules, source receipts, loader audit, validated baseline, proposed temporal graph method, synthetic and held-out operational evaluation, sensitivity CSV, candidate catalogue, compact local searchable viewer, and one 20-40 second tracking-only demonstration. All clips disclose extrapolation and candidate status. Publication copy uses generated results only. Expansion to all 20 assets and expert labeling are future work, not claimed pilot achievements.
