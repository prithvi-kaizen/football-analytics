# Invisible Runner design direction

User choice: “Editorial analyst desk: light, restrained, pitch-first.” Apply anti-slop during implementation.

Reading this as: a football analysis workbench for analysts, in a light editorial visual language, dial ENERGY 1 / RHYTHM 2 / MOTION 1. Replay motion is functional evidence, separate from decorative motion.

- Warm paper and dark ink support long reading and chart inspection without glare.
- Teal identifies the attacking team and newly free cells; rust identifies opponents and lost cells. Shape, fill and text also convey state.
- A system Georgia headline gives the requested editorial voice; system sans body text keeps numeric controls legible without web fonts.
- The pitch leads the run-detail view. A line chart follows it to explain changes through time; the distribution and exact records support comparison.
- Controls use native Streamlit widgets for focus, keyboard operation and stable labels. A keyboard-operable frame slider supplements playback.
- Spacing separates the selection, replay and evidence layers. Metric cards and decorative illustrations are unnecessary.
- The light theme is fixed to honour the user's explicit light direction; no custom theme toggle is introduced.
- Text product name only. All player names, numbers and metrics come from the requested real dataset. No logos, profile photos or testimonial assets.
- No separate marketing navigation. Dataset, team and run selection directly serve the requested analyzer.

## Published browser version

The same light editorial direction continues in `web/`. The desktop view places a large pitch beside the selected teammate's measurements and timeline; on phones those views stack. Native selects and a range control preserve keyboard access. Three reviewed speed profiles replace server-side recalculation on the static host, with that distinction stated beside the controls. A project-link header connects the repository, existing pressing dashboard and methods. Plotly.js is bundled locally; every chart uses the real reviewed snapshot.
