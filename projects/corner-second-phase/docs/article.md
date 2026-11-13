# The corner that never ended

*A clearance can change the ball's path without changing who attacks next. In 817 historical European Championship corners, the second ball was often the part worth measuring.*

The familiar picture of a corner ends at the first header. The delivery comes in, somebody gets a touch, and the graphic moves on to the next restart. But that touch might be a block, an attempted clearance, or a ball knocked straight back to the attacking team. Treating it as the end of the attack erases the part that defenders must organize for next.

This distinction is especially useful amid the Premier League's [2026/27 emphasis on holding and goalkeeper challenges](https://www.premierleague.com/en/news/4674118/premier-league-sets-football-principles-for-202627-season). [Contemporary reporting](https://theanalyst.com/articles/premier-league-corners-referees-grappling-holding-fouls-goals) has tracked how that interpretation changes the first five seconds of corners. The data here answer a different, older-data question: after the delivery, how often does attacking pressure visibly survive? None of these results estimates an effect of the new refereeing guidance.

I reconstructed every corner in the open StatsBomb event files for men's Euro 2024 and Women's Euro 2025: 817 corners across 82 matches. The unit of analysis is the corner, with event order checked against period clocks and possession identifiers. The main observation window is 15 seconds; the interactive explorer also shows 10, 20 and 30 seconds. A defender's Clearance, Duel, Block, Interception, keeper action, or Ball Recovery marks contact. Defensive possession requires a subsequent controlled defending action with the defending team named as possession team. An attacking action strictly after contact marks an observed recovery or retention. Events recorded at the same instant remain unresolved for phase attribution.

## The ball after the touch

At 15 seconds, defensive contact appeared on 710 of the 817 corners. The attacking side then had a later recorded action on **389 corners, 47.6% of all corners** (95% match-clustered bootstrap interval 44.1–51.3%). Among corners with contact, that is 389 of 710, or 54.8%. A clearance event appeared on 425 corners, but that is a different statement: the clearance alone says nothing about who controlled the next ball.

The second phase created a recorded shot on **126 corners, 15.4%** of the sample (95% match-clustered interval 12.9–17.9%). These corners produced 140 shots and 11.95 provider xG after an observed attacking recovery. A further 117 corners had a measured box entry after recovery. Box entry here means a pass or carry ending inside the standardized penalty area after starting outside it. It is a useful sign of continued attacking work, not a complete model of chance quality.

One sequence makes the difference concrete. In Croatia versus Italy at Euro 2024, a corner in the 26th minute was met by a clearance 1.33 seconds after delivery. Croatia recovered the ball at 3.17 seconds, carried and passed it back into the box, and shot at 7.24 seconds. A first-touch-only count would miss the continuation. The explorer presents this as a schematic sequence with observed event order, not invented tracking positions or broadcast footage.

## How much would an immediate-shot count miss?

Across the 15-second window, there were 69 first-ball shots, 44 shots during unopposed attacking continuation, and 140 shots after a contested recovery. That makes **184 later shots** against 69 immediate shots among the 253 shots whose phase can be assigned. On that known-phase subset, 72.7% of shots occurred after the first ball, and 55.3% followed observed defensive contact and recovery. The corresponding known-phase shot xG was 4.83 first ball, 4.29 unopposed continuation, and 11.95 recovered second phase.

There is an important missing slice. Another **75 shots have unresolved phase** because an attacking shot and a defending action share the same recorded timestamp. Forcing those events into either the first or second phase would make the neat percentage less trustworthy. The 72.7% figure describes classifiable shots; it is not a claim that precisely 72.7% of all danger came later. Nor does shot xG capture every entry, recycled cross, foul, or tactical advantage.

The window matters. At 10 seconds, 349 corners show a recovered attacking action and 106 have a second-phase shot. By 30 seconds those counts rise to 401 and 146. Longer windows admit more events that may be only loosely connected to the original corner, so 15 seconds is the primary view and the others are sensitivity checks. Shots and entries within one corner are correlated; uncertainty is therefore resampled by whole match, not by individual event.

## The other direction

The defending side had confirmed control within 15 seconds on 138 corners. After those confirmed turnovers, it took a shot within a further 15 seconds on nine occasions. This is a rare, descriptive counterattack risk, not evidence that taking a corner causes an opponent to shoot. A harmless clearance is also visible in the examples: Portugal's 28th-minute corner against Czechia generated a clearance, but no attacking recovery before play stopped. Both cases resist the tempting shortcut of treating every defender touch as either a completed escape or a fresh attacking phase.

The two tournaments differ in teams, context and sample size. Their separate rates are available in the explorer; neither is a Premier League forecast. Direct versus short corners are not ranked here because that would return to the initial-routine question TacticAI Lite already studied, and a length threshold alone does not validate tactical intent. The useful coaching question is narrower: when the first ball breaks loose, who can act on it next, and where is the defence positioned if they cannot?

*Source: [StatsBomb Open Data](https://github.com/hudl/open-data), pinned revision `4b73468fc5b0f1950f9f66fada70ad3a4f9327cb`; [definitions and reproduction](../README.md). Match examples and counts are historical; all graphics are original schematics.*
