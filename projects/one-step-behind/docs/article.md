# A defender can be deeper and still step with the line

At 66:58.5 in Sydney FC against Adelaide United, Adelaide's defensive line starts moving forward. Fabian Talladira becomes the deepest of its four identified players. His distance behind the median depth of the other three reaches 3.53 metres. An instantaneous depth rule would flag the sequence. Watching the movement changes the question.

By that peak, Talladira has moved 1.76 metres forward from the start of the step. His teammates' median advance is 2.36 metres. He has moved less, but he has still covered roughly three quarters of their forward distance. The line is uneven. Under the method used here, that is not enough to call him a defender who remains behind.

This is the most useful sequence in One Step Behind, a small investigation using [SkillCorner's public broadcast tracking](https://github.com/SkillCorner/opendata). The original question was straightforward: when a defensive line steps forward, how often does one player stay deeper, and how quickly does the line recover? The evidence produced a negative result worth keeping.

The frozen rules found no qualifying candidates in 49 development steps or 44 held-out steps. In the held-out match, a simpler baseline flagged two steps with an instantaneous gap of at least three metres. Neither met the complete temporal definition. These counts describe the available sample and a conservative method. They cannot tell us that the teams never had coordination problems.

Before looking for gaps, the project needed a defensible way to find a line. Metadata roles alone are insufficient: a fullback may be pressing high while a midfielder drops into cover. The method therefore accepts three to five role-listed defenders only when they are also the deepest outfield players. It requires at least two central defenders, enough lateral width and a bounded depth spread. Unclear shapes are excluded. The actual eligible sample contains three- and four-player units; no five-player unit survives these rules.

That choice makes the investigation selective. It can miss the very moments when a defensive unit changes membership or loses its shape. A result of zero could reflect coordinated movement, restrictive retrieval rules, unavailable observations, or some combination. There is no independently labelled set of defensive steps to separate those explanations.

The motion test starts with a line whose depth spread is at most three metres. All but one player must advance at least 1.5 metres over a second, with movement sustained through both half-seconds. A candidate then needs a growing gap, compact peers and no more than half the peers' median forward movement, sustained for half a second. A three-metre difference is a declared analytical tolerance, not a universal coaching standard.

These relational and temporal choices draw on published work on [player-team synchrony](https://www.mdpi.com/1424-8220/20/17/4990), [dynamic football subgroups](https://doi.org/10.1080/02640414.2020.1834689) and [formations in different phases](https://doi.org/10.3233/JSA-220620). This project uses a simpler geometric retrieval rule. It does not reproduce those studies or claim that its thresholds have tactical validity.

Coverage puts a further limit on the result. Only 57.89% of valid player coordinates in the development match and 65.80% in the holdout are marked detected. The remainder are extrapolated. Requiring all ten defensive outfielders to be detected reduces eligible time from 31.5 to 5.2 minutes in development and from 23.2 to 9.4 minutes in the holdout. That stricter population yields eight and 22 steps respectively, again with no qualifying candidate. It is a different population, not a direct validation of every original step.

The held-out zero also persists across gap thresholds from two to four metres and persistence requirements from 0.3 to 0.8 seconds. Development produces one candidate at two metres. That sensitivity result stays separate from the frozen three-metre finding; it was not used to manufacture a better demonstration.

Talladira's sequence is unusually helpful because every coordinate for the four line players is marked detected throughout the clip. At the peak gap, whole-line depth spread is 4.14 metres. At the clip's end it is 1.02 metres. The shape narrows again, but calling that a candidate recovery time would be misleading: no primary lagging event was identified. There is therefore no candidate recovery distribution to estimate.

A deeper player might be covering a runner or protecting space that teammates have left. Tracking cannot establish those responsibilities. The explorer lets the reader scrub the movement, change the tolerance and inspect observation flags. Its central distinction is practical: before judging the player behind the line, measure how he moved with it.
