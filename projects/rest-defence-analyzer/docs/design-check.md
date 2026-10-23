# Design delivery gate

Checked 23 October 2026. Owner selected application during construction and the light, pitch-first analyst-workspace direction, recorded in `DESIGN.md`. Scope: authored Streamlit application, included report figure and the tested viewport widths. This is a scoped delivery check, not an exhaustive accessibility certification.

## Hard gates

* R-02 PASS: authored UI and report prose contain no em dash; source data and library-generated accessibility labels retain their original text.
* R-03 PASS within inspected widths: 1280 px desktop and 561 px narrow viewport render without page overflow; narrow DOM width equals viewport width, 561 px. Metrics stack and the pitch scales. Smaller screens remain an unexhausted QA area.
* R-17 PASS: displayed counts and shares bind to hashed DFL outputs; report denominators are regression-tested.
* R-18 PASS: no testimonials, avatars or customer claims are present.
* R-23 PASS: user requested the app, analysis figures and metrics and selected pitch-first red/teal direction. No invented logos or photographic assets were generated.
* R-24 PASS: tabs expose implemented views; source links resolve to the original data, paper and licence destinations.
* R-25 PASS: measured body contrast 13.69:1; white team numerals on red 7.38:1 and teal 6.35:1. Team shapes and shirt numbers supplement colour.
* R-26 PASS: AppTest exercises authored filters, sample selection, turnover selection and replay. Browser CSV export was clicked; native replay ArrowRight changes its displayed time. Overlay toggling works with Space and is covered by AppTest.
* R-27 PASS: loading text uses the cached-data spinner; empty filters display a recovery message; injected integrity errors display a rerun instruction without crashing.
* R-28 PASS: no filler FAQ is present.
* R-32 PASS in checked interactions: native checkbox Space and replay ArrowRight work; default keyboard-capable Streamlit controls and visible focus are retained. No outline removal is authored.
* R-33 PASS: UI changes are written in `app.py`, `viz.py` and the Streamlit config; no runtime patch script is used.
* R-34 PASS: one owner-selected light theme; no authored theme toggle.
* R-35 PASS within authored controls: the local server was run, AppTest controls exercised and the browser's structure, replay, evidence, definitions and CSV control inspected. Publication PNG was rendered and visually inspected. Generic library toolbars were not exhaustively audited.
* R-36 PASS: no invented performance, security, causal or predictive claims. The approximately zero score association is reported.
* R-37 PASS: owner-selected direction is recorded before UI construction in `DESIGN.md`.
* R-38 PASS: all teams, player shirt numbers, positions and statistics come from the legal source; mathematical fixtures remain confined to tests.

## Purpose gates

* R-01/R-04/R-07 PASS: no gradients, glows, generic icons or decorative background grids. The plotted grid measures central exposure and is explained in the legend.
* R-08/R-09 PASS: no decorative button arrows or promotional badges. The pitch direction arrow encodes the actual coordinate convention.
* R-10/R-12/R-13 PASS: no authored glass, shadows or glow effects.
* R-14 PASS: pitch, metric readout, line chart and evidence table have different sizes according to analytical purpose; no feature-card template.
* R-19/R-22 PASS: no ambient animation or invented motion. Replay scrubs recorded frames without interpolation.

## Liveliness and craftsmanship

* ENERGY 2 PASS: a large pitch and role-coded circle/triangle marks provide content-specific emphasis.
* RHYTHM 2 PASS: pitch, compact metric readout, bounded timeline, scatterplot and source definitions each serve a distinct analytical task.
* MOTION 1 PASS: only explicit recorded-frame interaction, appropriate to historical evidence.
* C-1 PASS: rationale for colour, pitch priority, typography and motion is written in `DESIGN.md`.
* C-2 PASS: primary controls have tested behaviour; no inert promotional elements.
* C-3 PASS: every view corresponds to structure, observed outcomes or source/method review.
* C-4 PASS within reviewed states: source error, empty filter, sample warning, replay and narrow layout checked. No claim of exhaustive assistive-technology testing.
* C-5 PASS: independently audited source counts and the observed score failure support the visible claims.
* R-05/R-06/R-11/R-15/R-16/R-20/R-21/R-29/R-30/R-31 PASS: one light theme, system typography, restrained two-team palette, native widget consistency, explicit units/definitions, and no buzzword or decorative-accent sections.

Analytical validation and remaining limits are in `validation.md`. The author's app-level check does not replace the source paper's measurement limitations or establish ground truth.

## Static publication addendum

* Static companion PASS: the owner-selected light, pitch-first red/teal direction is retained using native HTML/CSS/SVG and no new decorative assets.
* Controls PASS: native browser team/half/scope/corroboration filters, reset, turnover selection, overlay switch, keyboard frame stepping, recorded playback, CSV export and definitions disclosure were exercised. The live public site's default and team-filter counts agree with the Python results.
* Source binding PASS: every published transition, complete snapshot and timeline maximum is covered by release tests. A changed asset or analytical fingerprint fails verification.
* Layout PASS in checked desktop viewport: measured document width 1265 px within a 1280 px viewport, with no horizontal overflow. Responsive CSS supplies intermediate and narrow reflows; the new static companion has not received exhaustive device/screen-reader testing.
* Publication PASS: exact-commit Vercel status succeeded, the public page loaded its checksum-verified snapshot, and GitHub Actions passed the smoke/test/report/build workflow.
