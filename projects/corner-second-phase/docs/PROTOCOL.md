# Frozen sequence protocol (13 November 2026)

Source: the locally cached StatsBomb open event files at revision `4b73468fc5b0f1950f9f66fada70ad3a4f9327cb`, audited in TacticAI Lite. The main sample is every match in men's UEFA Euro 2024 and UEFA Women's Euro 2025 (82 matches). The two tournaments are reported separately. No 2026/27 match is in this sample.

## Unit and clock

One corner restart is one observation. A Pass with `pass.type.name=Corner` or Shot with `shot.type.name=Corner` in periods 1–4 starts an episode. Provider `index` sets order; period-relative timestamps set elapsed seconds. The sequence is censored at the next restart, period end, stoppage, a confirmed defending possession, or the chosen horizon (10, 15, 20, 30 seconds). Overlapping annotation events at the same timestamp are retained in provider order. A negative clock jump or missing clock makes the state unknown. A truncated recording before a known endpoint is unknown, not a no-shot episode.

## State tree

The corner shot itself is an immediate outcome. Otherwise, a same-team shot before any defending action is an immediate shot. A defender's Clearance, Block, Interception, Duel, 50/50, Goal Keeper or Ball Recovery is *contact or attempted clearance*, not possession. The `Clearance` event is counted separately; its presence alone does not close the attacking episode. A subsequent attacking Pass, Carry, Shot, Dribble or Ball Recovery strictly later than contact is an observed attacking recovery/retention, even if the provider possession number changes. Simultaneous contact and attacking action remain unresolved for phase attribution. A defending Pass, Carry, Shot or Dribble, with `possession_team` equal to the defending team, confirms defensive control. A defending Ball Recovery alone does not. If attacking and defending evidence conflict, or play stops before either control is seen, the branch remains ambiguous/stoppage. Unopposed attacking continuation after delivery is tracked separately from contact-and-recovery.

`Second-phase shot` is an attacking shot strictly after observed defending contact and observed attacking recovery. A later shot without observed contact is continuation, not a recovered second ball. A `post-delivery shot` excludes a directly shot corner and includes both continuations and recoveries. Box entry is an attacking Pass or Carry whose endpoint enters x>=102 and 18<=y<=62 after recovery, where the start was outside the box. It is a proxy, not a possession value model. Shot xG is the provider's `statsbomb_xg`; missing xG stays missing. Multiple shots and entries are counted within one corner, and corner-level binary rates use the corner as denominator.

The counterattack risk is an opposition shot within 15 seconds *after confirmed defensive control*, before another stoppage or a new restart. This is descriptive exposure among failed corners, not a causal comparison to no corner.

## Checks and limits

Validate unique IDs and indexes, monotone clocks within a period, corner team against possession team, and possession transitions. Report anomaly counts. Use match-clustered resampling for rate intervals; for rare counts, report exact binomial intervals as a descriptive complement. Time-to-shot and time-to-possession-end use observed episodes only; right-censored cases are marked. Null control: compare attacking second-phase shots with shots by the defending team in the same initial 30-second window, without calling the latter a treatment effect. Direct/short delivery comparison is exploratory only after pass length and receipt are validated; no claim is made from swing/trajectory labels.

Public artifacts contain aggregate results and authored diagrams. Derived examples identify actual matches and phase order, but do not redistribute raw event feeds. The [StatsBomb public-data agreement](https://github.com/hudl/open-data/blob/master/LICENSE.pdf) governs use; the code licence does not cover provider data.
