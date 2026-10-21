# Pressing trap detector: measurement contract

Source: [StatsBomb Open Data](https://github.com/hudl/open-data), UEFA Euro 2024, competition 55, season 282. The extraction uses all 51 matches and periods 1–4, excluding penalty shoot-outs. `data/manifest.json` pins the repository revision and records each event file's SHA-256 hash. Raw data remains in its provider format.

## Anchor and population

One row is one Pressure event with a location, a named pressing team, and a different possession team. The match, period and event ID identify the anchor. The table includes all such events; it does not restrict the baseline to high presses or build-up possessions. Use the attacking-third filter to investigate high pressing. The wide-entry heuristic is a separate, optional subset.

The event provider's team coordinate frame always points toward x=120. Pressure and recovery locations are shown in the pressing team's frame. Opposition action locations and destinations are rotated by 180 degrees: `(120−x, 80−y)`. Pass direction uses the opponent's original frame, so Forward means toward the opponent's attacking goal. The pitch uses 120×80 provider units; these are not metres.

## Preceding passes and the wide-entry heuristic

Link opposition Pass events from the preceding 15 seconds, in the same period and StatsBomb possession. Pass counts include attempts. The replay shows the most recent five preceding passes, while counts include all qualifying passes.

The last completed pass must have arrived by the pressure timestamp (50 ms timing tolerance). A wide-entry candidate requires all of the following:

- Its destination has opposition-frame y≤18 or y≥62.
- Its lateral displacement is at least 8 pitch units.
- Pressure follows its arrival within 0–3 seconds.
- The destination is within 15 pitch units of the pressure location.

These fixed thresholds are inspectable heuristics, not learned labels. A candidate can succeed or fail. A pass into a wide area need not target a full-back. This release does not infer a player's role or the defending team's intention. Direction is Forward if dx>5, Backward if dx<−5, and Lateral otherwise.

## Recovery rule

Search forward from each pressure for at most 15 seconds, remaining in the same period. Stop at a marked out-of-play event, foul, offside, stoppage, period end, or restart pass. This deliberately conservative rule excludes foul-winning regains, including cases where advantage might have continued.

A recovery is the first located event by the pressing team indicating control: a non-failed Ball Recovery, a successful Interception, selected goalkeeper collection/sweeper events, or a Pass, Carry, Shot, or completed Ball Receipt while StatsBomb assigns possession to that team. Clearances and merely contested duels do not alone establish control. The system therefore measures controlled regains, not only the provider's Ball Recovery event type.

The selected 3–15 second threshold is inclusive. A pressure is successful when its recorded recovery delay is no greater than that threshold. The numerator is successful pressure anchors; the denominator is all filtered pressure anchors. Several anchors may lead to one regain. Distinct recovery counts, recovery maps, and subsequent-threat comparisons deduplicate `recovery_id`.

An episode groups pressure anchors by match, period, possession ID and defending team. It is a possession grouping, not a claim that pressure was continuous. `episode_first` supports an alternative episode-level analysis; the main pressure rate uses every anchor.

## Passes allowed and threat

`passes_before` counts opposition attempts in the 15-second lookback. `passes_after` counts opposition attempts from the pressure to the identified regain, only for recovered sequences. `passes_allowed` is their sum; it is not a full-possession pass count.

The subsequent-threat window is fixed at 10 seconds from the recovery and ends earlier at a dead ball, period boundary, or end of the gained possession. It remains 10 seconds when the pressure-to-recovery threshold changes. Shot xG sums StatsBomb `statsbomb_xg` for eligible shots.

The xT model uses a 12×8 grid and all tournament Pass, Carry and Shot actions. Each action is one observation. Completed passes and carries create transitions; incomplete passes have zero terminal reward; shots have StatsBomb xG as terminal reward. The value iteration is:

`V(a) = (sum(shot_xG from a) + sum(completed_moves(a,b) × V(b))) / actions(a)`.

An unobserved cell has value zero. Iteration stops when the maximum cell change is below 1e-10. Subsequent xT is the sum of signed destination-minus-origin values for completed passes and carries in the post-recovery window. It may be negative. It does not assign a turnover penalty to unsuccessful passes and should not be interpreted as total possession value or added to shot xG. This is a tournament-fitted, in-sample descriptive model, not an independently validated forecast. Its grid, observation count, iterations and residual are saved in `outputs/xt_model.json`.

## Interpretation

This is a temporal and spatial pattern detector. The 5-second and 10-second rates are different operational definitions, not interchangeable measures. Team comparisons are descriptive: game state, opponent quality, playing time and number of matches differ. No causal or statistical-significance claim is made.

The animated replay interpolates the ball between recorded event locations. It does not reconstruct all players, off-ball runs, speed, defensive spacing or continuous tracking. 360 data is not used in this version.
