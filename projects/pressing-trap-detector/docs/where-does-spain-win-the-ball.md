# Where does Spain actually win the ball?

Spain’s high press is an obvious place to look for their regains. This event-based test finds a broader picture: most of the controlled recoveries following a pressure arrive outside the attacking third.

Across Spain’s seven Euro 2024 matches, StatsBomb records 991 located pressure events against an opposition possession. Of these, 171 are followed by a controlled regain within five seconds, before a dead ball or the end of the period. That is a **17.3% pressure-to-recovery rate**. Several pressures can precede the same regain: those 171 successful anchors resolve to **132 distinct recoveries**.

Of the 132 recoveries, **58 are in the middle third, 57 in the defensive third, and 17 in the attacking third**. The location is where Spain first establish control under this detector’s rules, rather than where their pressure began. These are recoveries linked to recorded pressures, not every occasion on which Spain win possession.

## Does the wide-pass pattern appear?

The detector finds 133 Spanish pressure events matching a simple wide-entry pattern: a completed opposition pass moves laterally into a wide channel, then Spain apply pressure nearby within three seconds of its arrival. Twenty-one of these pressures lead to a controlled regain within five seconds, a rate of **15.8%**.

That pattern supplies sequences worth watching. It does not, on its own, establish that Spain deliberately invited the pass or that this pattern is more effective than their other pressures. The wide-entry subset’s raw conversion rate is lower than Spain’s all-pressure baseline. The populations differ in location and game context, and the heuristic has not been validated against video.

## The clock changes the answer

Extending the recovery window to ten seconds raises Spain’s successful pressure anchors to 280, a **28.3%** rate, associated with **170 distinct recoveries**. Only 19 of those distinct recoveries are in the attacking third. A longer window captures more delayed regains and creates more opportunities for unrelated subsequent events to be associated with the pressure.

Germany provide a useful descriptive comparison. Their 598 pressure events yield 109 successful anchors and 80 distinct regains within five seconds: an **18.2%** pressure-to-recovery rate. Spain’s 17 attacking-third regains constitute 12.9% of their distinct recoveries; Germany’s six constitute 7.5%. Germany played five matches and Spain seven, so the raw totals do not establish comparative pressing strength. Opponents, scorelines, match durations and tactical choices remain uncontrolled.

## What to look at next

Start with the successful wide-entry sequences, then compare them with failed candidates from the same match. Watch whether the receiving player has an easy return pass, whether Spain block the route inside, and whether a second defender arrives as the receiver controls the ball. Those are tactical details that event locations alone cannot settle. The dashboard’s event replay is a navigation aid; it interpolates recorded actions and does not reproduce player movement.

The defensible finding is specific: under a five-second controlled-regain definition, Spain’s pressure-linked ball wins are spread across the pitch, with relatively few in the attacking third. Wide-entry sequences occur, but the event data do not yet justify calling them intentional traps.

Data: [StatsBomb Open Data](https://github.com/hudl/open-data), UEFA Euro 2024. Source revision and per-file hashes: `data/manifest.json`. Definitions and limitations: [methodology](methodology.md). Results are descriptive and sensitive to the recovery window.
