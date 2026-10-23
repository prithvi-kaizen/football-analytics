### Turnovers and eligibility

Turnover time is the **first 25 Hz ball frame with new team possession**, provided both the old and new runs contain at least 0.4 s of contiguous, valid, live-ball control. Home/away codes come from the original match metadata. Dead balls, unknown control, missing frames and half boundaries break runs. Future control frames confirm that a switch persisted; they never enter pre-loss features. This is an offline event detector, not a zero-latency live predictor.

The headline **attacking-loss** scope requires the losing team to have controlled the ball continuously for at least 2 s and the last pre-loss ball to lie in the opposition half. The app can also inspect every eligible live-ball loss. This filter does not identify a settled attacking phase or prove that seven players attacked.

Each snapshot uses the most recent **strictly earlier** player frame, at 5 Hz: 0.04–0.20 s before the switch. It must have 11 identified players per side and one goalkeeper per side, with a valid live ball at the same instant. Incomplete and non-11v11 snapshots are excluded and counted. No interpolation or missing-player replacement is performed. Changes between the snapshot and the turnover may matter.

### Coordinates and direction

Tracking coordinates are metres from pitch centre. `KickOff.TeamLeft` attacks right; `TeamRight` attacks left. The half-specific directions rotate x and y together by 180° when needed, so **the losing team always attacked toward positive x**. Its own goal is at negative x, and the counterattack travels toward negative x. The actual pitch dimensions are read from metadata. Event locations use another coordinate convention and are never mixed into tracking geometry.

### Metric definitions

* **Players behind the ball:** losing-team outfield players with normalized x ≤ ball x, including those level with the ball. The goalkeeper is counted separately. A large number does not establish a compact or effective structure.
* **Counter options:** opposition outfield players at least 3 m toward the losing team's goal from the ball and within 40 m Euclidean distance of it. This fixed selection is a proxy for potential forward receivers.
* **Numerical coverage margin:** number of outfield players behind the ball minus the number of counter options. No assignment or marking responsibility is inferred.
* **Compactness RMS:** square root of the mean squared distance of behind-ball outfield players from their centroid, in metres. Undefined for fewer than two players. Lower values mean a smaller spatial spread; compactness alone need not be desirable.
* **Width/depth:** y/x range of that structure. **Hull area:** area of its convex hull in m², undefined below three players and zero for collinear points.
* **Central exposure:** 2 m grid cell centres in a rectangle extending up to 30 m toward the losing team's own goal from ball x, between y = −10 and +10 m, clipped to the pitch. A cell is exposed when it is >5 m from every behind-ball outfield player. Report the exposed fraction, not an asserted pitch-control probability. With no behind-ball outfield players all available cells are exposed; if there are no in-pitch cells, this metric and the score are unavailable.
* **Clear forward corridors:** ball-to-counter-option straight-line segments with no losing-team outfield player within a 2 m perpendicular corridor and projected strictly between the endpoints. All losing outfield players can block a corridor. The goalkeeper is excluded. No timing, body orientation, aerial path, offside or endpoint pressure model is used.
* **Distances to counter options:** mean and maximum of each option's nearest behind-ball outfield-player distance. Undefined when there are no options or no behind-ball outfield players.

### Ten-second outcomes and event alignment

Observe the first uninterrupted new possession, up to 10 s from the turnover. Stop before the first opposition regain, inactive ball, unknown control, invalid position, tracking gap or half end. The 25 Hz ball stream drives calculations; replays display recorded 5 Hz positions. A regained or dead-ball window is fully observed even when shorter than 10 s. A source cut, unknown control or tracking gap is **censored** and excluded from outcome rates and score associations.

**Progression** is the maximum ball displacement toward the losing team's goal relative to the first new-control ball position, floored at zero. It can include a forward pass in flight and does not establish controlled territorial gain. The progression indicator is displacement ≥10 m. Final-third entry means crossing into the attacking final third from outside it; starting there is not an entry. **Shot** means a winning-team `ShotAtGoal` within the same half and bounded window. Provider xG is summed only for those shots and is an outcome, never a score input.

Use a shot's `CalculatedFrame` when it exists in the same half's tracking stream; otherwise use its timezone-aware ISO timestamp and flag the alignment as approximate. The source paper documents event timing error. Shots close to a window boundary are therefore uncertain. No claim of exact event synchronization is made. **Event corroboration** means the nearest winning-team Play, OtherBallAction, BallClaiming, TacklingGame or ShotAtGoal is within ±2 s of the tracking turnover; the event ID and signed offset remain inspectable. This check supports review and does not prove that a duel winner established possession. It is an optional app filter.

### Fixed vulnerability diagnostic

The **0–100 diagnostic** is 100 times the unweighted mean of:

1. Numerical shortfall: `1 − min(behind_ball / 4, 1)`.
2. Spread: `min(RMS / 20, 1)`; set to 1 if fewer than two players remain behind.
3. Central exposed fraction.
4. Fraction of counter-option corridors that are clear; set to 0 when there are no options.

All constants are declared heuristics, selected before outcome inspection. **The score is not a fitted model, calibrated probability, or validated tactical rating.** Report within-match Spearman rank association with subsequent ball movement and fixed-bin outcome counts as a descriptive diagnostic. No test-set performance or statistical generalization is claimed. Event corroboration and shot xG never enter the score.

No learned model is fitted. Any future model must hold out complete matches **before** fitting imputers, scaling, feature selection or thresholds. With seven selected matches and a repeated club, leave-one-match-out checks would still provide limited evidence of transfer to other teams.

### Sources and limits

Data: **Deutsche Fußball Liga (DFL)**; Bassek, Rein, Weber & Memmert (2025), [Scientific Data 12, 195](https://doi.org/10.1038/s41597-025-04505-y). Original dataset: [Figshare version 1](https://doi.org/10.6084/m9.figshare.28196177.v1), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). These are historical 2022/23 matches released in 2025. Extracts are modified by time subsetting; displayed coordinates are rotated and metrics derived.

Seven selected matches support benchmarking and case studies. They cannot support league-wide team rankings, causal claims about defensive intent, or conclusions that a high-possession team necessarily has weak rest defence. Optical measurement error, contested possession, event timing, excluded non-11v11 states, fixed thresholds and lack of labelled video ground truth remain material limitations.
