# Source audit, before implementation

Inspected 21 October 2026. Controlling source: [SkillCorner/opendata](https://github.com/SkillCorner/opendata), pinned to `4340d274572876239c154c90bc507a9b3250a656`. Copies of the README, match index and MIT license are in `docs/source/`. SkillCorner and PySport receive credit in all outputs.

## Confirmed fields

- Match metadata: `id`, `players[].id`, `team_id`, `short_name`, `player_role`, `home_team_side` by period, `match_periods`, `pitch_length`, `pitch_width`. Sample 1886347 is Auckland FC vs Newcastle, 30 November 2024; pitch 104 by 68 m.
- Tracking JSONL: `frame` (10 Hz), `period`, `timestamp`, `player_data` (`player_id`, `x`, `y`, `is_detected`), `ball_data`, `possession` (`player_id`, `group`), camera projection. Null pre-match frames exist. Coordinates are metres, centred on the pitch, x along its length. Player IDs join to `players[].id`, not `trackable_object`.
- Dynamic events: `event_id` unique within match, `frame_start`, `frame_end`, `period`, `time_start`, `event_type`, `player_id`, `team_id`, `attacking_side`, plus provider-derived off-ball-run labels and outcomes. Sample contains 5,115 rows and 322 columns. Provider labels are comparisons, never detector inputs.
- Phases: `frame_start`, `frame_end`, `period`, `team_in_possession_id`, `attacking_side`. Defined only with ball in play. Adjacent phases can share endpoints; use half-open intervals [start, end).
- Timing check: first-period frame 28 is 00:01.8, not 2.8 s; second-period frame 27824 is 45:02.4. Use frames for joins and period metadata for clocks, not timestamp-to-frame multiplication.
- Player-season Physical/OBR/Passing aggregates exist, filtered to performances above 60 minutes. They cannot establish match-level or run-level effects and are excluded from this baseline.

## Licensing and access

The repository's MIT license permits reuse with its copyright and permission notice retained. The source README requests SkillCorner credit. No login, paid API, footage download or scraping is required. Public raw files and Git LFS media are sufficient. Dependencies will be open source. The linked vendor event/phase specification PDFs were inaccessible through the web reader; implementation relies only on the repository documentation and fields directly inspected here, with no assumptions about undocumented provider scores.

## Limitations and decisions

1. README describes ten matches; the pinned index actually contains twenty. Scope each output by explicit match IDs and loaded frames, never call this a representative league sample.
2. Off-camera coordinates are extrapolated. Preserve detected flags for runner and context players, expose an observed-only sensitivity filter, and disclose lower visibility in space estimates.
3. Identity errors and noisy positions occur (the vendor README estimates about 97% identity accuracy). Smooth within contiguous player/period segments, break gaps and reject implausible raw jumps before smoothing.
4. No exact touch events or human ground truth are supplied. Carrier identity is frequently null. Off-ball means an in-play phase confirms team possession, the tracked carrier is not the runner, the player is at least 3 m from the ball, and no provider possession interval belongs to that player. Tracking possession-group evidence must not contradict the phase. This can include frames with unknown carrier identity. It is an operational estimate.
5. Defensive line, clearance and receiving space are geometric proxies. They do not model offside, passing lanes, body orientation, reaction speed, reachability or tactical intent.
6. Defender displacement and teammate space changes are associations. No causal credit, counterfactual model or learned model is included. A later learned model must split by match before fitting any preprocessing or tuning; season aggregates and provider outcome labels must not leak into predictors.
7. Retrospective smoothing uses a centred window. It is unsuitable for claims of live prediction. Runs clipped by sample/period boundaries must be excluded.
8. Threshold selection affects counts. Publish defaults and sensitivity, missingness, denominator and exact source/cache hashes. A small smoke-test excerpt supports pipeline validation, not season conclusions.
