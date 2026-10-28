# Validation record

Initial analysis validation, 28 October 2026. All analysis work was contained in `projects/open-body`; unrelated pre-existing workspace changes were left in place. At initial analysis completion no public deployment, repository push or social post had been made. Subsequent publication is recorded separately in `docs/deployment.md`.

## Data, calculations and reproducibility

* Both full pose archives match the SkillCorner manifest SHA-256 and byte counts. Tracking media match their Git LFS hashes; all 14 downloaded inputs have recorded hashes in `data/provenance.json` and `data/source-lock.json`.
* Both matches were scanned fully, not just the tutorial sample. The first reproduces the publisher's 153,252 frames, 4,902,560 roster player-frames and 1,540,715 pose player-frames. Both periods, never-played substitutes, inactive roster rows, null periods and pose gaps are handled.
* Exact 25/10 Hz clock joins have maximum residual zero in both matches. XY disagreement remains and is measured/gated; clock agreement does not validate identities or coordinates.
* Real labels are independently reconciled against source event rows. Tests also check native/event coordinate conversion, excluded goalkeeper role codes, macOS ZIP metadata, angle wrap, width/error gates, missing/incoherent windows, native alignment, no future pose inclusion, training-only standardization, held-out-label isolation, metric formulas, deterministic paired bootstrap, published-count reconciliation, prediction-level aggregate reconciliation and real clip synchronization.
* **17 tests pass**, no skips in the completed local environment: `.venv/bin/python -m pytest -q`. `ruff check open_body scripts tests` passes. `node --check open_body/web/viewer.js` passes.
* A complete rerun of `python -m open_body all` produced **identical SHA-256 hashes for ten analytic/clip artifacts**, including reception tables, per-event predictions, coverage, results, sensitivity runs and viewer data. `outputs/reproducibility.json` records the hashes. This was a rerun with verified local inputs and extraction caches, not a second fresh network download.
* The primary and reverse intervals include zero. The predeclared pilot criterion is false. The midfield-only direction is mixed. README, results document, public draft, figure, viewer and MP4 reflect those qualifications.
* The event specification PDF linked upstream was inaccessible (HTTP 403). No claim is based on reading it. Actual CSV columns, metadata directions, frame durations and coordinate joins were checked. General pitch scaling is implemented but these two pitches do not validate non-reference dimensions.

## Interactive viewer checks

Browser: Codex in-app browser, local-only preview at `http://127.0.0.1:8766/viewer.html`. The delivered HTML also embeds its full data/CSS/JS and requires no runtime network connection. Temporary QA fixtures are ignored by Git.

| Control/state | Observed result |
|---|---|
| Example selector | Switching to Sydney changes fixture, player, event and both views to E. Alagich |
| Play | Button becomes Pause and time/frame advance |
| Pause | Button returns to Play; playback stops |
| Go to reception | Scrubs to the nearest available pose frame; an odd tracking frame correctly displays −0.02 s rather than rounding to future pose |
| Speed | 0.5× selected and displayed; playback progresses at the selected rate |
| Time slider | End key reaches +2.98 s; input stops playback and updates pose/tracking frame annotations |
| Rotate skeleton | ArrowRight moves yaw from 35 to 40 degrees; skeleton rotates |
| Keyboard focus | Tab moves Play to Go to reception; visible focus styling retained; native select/range/button controls are keyboard operable |
| Category panel | Opens the actual six match/category summaries with counts and outcomes |
| Sensitivity panel | Opens all sixteen declared direction/check rows, including mixed midfield results |
| Limits panel | Opens target, selection, timing, proxy and generalisation qualifications |
| Missing pose | Second clip's final frame shows `no_pose` and “Pose missing in this frame”; no prior/future skeleton is substituted |
| Empty fixture | Shows “No eligible clips were exported” with rebuild instructions and hides controls |
| Malformed-data fixture | Shows a readable parse/rebuild error and hides controls; the expected fixture error is separate from normal-page checks |
| Loading | Included-data preparation text exists before synchronous initialization; no remote fetch is required |
| Data links | Both source links were clicked, reached the intended Hugging Face/GitHub pages, and returned to the viewer |
| Normal-page console | No error/warning entries observed; final error query for `viewer.html` returned an empty list |

Narrow, intermediate and wide viewport overrides were exercised (requested 390, 820 and 1280 CSS pixels; host-reported inner widths approximately 354, 745 and 1163). Document scroll widths stayed within the corresponding inner widths. The narrow layout stacks pitch/skeleton; intermediate and wide layouts place them side by side. Wide tables scroll inside their own container. The uncertainty chart has a dedicated narrow layout and exact text values below it. Temporary viewport overrides were reset before handoff. Screenshots: `outputs/viewer-mobile.jpg` and `outputs/viewer-preview.jpg`.

Text reflow uses rem/fluid type without fixed-height text boxes. Browser-level 200% zoom, screen-reader use and real touch hardware were not separately tested; do not claim comprehensive accessibility certification.

## Rendered outputs

FFprobe verifies H.264, 1280×720, 15 FPS, exactly **30.000 s** for `outputs/open-body-demo.mp4`. The demo is silent, rendered from the same deterministic real clips as the viewer. Intro, both animated sections and final results frame were inspected. A pitch-border/text overlap and a chart-footnote overlap found in the first render were fixed and the output rendered again. The final scientific plot and demo check images were visually inspected. No fabricated video footage or illustrative player observations were added.

## Anti-slop delivery gate

The owner selected “apply during the build” and approved the analyst workbench direction. The gate is scoped to the authored viewer/demonstration, not verbatim upstream source snapshots.

### Hard gate

* R-02 PASS: authored viewer copy contains no em dash; prose uses plain labels.
* R-03 PASS: tested narrow/intermediate/wide reflow; measured document width does not exceed viewport width.
* R-17 PASS: every displayed statistic is bound to saved, reconciled experiment output.
* R-18 PASS: no testimonials, fictional people or avatars are used.
* R-23 PASS: viewer, real-data animation and displayed findings were requested; palette/layout were approved by the owner.
* R-24 PASS: source links reach verified pages; all local disclosure targets exist.
* R-25 PASS: contrast checker reports secondary text/paper 7.08:1, white/pitch 9.34:1, orange/paper 5.68:1, bright orientation mark/pitch 5.04:1. Team markers have contrasting outlines and textual legends.
* R-26 PASS: selector, playback, speed, reception jump, both sliders and all disclosure controls were exercised as recorded above.
* R-27 PASS: preparation, empty, malformed-data and missing-pose states are explicit and tested as recorded above.
* R-28 PASS: no template FAQ exists.
* R-32 PASS: native keyboard-operable controls and visible focus styles; Tab/ArrowRight/End interactions observed.
* R-33 PASS: UI features live in HTML/CSS/JS sources. Python only assembles the offline artifact by injecting the data and source bundles.
* R-34 PASS: one approved light theme is supplied, with no untested theme toggle.
* R-35 PASS: app run, controls clicked, console inspected, layouts captured; render repairs were rechecked.
* R-36 PASS: no invented performance, security, customer or causal claims.
* R-37 PASS: owner-approved direction is recorded in DESIGN.md and the design read preceded UI generation.
* R-38 PASS: real exported observations/results; unavailable pose is labelled and never fabricated.

### Purpose gate

* R-01/R-07/R-09/R-10/R-12/R-13/R-14/R-22 PASS: no decorative gradients, grids, capsules, glass, shadows, feature-card template or generic illustrations are used.
* R-04/R-08 PASS: no generic icon library or decorative CTA arrows. Pitch direction/heading arrows encode actual geometry.
* R-06 PASS: system sans supports dense analyst reading and offline reproducibility; reason is recorded in DESIGN.md.
* R-19 PASS: user-triggered clip playback and yaw rotation explain the measurement; animation stops at clip end and opens paused.

### Liveliness and craftsmanship

* Dials PASS: ENERGY 1 / RHYTHM 1 / MOTION 2 are explicit and match the compact workbench.
* Focal point PASS: tactical pitch and selected orange receiver lead the screen; no decorative metric row competes with the mechanism.
* Structure PASS: spacing separates inspection, comparison and supporting details; orange repeats only for selected geometry and model-change marks.
* C-1/C-2/C-3 PASS: palette/layout have written purposes; controls work; sections contain the actual analysis rather than marketing filler.
* C-4 PASS within recorded test scope: real empty/error/missing states, keyboard controls and three responsive widths checked. Untested accessibility dimensions are disclosed above.
* C-5 PASS: content is measured or explicitly qualified; no fictional proof is used.
* R-05/R-11/R-15/R-16/R-20/R-21/R-29/R-30/R-31 PASS: the approved pitch/skeleton workbench determines the layout, functional labels, restrained corners and palette. There is no generic landing-page shell, hype copy, forced dark theme or product clone. Major design reasons are recorded in DESIGN.md.
