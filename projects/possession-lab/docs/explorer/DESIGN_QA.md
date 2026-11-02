# Design delivery gate

2026-10-26. Antislop applied during the build as requested. Research instrument for
football analysts and ML engineers; warm editorial language. ENERGY 2 / RHYTHM 2 /
MOTION 1. The pitch is the focal point; time-aligned rows are the identity motif.
Reasons for colour, layout, typography, motion and spacing are in explorer/DESIGN.md.

## Hard gates

- R-02 PASS: UI source contains no em dash.
- R-03 PASS: browser geometry at 375 and 390 px showed no horizontal overflow; phone screenshot reviewed.
- R-17 PASS: scenario metric rows originate in Python scorer exports; public accuracy is absent.
- R-18 PASS: no testimonials or invented people appear.
- R-23 PASS: navigation implements the three user-requested experiences and methodology; pitch is observed data, with no fabricated asset.
- R-24 PASS: navigation points to existing experiences, methodology, source archive and reports.
- R-25 PASS: computed text contrasts 6.01:1 light secondary, 9.44:1 dark secondary, 5.50:1 white on away, 7.10:1 white on home.
- R-26 PASS: playback, frame buttons, speed, scrubber, timeline, transition/error navigation, selectors, form, disclosures, exports and theme have real handlers and were exercised.
- R-27 PASS: fixture loading message, runtime loading/ready/computing messages, unknown-frame explanation and actionable fetch/runtime errors exist.
- R-28 PASS: no filler FAQ.
- R-32 PASS: native controls, visible focus, skip link, keyboard tab arrows and range Home/End/ArrowRight were exercised.
- R-33 PASS: visual features are written in repository HTML/CSS/JS; no injected runtime styling or external patch service.
- R-34 PASS: both light and dark themes were switched and visually inspected.
- R-35 PASS: build, syntax checks, Python suite and recorded browser click-through completed; see REPORT.md for verification limits.
- R-36 PASS: no security, customer or real-match performance claim is presented.
- R-37 PASS: design direction and dials recorded before implementation; user selected during-build checks.
- R-38 PASS: synthetic scenarios are explicitly labelled; public Metrica provenance is linked.

## Purpose gates

- R-01 PASS: no gradients or glows; pitch stripes mark field context.
- R-04 PASS: no generic icon library; circles and slot labels encode tracking.
- R-06 PASS: Georgia titles provide editorial research character; system sans preserves control readability.
- R-07 PASS: no decorative grid; pitch markings and aligned timeline rows carry physical/time meaning.
- R-08 PASS: no decorative CTA arrows.
- R-09 PASS: no capsule badges or repeated marketing label.
- R-10 PASS: no glass treatment.
- R-12 PASS: no floating component shadows.
- R-13 PASS: no glow effects.
- R-14 PASS: no feature-card template; pitch, inspector, timeline, score table and prose have distinct jobs.
- R-19 PASS: motion is user-triggered data playback; no autoplay or scroll animation.
- R-22 PASS: no unrelated illustration.

## Liveliness

- Dials PASS: 2/2/1 recorded in DESIGN.md and maintained across the three views.
- Consistency PASS: restrained interface with an editorial opening, data workspace and prose methodology.
- Focal point PASS: measured football pitch dominates the workspace.
- Whitespace PASS: major gaps separate question, controls, observations and evaluation.
- Accent PASS: team colours encode state, green marks control focus and field context.
- Motif PASS: consistent team colours and aligned possession spells connect space with inference.
- Design Read PASS: research instrument audience, visual language and playback-only motion declared before implementation.

## Craftsmanship and quality locks

- C-1 PASS: major decisions have recorded purposes in DESIGN.md.
- C-2 PASS: controls perform data inspection, computation, download or navigation.
- C-3 PASS: every section answers a requested research question or defines interpretation.
- C-4 PASS: desktop/phone, both themes and keyboard paths checked; no universal accessibility audit claimed.
- C-5 PASS: metrics and data provenance are inspectable; no fabricated testimonials or claims.
- R-05 PASS: no generic hero/card/dashboard shell; the primary surface is a football research tool.
- R-11 PASS: controls use small radii; no pill-shaped component system.
- R-15 PASS: actions name their work: Run Python models, Next frame error, Download predictions CSV.
- R-16 PASS: copy uses possession, observation and scoring language, without marketing buzzwords.
- R-20 PASS: pitch geometry, physical-distance inspector and possession timelines are football-specific.
- R-21 PASS: light defaults with a working dark toggle.
- R-29 PASS: paper/ink plus team blue/orange, field green and neutral D/X have explicit semantic roles.
- R-30 PASS: no copied product identity or recognisable template.
- R-31 PASS: reasons for all major visual choices recorded in DESIGN.md.

## Motion v2 follow-up, 2026-11-02

- R-03 PASS: added descriptive source names initially exposed mobile form overflow;
  fixed select/grid minimum widths and stacked the phone form. Browser measurements
  after the fix: document width 375 at viewport 390; 360 at viewport 375, including
  reserved scrollbars. Both public and synthetic selections checked.
- R-26/R-27 PASS: public interventions and v2 generation completed through actual
  browser Python; ready/computing/complete messages appeared. Source changes enable
  synthetic mechanisms only for synthetic data. Moving observability pair and
  independent-cue selection were exercised; playback advanced public source frames.
- R-17/R-36/R-38 PASS: public accuracy remains unavailable; scripted v2 scope,
  measurement corruption, legacy fixtures and historical-score separation are explicit.
- R-34 PASS: phone dark/light switching visually reviewed; viewport override reset.
- R-35 PASS: 199 Python tests and four Node request tests; 25-case fixture release
  independently checked. All seven portfolio routes built.
- Purpose/liveliness/craft PASS: same documented colours, type, pitch/time motif and
  2/2/1 dials retained. Source selection serves provenance; motion depicts observations
  under user playback. No decorative interface expansion.

The earlier full gate remains the design baseline. See ../MOTION_V2.md for precise
research limitations and separately reported outcomes.
