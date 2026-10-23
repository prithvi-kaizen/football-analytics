# Design delivery gate

PASS, 23 October 2026. User selected checks during implementation and approved the direction recorded in [DESIGN.md](../DESIGN.md). Evidence: [validation receipt](validation.md), [desktop review](dashboard-desktop.png), [mobile review](dashboard-mobile.png), source inspection and 34 passing tests. This gate covers authored content and controls; no claim is made to exhaustively retest Streamlit's own settings, table toolbar or Plotly's entire interaction library.

## Hard gate

- R-02 PASS: no em dashes in authored application, methods, report or README text; source scan completed.
- R-03 PASS: desktop and mobile rendered review; page width equals viewport width. Tables/tab strips scroll inside their own containers.
- R-17 PASS: every displayed statistic comes from validated StatsBomb-derived outputs; sample results carry a visible warning.
- R-18 PASS: no testimonials or invented identities.
- R-23 PASS: requested analytics define the statistics and navigation; direction approved; only the original, licence-required provider logo is used. No product logo or decorative imagery was created.
- R-24 PASS: authored external links lead to named sources; tabs each display an implemented view.
- R-25 PASS: tested text palette on paper background: charcoal 13.74:1, teal 5.99:1, rust 5.76:1. Rendered inspection found Streamlit's default 0.6 caption opacity; the authored style sets it to 1 so definitions and caveats retain the charcoal contrast. Secondary point colour at its plotted opacity exceeds 3:1 for graphics. Chart evidence also has exact tables.
- R-26 PASS: dataset, split, competition, focus, match, sequence, metric and threshold controls have real behavior; AppTest exercises them. Three download controls verified through the browser.
- R-27 PASS: no-output setup instructions, loading spinner, invalid-output error handler, and empty-result states are implemented; empty threshold results exercised.
- R-28 PASS: no FAQ section.
- R-32 PASS: native keyboard-operable controls retained, with framework focus styling. Keyboard duration-slider adjustment verified; exact tables accompany plots.
- R-33 PASS: UI lives in authored Streamlit source and theme configuration; no external source/CSS rewrite script.
- R-34 PASS: no authored theme toggle; light analysis theme is the supported design direction. Exported charts use their own readable background.
- R-35 PASS: app started and inspected in browser; authored selectors, thresholds, tabs, source disclosure and downloads exercised through AppTest and/or browser interaction.
- R-36 PASS: no fabricated performance, security, customer or compliance claims.
- R-37 PASS: approved direction and explicit dials recorded before UI implementation.
- R-38 PASS: real source-derived data throughout; smoke-test scope and unsupported tactical inferences are disclosed.

## Purpose gate

- R-01 PASS: no decorative gradients or glows. Sequential colour in evidence heatmaps encodes quantitative magnitude.
- R-04 PASS: no custom icon set or generic AI icons. Framework controls retain their functional symbols.
- R-06 PASS: native readable sans-serif typography serves chart and table legibility; no decorative monospace or spaced uppercase labels.
- R-07 PASS: pitch geometry and chart axes carry analytical meaning; no decorative background grid.
- R-08 PASS: no decorative arrows on buttons; pitch arrows represent actual passes/carries.
- R-09 PASS: no badges or eyebrow pills.
- R-10 PASS: no glassmorphism.
- R-12 PASS: no authored elevation/shadow treatment.
- R-13 PASS: no glow effects.
- R-14 PASS: no feature-card template. Three headline shares are parallel measures; comparison charts, tables and sequence inspection have different forms.
- R-19 PASS: motion dial 1; no authored animation. Interactions update evidence directly.
- R-22 PASS: no generic illustrations.

## Liveliness and craft

- Dials PASS: Energy 2 / Rhythm 3 / Motion 1, recorded in DESIGN.md.
- Focal point PASS: possession versus threat is the leading analytical chart; Match lab centres on the match and selected sequence.
- Structure PASS: whitespace separates comparison, score-state context and sequence evidence; no landing-page template sections.
- Accent PASS: teal identifies the focus team; rust identifies the rest; marker shape also distinguishes the focus in the scatterplot.
- Identity PASS: repeated pitch coordinates, sequence arrows and precise football metric labels connect the views.
- Design read PASS: written direction and the user's approval preceded UI work.
- C-1 PASS: typography, palette and chart choices have documented analytical purposes.
- C-2 PASS: controls transform real output or deliver an actual export.
- C-3 PASS: every tab answers a distinct part of the requested football question.
- C-4 PASS: desktop/narrow layouts inspected, internal scrolling retained, native focus preserved, empty/loading/error handling present.
- C-5 PASS: claims trace to source audit, manifests and generated statistics.
- R-05 PASS: hierarchy follows comparison, temporal inspection and methods, without invented marketing content.
- R-11 PASS: framework controls and plain chart/table regions replace a uniform pill/card treatment.
- R-15 / R-16 PASS: short factual labels, explicit units and denominators; no marketing filler.
- R-20 / R-21 PASS: restrained, approved light palette; no unrelated themes or motifs.
- R-29 PASS: charcoal/paper neutrals, teal focus, rust comparison; heatmaps use a purposeful sequential scale.
- R-30 / R-31 PASS: native component spacing and hierarchy; prominence reflects the user's analytical question, with no pricing or promotional emphasis.
