# Dataset review, completed before implementation

Reviewed 22 October 2026. The controlling source is Figshare article **28196177, version 1**, DOI [10.6084/m9.figshare.28196177.v1](https://doi.org/10.6084/m9.figshare.28196177.v1). The original API response is retained in `source/figshare-v1.json`, including file IDs, sizes and MD5 checksums.

## Permission and citation

The API identifies **CC BY 4.0**. The [authors' repository](https://github.com/spoho-datascience/idsse-data) confirms DFL authorization and requires naming the **Deutsche Fußball Liga (DFL)** and citing Bassek, M., Rein, R., Weber, H. & Memmert, D. (2025), *An integrated dataset of spatiotemporal and event data in elite soccer*, Scientific Data 12, 195. [Paper](https://doi.org/10.1038/s41597-025-04505-y). Derived extracts must retain attribution, identify modifications and link [the licence](https://creativecommons.org/licenses/by/4.0/).

## Confirmed fields

The paper's Data Records and Technical Validation sections, authors' parser, and actual J03WPY XML were inspected.

* Seven complete 2022/23 matches: two Bundesliga, five 2. Bundesliga. Five matches involve Düsseldorf. All three XML files are required per match.
* Match information: match/team/person IDs, team names and home/guest roles, starter flags, shirt numbers, German position abbreviations (`TW` = goalkeeper), and actual pitch dimensions `PitchX/PitchY`.
* Tracking: entity-major `FrameSet` grouped by `GameSection`, `TeamId`, `PersonId`; individual frames have `N`, ISO timestamp `T`, metric `X/Y`, and derived motion fields. The ball additionally has `Z`, `BallPossession` (1 home, 2 away), `BallStatus` (1 live, 0 inactive). Nominal rate 25 Hz. Coordinates are pitch-centred; no event-coordinate conversion will be applied to tracking positions.
* Events: IDs, ISO `EventTime`, nested action classes and team/player attributes. `KickOff` supplies `TeamLeft`, `TeamRight`, and the half. `FinalWhistle` supplies half end. `ShotAtGoal` supplies team and provider xG. Some events include `CalculatedFrame`/`CalculatedTimestamp`; only 25 of 1,504 event records have `CalculatedFrame` in the inspected match. Deleted records must be ignored and events sorted by time, not XML order.

## Limitations and implementation consequences

1. This is a selected seven-match method-demonstration set, not a representative league sample. No league-wide rankings or causal team explanations are justified.
2. Shared timestamps do not guarantee exact event alignment. The paper discusses unsystematic manual timing errors and evaluates automatic synchronization without video ground truth. Use tracking possession/live flags to anchor turnovers; record event corroboration separately. Prefer corrected shot frame references when available, otherwise flag UTC alignment as approximate.
3. Tracking is optical and postprocessed. Identity swaps, occlusion and position error remain possible. Validate duplicate entity/frame keys, continuity, finite coordinates, roster membership and complete snapshots. Do not fabricate or interpolate missing players.
4. Ball possession labels measure control, not tactical intention. Short changes and stoppage/restart switches should be excluded by explicit persistence and live-ball criteria. These rules still need video-labelled validation.
5. Behind-ball counts, compactness, central unoccupied grid points and straight-line passing corridors are geometric proxies. They omit speed, body orientation, aerial ball travel, pressure and offside. An open corridor is not proof a pass was available.
6. Ten-second outcomes must stop at a regain, dead ball, tracking gap or half boundary. Truncated source windows must be marked censored rather than treated as safe transitions.
7. No fitted model in the MVP. A fixed-weight score can be checked descriptively against outcomes; it is neither a calibrated probability nor independently validated. Any future learned model must split by match before preprocessing or tuning.
8. The source tracking XML is entity-major: downloading its first bytes gives one player, not a synchronized match sample. A genuine small download needs a verified byte-range index covering every entity in the chosen interval.

## Smallest end-to-end stage

One match, tracking-native stable live-ball turnovers, last pre-loss player snapshot, behind-ball count, and a bounded ten-second outcome. Only after tests and a real-data run pass: geometric features, fixed score and sensitivity checks, then the Streamlit explorer and reproducible publication chart.
