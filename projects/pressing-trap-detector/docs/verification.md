# Verification: 21 October 2026

## Evidence and build

PASS: All 51 raw event-file SHA-256 hashes match the pinned manifest. The files contain 187,924 events. Event IDs are unique within each match.

PASS: Extraction produces 12,891 unique pressure anchors across 24 teams. Automated checks cover coordinate bounds, opposition possession, replay order, recovery delays, pass counts, Spain's 5s/10s headline totals and xT convergence.

PASS: Eleven focused unit tests cover both-axis coordinate rotation, pass direction, prior possession exclusion, candidate matching, the inclusive 15s boundary, dead balls, period boundaries, failed recoveries, lost interceptions, repeated pressure anchors and threat after an interception changes possession ID.

PASS: The Data plugin's prebuilt compiler and authored-content verifier succeed. Protected runtime files were preserved. The final snapshot has `buildStatus: complete`.

## Browser checks

These checks were performed in the Codex in-app browser against the compiled local build.

| Control or view | Observed result |
| --- | --- |
| Spain, default 5s | 991 pressures, 171 successful anchors, 17.3%, 132 distinct regains |
| Recovery window → 10s | 280 successful anchors, 28.3%, 170 distinct regains |
| Team → Germany at 10s | 598 pressures, 172 successes, 28.8%, 110 distinct regains |
| Team → All at 10s | 12,891 pressures, 3,082 successes, 23.9%, 2,058 distinct regains |
| Reset filters | Restores Spain, all matches/regions/channels, all candidates, 5s |
| Wide entry → Yes at 5s | 133 pressures, 21 successes, 15.8%, 19 distinct regains |
| Pressure region → Attacking third, wide entry Yes | 35 pressures, 5 successes, 4 distinct regains |
| Channel → Centre in that subset | 1 pressure, 0 recoveries; mean xT shows No data |
| Spain + Germany vs Scotland | Explicit empty states in summary, maps, list and replay |
| Map point → select | Replay updates to the exact Spain vs Croatia 2:43 Morata anchor |
| Sequence row → select | Replay updates to Spain vs Croatia 46:55 Lamine Yamal |
| Next page / Previous page | Rows change 1–8 → 9–16 → 1–8 |
| Sequence result → No recovery | List changes to 820 unsuccessful Spanish anchors at 5s |
| Play / Pause | Button toggles and replay time advances |
| Next / Previous recorded event | Time steps to recorded timestamps |
| Restart | Returns to the start of the replay |
| Replay slider, End key | Moves to the replay's final timestamp |
| Recorded events disclosure | Reveals timestamped original actions |
| Source actions → View data source | Opens definitions, source revision, caveats and scoped source records |
| Escape | Dismisses the source actions menu |
| Pass-direction / recovery-region plots | Visible painted bars, labels and axes; all 4/3 categories present |
| Tournament comparison | 24 painted team bars, nonzero geometry; matching count table |
| 390px responsive viewport | Reflowed controls, two-column metrics, stacked content; page scroll width equals viewport client width (375px) |
| Default pane | No horizontal page overflow (735px client/scroll width) |

The first render exposed a component named Map shadowing JavaScript's built-in Map. It was renamed and rebuilt. No new console errors were recorded after that correction; the earlier console entry remained in the browser's retained log.

Clipboard limitation: the shared Copy data action was invoked for the 133-row wide-entry subset, but the browser clipboard inspection returned no text. Clipboard delivery is therefore **not verified**. The source inspector and generated `outputs/pressures.csv` remain available. No claim is made that every built-in shell theme, export workflow, layout-editing action or publishing flow was tested.

## Antislop delivery gate

The scope below covers the authored dashboard; protected shell features were preserved rather than reimplemented. The user chose During mode and the light editorial direction recorded in `DESIGN.md`.

- R-02 PASS: Authored React/CSS and article prose contain no em dashes.
- R-03 PASS: 390px and default-width browser inspection found no horizontal page overflow; wide tables scroll within their containers.
- R-17 PASS: Every displayed football count comes from the reviewed StatsBomb extraction.
- R-18 PASS: No testimonials or invented people are used.
- R-23 PASS: Maps and statistics implement the requested features; visual direction was selected by the user. The only image is the original publisher's attribution logo.
- R-24 PASS: The authored source link resolves to the actual StatsBomb repository; no invented navigation destinations.
- R-25 PASS: Measured primary text contrast is 14.15:1; secondary text 5.72:1; red 5.98:1; recovery green 6.55:1. White play-button text on red is 6.47:1. Dark palette equivalents were also checked.
- R-26 PASS: Authored selects, map points, row buttons, paging, replay controls and disclosure have real handlers and observed effects.
- R-27 PASS: Loading was observed during sidecar fetch; empty selections were tested; shared runtime error handling remains intact. A forced network-failure scenario was not run.
- R-28 PASS: No FAQ is present.
- R-32 PASS: Native controls, focusable map points, visible red focus rings, keyboard slider and Escape dismissal were verified.
- R-33 PASS: UI files were authored directly and updated using source patches, not external replacement scripts. Python edits update evidence, not UI source.
- R-34 PASS: The requested authored theme uses the supported fixed-light theme token. Dark theme colors were inspected before the fixed-light direction was applied; alternate protected themes remain available and were not exhaustively tested.
- R-35 PASS: The application was built and the authored control click-through above was recorded. The shared clipboard verification limitation is disclosed separately.
- R-36 PASS: No security, compliance, customer or performance claims are invented.
- R-37 PASS: The user explicitly selected warm paper, dark ink, Spain red and clear pitch diagrams before UI authoring.
- R-38 PASS: Every match, player, event and result is sourced; the article is labelled a draft.
- R-01 PASS: The warm neutral and red palette implements the user's direction. No gradients or glows.
- R-04 PASS: No decorative authored icon set.
- R-06 PASS: System sans-serif is used for data readability; serif metrics and article text implement the editorial direction.
- R-07 PASS: Pitch lines encode real pitch geometry; no decorative background grid.
- R-08 PASS: The pitch-direction arrow communicates the actual coordinate frame.
- R-09 PASS: No promotional capsules or eyebrow badges.
- R-10 PASS: No authored glassmorphism.
- R-12 PASS: No card shadows; the shared menu shadow denotes an actual overlay.
- R-13 PASS: No glow effects.
- R-14 PASS: Composition follows coupled maps, sequence inspection, aggregate patterns, comparison and the requested article; no feature-card template.
- R-19 PASS: Motion only interpolates event-level ball movement after the user presses Play; manual stepping is available.
- R-22 PASS: No generic illustrations.
- Liveliness PASS: Energy 2 / Rhythm 2 / Motion 1 are recorded. The pitch geometry, team-specific evidence, red pressure marks and editorial type give the page its subject-specific identity.
- C-1 PASS: Palette, typography, geometry and motion purposes are recorded in `DESIGN.md`.
- C-2 PASS: Requested detector, filters, maps, directions, recovery regions, replay and comparison are implemented. Shared clipboard delivery remains unverified.
- C-3 PASS: Each authored section answers a question in the project brief.
- C-4 PASS: Empty-state, loading, keyboard and narrow-width behavior were checked; error handling uses the preserved runtime.
- C-5 PASS: Source revision, hashes, definitions and executable extraction accompany the results.
- Quality locks PASS: Consistent spacing, small corner radii, hierarchy, quantitative formats and semantic colors are defined in authored CSS/theme tokens. No unsupported claims or artificial benchmarks were added.

## Interpretation limits

The detector identifies temporal/spatial associations, not intentional traps. Replays interpolate the ball between recorded actions and do not reconstruct player tracking. The xT model is fitted on this tournament and has no independent predictive validation. Team comparisons are descriptive and unadjusted for opponents, score state and playing time. 360 snapshots are not used.
