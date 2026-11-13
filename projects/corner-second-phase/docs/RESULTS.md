# Results and uncertainty

This document was produced from the pinned 82-match run. The [protocol](PROTOCOL.md) was fixed before the full sequence analysis. The source audit returned **zero** missing/duplicate indexes or IDs, missing possession fields, missing clocks or reverse period clocks. The first-pass check revealed simultaneous defender and attacker annotations; phase attribution was then narrowed and the entire sample rerun. The current code and aggregates are the corrected analysis.

## Primary 15-second probability tree

| Stage | Count | Conditional probability |
|---|---:|---:|
| Corner restart | 817 | — |
| Observed defensive contact | 710 | 86.9% of corners |
| Attacking action strictly after contact | 389 | 54.8% of contacts; 47.6% of corners |
| Recovered second phase with a shot | 126 | 32.4% of recoveries; 15.4% of corners |
| Contact without observed attacking recovery | 321 | 45.2% of contacts |
| No recorded defensive contact | 107 | 13.1% of corners |

These branches describe event order within 15 seconds, not the final winner of possession. A later turnover can follow an attacking recovery. At the end of the window, 138 corners had reached confirmed defensive control, 238 ended by stoppage, 11 by a new restart, 17 by a goal, and 43 had contact without resolved control. The remaining episodes were still attacking or had no substantive action in the observed window. `Clearance` occurred on 425 corners; it was never used alone to infer a turnover.

The 389/817 recovery rate has a 95% match-clustered bootstrap interval of **44.1–51.3%**. The 126/817 second-phase shot-corner rate has an interval of **12.9–17.9%**. The bootstrap resamples whole matches 2,000 times, seed 13; shots within one corner and corners within one match are not treated as independent units.

## Shot activity and sensitivity

| Window | Recovery corners | Second-phase shot corners | Second-phase shots | Box-entry corners |
|---:|---:|---:|---:|---:|
| 10s | 349 | 106 | 116 | 88 |
| 15s | 389 | 126 | 140 | 117 |
| 20s | 398 | 135 | 152 | 130 |
| 30s | 401 | 146 | 167 | 145 |

At 15 seconds, the known shot phases are 69 first-ball shots (4.83 xG), 44 unopposed continuation shots (4.29 xG), and 140 after observed contact plus recovery (11.95 xG). Another **75 shots are phase unknown** because attack and defence events share a timestamp. Among **253 classifiable shot events**, 184 (72.7%) were later than the first ball, and 140 (55.3%) followed contested recovery. These are shares of events, not independent Bernoulli observations; the corner-level interval above is the inferential result. The unknown bucket means the share of *all* post-delivery danger cannot be stated exactly.

Observed time to first shot among 291 shot-producing episodes: 25th percentile 1.68s, median 2.94s, 75th percentile 5.29s. Observed time to a known episode end among 402 episodes: 2.05s, median 5.06s, 8.42s. The remaining episodes are censored at the selected horizon or remain unresolved; these are empirical distributions of observed times, not Kaplan–Meier estimates. A competing-risk/discrete-time hazard model is not fit because event ties and overlapping outcomes make its risk sets difficult to defend with this feed.

## Defensive transition and context control

Confirmed defending control occurred on 138 corners. Nine of those had an opposition shot within a *further* 15 seconds: **6.5%**, exact Clopper–Pearson 95% interval **3.0–12.0%**. This is a conditional descriptive rate; follow-up time extends beyond the initial corner window. In the women's tournament, the count is only 2/52, so a point estimate alone would be misleading.

A seeded, within-match **context benchmark** samples one open-play pass in the final third per corner, at least 30 seconds from any corner. Among 817 such passes, 216 (26.4%) had an attacker act after defensive contact and 30 (3.7%) had a shot after that recovery. Its match-bootstrap intervals are 23.1–29.7% and 2.4–5.3%. This is a negative-control-style comparison for whether the sequence code produces second phases everywhere. It is **not** a causal null: final-third passes and corners differ in selection, field position and defensive shape. The reproducible seed and counts are in [context_control.json](../results/context_control.json).

## Scope decisions

The source inventory also lists men's Euro 2020, Women's Euro 2022, World Cup 2022, Women's World Cup 2023 and Women's Super League 2023/24. They could expand or test external validity, but were not combined here because tournament era, event coverage and women's/men's contexts require separate audits and reporting. The two primary tournaments are already complete in the local verified cache and match TacticAI Lite's original sample, making the change in outcome definition directly inspectable. The provider inventory is not evidence that the additional match event files passed this sequence audit.

The pass-length plus named-recipient check labels a short delivery as `short_verified` for exploratory inspection, but it does not prove a designed short-corner routine. Direct/short comparative rates are therefore withheld. A team hierarchy is also withheld: 82 matches spread across two distinct tournaments provide too few independent team-match clusters for a credible team ranking. Neither omission changes the pooled, match-clustered descriptive estimates.
