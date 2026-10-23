# Source audit, completed before analytical implementation

Inspected 22 October 2026. Controlling source: [StatsBomb Open Data](https://github.com/statsbomb/open-data), repository revision `4b73468fc5b0f1950f9f66fada70ad3a4f9327cb` (the repository now redirects to hudl/open-data). The pipeline pins that revision. Local source PDFs and extracted text are in `docs/source/`.

## Fields verified

- `competitions.json`: competition/season identifiers, name, gender and available-360 timestamps. Men’s Euro 2024 is 55/282 (51 matches); Women’s Euro 2025 is 53/315 (31 matches). Both match lists advertise 360 availability, which does not establish corner-level coverage.
- Event specification v4.0.0 and v1.1: unique `id`, `index`, `period`, period-relative millisecond `timestamp`, `team`, `possession`, `possession_team`, `location`; `pass.type.name = Corner`; `pass.technique` includes Inswinging, Outswinging, Straight; `pass.length`, `height`, `end_location`, body part and outcomes. A direct shot can have `shot.type = Corner`. Shots have `statsbomb_xg` and outcome. Missing values are not zero.
- 360 v1.0.0: `event_uuid` joins to event ID; `freeze_frame` has location, teammate, actor and keeper booleans, without player identity; `visible_area` is a polygon or may be empty. Orientation is the linked actor’s team attacking from x=0 to x=120. StatsBomb pitch coordinates span 120 by 80; they are standardized units, not measured pitch metres.
- Inspected actual matches 3930158 (Germany vs Scotland) and 3998836 (Iceland Women’s vs WNT Finland): 5 and 11 pass-corners, with 2 and 9 linked frames. This is a smoke sample, not tournament findings.

## Licence and publication handling

Read `LICENSE.pdf` (StatsBomb Public Data User Agreement, updated 8 September 2023), particularly sections 1.1, 1.2, 1.4 and 7, and the repository README. The data is free to access for research, but is **not an unrestricted open-source dataset**. The agreement restricts commercial exploitation and redistribution of the data; public analytical findings require StatsBomb brand-logo attribution. The README also asks for source acknowledgement and the logo. Data and branding retain StatsBomb terms; the code licence does not relicense them. The agreement asks users to register interest through the provider’s resource centre.

This project downloads directly from the provider for local research; raw data, per-corner tables, sequences and player frames are ignored by Git and are not bundled for redistribution. Public outputs contain aggregate analytical findings, attribution and the provider logo. Review the original agreement for intended downstream use; commercial use is outside this project’s stated scope.

## Limitations established before coding

1. 360 is sparse broadcast-derived snapshots, not continuous tracking. Not all players/events are visible, polygons can be absent and actor/keeper flags have documented caveats. Absence is not evidence of no player.
2. No reliable player identities or trajectories in these frames: no run detection, marking assignments, tactical intent, optimal repositioning or TacticAI reproduction is supported.
3. Delivery technique can be absent or conflicting. Short corners need a declared heuristic; never infer swing from preferred foot alone.
4. A shot-window association is not causal attribution. Team quality, opposition, delivery choice and match context confound comparisons. Possession boundaries deliberately exclude some second phases.
5. A cutoff late in a period can censor observations. Preserve an unknown outcome if the observable sequence ends early without a shot or explicit terminal event.
6. The two tournaments differ in population and year. Show separate comparisons by default; pooled clusters are exploratory and may reflect visibility or tournament mix.
7. Use only the corner’s own frame for spatial features. Subsequent events, pass endpoints and shot outcomes must not enter the pre-kick model. Swing technique/short delivery are retrospective descriptions, excluded from the strict pre-kick predictor.
8. Small clusters and overlapping uncertainty do not justify declaring a best tactic. Learned models require whole-match splits, training-only preprocessing and a constant-probability benchmark.

## Research inspiration

Wang et al. (2024), [TacticAI: an AI assistant for football tactics](https://doi.org/10.1038/s41467-024-45965-x), Nature Communications 15, 1906. The public project is a simplified event/snapshot analysis inspired by the paper. It does not reproduce its training data, graph model or counterfactual recommendations.
