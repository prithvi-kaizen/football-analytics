# Source audit (before implementation)

Inspected 22 October 2026. Official repository revision: `4b73468fc5b0f1950f9f66fada70ad3a4f9327cb`.

## Sources and rights

- [Official release, 27 May 2026](https://www.hudl.com/blog/statsbomb-free-womens-data-wsl-ligaf-bundesliga-seriea-nwsl): five domestic women's leagues; 2023 NWSL and 2023/24 European seasons.
- [Repository README](https://github.com/hudl/open-data): JSON competitions, matches, events and lineups; selected 360 coverage.
- [Public Data User Agreement](https://github.com/hudl/open-data/blob/4b73468fc5b0f1950f9f66fada70ad3a4f9327cb/LICENSE.pdf), last updated 8 September 2023: permits public research analysis; restricts commercial exploitation and raw-data redistribution (1.2, 7); requires StatsBomb brand-logo attribution (1.4). Free access is not an unrestricted open-source data licence. Original terms retained in `docs/source/LICENSE.pdf`; code licence will exclude data and provider branding. Downloads remain local and ignored by Git.
- [Event specification v4](https://github.com/hudl/open-data/blob/4b73468fc5b0f1950f9f66fada70ad3a4f9327cb/doc/Open%20Data%20Events%20v4.0.0.pdf), read before coding; original retained locally.

## Catalog and field inspection

The pinned catalog contains WSL 37/281, Serie A Women 131/281, Frauen Bundesliga 135/281, Liga F 182/281 and NWSL 49/107. Liga F has 240 matches, 30 with Barcelona. Actual downloaded coverage will be recorded per run rather than inferred from the announcement.

Inspected all 3,302 events of match 3911491. Fields available: unique `id`, match-order `index`, `period`, period-relative `timestamp`, display `minute` and `second`, provider `possession`, `possession_team`, event `team`, `type`, `location`, optional `duration`; pass endpoint and outcome; carry endpoint; shot outcome, type and StatsBomb xG. Match metadata includes teams and final scores. Completed passes omit `pass.outcome`; unknown and injury-clearance outcomes must not count as completed.

Provider possessions restart when control is established and may restart for the same team after a throw-in. `possession_team` identifies the **starter** of a chain. Opposing defensive events also carry that field; never attribute their coordinates or duration to the attacker. Half-start/end events are duplicated by team; do not count them twice. Period 2 timestamps restart at zero, while display minutes restart at 45. Include stoppage time and exclude shootouts.

## Limits and analytical decisions

1. Event coordinates use a 120 x 80 pitch, with the event team attacking right. Retain the actual on-ball actor's coordinates; do not rotate both halves. Validate endpoints and use coordinate units, not inferred metres.
2. There is no continuous ball-in-play clock. Use unioned on-ball action intervals for an **active possession-time proxy**, capped at the next possession boundary. Also report possession elapsed span separately. Neither is official possession percentage; dead time and overlapping events otherwise inflate time.
3. Territorial control means **final-third completed-pass share** (field tilt), not tracked spatial occupation. No full tracking or universal 360 coverage is assumed.
4. xT is a location-only Markov baseline. Learn from completed and failed moves, non-penalty shots and explicit losses, exclusively on training matches. No men's pretrained grid, future goals, shot xG or test matches in fitting. Evaluate using held-out matches only. Small samples are functional tests, not league evidence.
5. Positive move xT can double-count repeated advances. Show signed move xT and terminal shot xG separately; positive xT is not a calibrated possession scoring probability or causal player value.
6. Reconstruct goals in event-index order before each action; handle own-goal-against and avoid double-counting own-goal-for. Validate final scores against metadata. Sequence start state and action-level score-state views serve different questions.
7. League, opponent, score state and selection affect comparisons. Keep same-league comparisons primary; cross-league totals are descriptive, without strength adjustment. No claim of tactical intent or superiority from possession alone.
8. Low immediate threat can be useful for lead protection, rest or drawing opponents out. Event data cannot establish those purposes. Style thresholds are transparent exploratory rules, not learned tactical labels.

## References for the baseline

[Karun Singh, Introducing Expected Threat](https://karun.in/blog/expected-threat.html) and [socceraction xT documentation](https://socceraction.readthedocs.io/en/stable/documentation/valuing_actions/xT.html). Implement the transparent fixed-point baseline ourselves with NumPy, retaining failure probability rather than conditioning transitions only on successful moves.

## Post-smoke-test reconciliation corrections

Full-season validation found that 16,383 passes, 11,162 carries and 173 shots are by a team other than the provider chain starter. Example: match 3910744, events 3650-3653, Real Madrid recover, carry and shoot while `possession_team` still names Valencia. Filtering attacking events by the starter would drop real actions. The final baseline therefore splits on opposing attacking on-ball anchors (pass/carry/shot/dribble/miscontrol/dispossessed/shield), retaining the provider starter in separate columns and leaving defensive annotations within the current phase. All source passes, shots and xG must reconcile. This is an explicit analytical sequence definition, not a claim to reproduce StatsBomb's proprietary control model.

The same audit found one interception with duration -0.090642 seconds (match 3911552, index 566). Durations in [-0.1, 0) are explicitly set to zero and flagged with their original values; larger negatives fail. The immutable cached source is never edited.
