# Validation record

Completed 23 October 2026. Python 3.14.2; exact dependencies in `../requirements-lock.txt` and versions in `run-summary.json`.

## Analytical checks

- PASS: complete pinned real-data run, all 82 matches; then a complete offline rerun using 167 verified source receipts.
- PASS: four-match logistic smoke pipeline and offline reproduction, 2,257 eligible passes. Insufficient recipient-proxy training data causes an explicit model omission.
- PASS: 42 tests covering parsing, outcome coding, normalized coordinates, finite off-pitch defenders, withheld off-pitch targets, segment geometry, period timing/stoppage, strict earlier-event matching, missing/duplicate joins, cache corruption/offline behavior, match splits, probability inference, and Streamlit state changes.
- PASS: outcome/endpoint/length/angle/duration mutations do not alter prediction features. Future or other-period player observations cannot supply a target.
- PASS: all model comparisons use identical event IDs within each population. All predictions used for scoring and the review queue belong to held-out matches. Model bundles contain only training-match IDs; their plain JSON inference reproduces sklearn probabilities to 1e-12.
- PASS: real source count/label/join checks for Germany vs Scotland; every retained row's origin and label agree with the selected raw events in that match. This is a sampled independent source check, not an independent recoding of every event in the tournament.
- PASS: all recorded output hashes verified. Regenerating the calibration PNG and SVG from saved predictions produces byte-identical files.
- PASS: Ruff lint and formatting checks.
- PASS: source data and pass-level outputs are excluded by Git. Only original code, source documentation/notices, aggregate findings, calibration and metric summaries are intended for version control.
- PASS: dependency metadata identifies open-source licenses; no paid API, account credential or scraped data is used.

## Final scope

54,200 eligible passes; 48,205 framed observations with visible opponents; 2,122 recipient proxies (4.4%). Whole-match split: 61 train, 21 test. Context logistic log loss: 0.223219 event origin/period, 0.202223 with 360 context. Target training/holdout observations: 1,559/563. The fixed queue contains 184 hypothetical lanes across 146 held-out events. These are unvalidated review hypotheses, not confirmed missed opportunities.

Source audit records 7,470 finite off-pitch frame-player observations in the eligible snapshots. They remain in opponent geometry and are counted separately; off-pitch targets are excluded from target training and candidate probabilities. No malformed frame-player coordinates were found in this run. There are 74 excluded unknown pass outcomes and 5,961 retained passes without frames.

## Rendered and interaction checks

The local Streamlit app was run at `http://127.0.0.1:8517/` and inspected in the in-app browser. Browser checks exercised the review filter, model population selection via keyboard, all three tabs, pitch fullscreen/close, source-observation disclosure, and findings download. The downloaded findings matched the generated Markdown byte for byte. AppTest additionally changes tournament, partition, match, team, possession, pass, candidate, model population and calibration selections, including an empty calibration selection. Missing/corrupt output states are tested.

Responsive checks: widths 390, 820 and 1280 pixels. Browser DOM measured document widths of 390, 820 and 1280 respectively, with no page-level horizontal overflow. Native wide tables scroll inside their containers. Phone controls stack; larger screens use paired selectors. The selected event's heading and context remain readable. Desktop pitch labels, observed/hypothetical line styles and camera shading were inspected; the final legend was moved outside the pitch with automatic tight layout disabled to prevent overlap.

Palette contrast against paper: ink 13.37:1, caption 6.82:1, teal 5.92:1, rust 6.00:1. Native controls retain keyboard focus behavior; a visible teal focus outline was inspected during keyboard selection. The native Streamlit and Plotly components retain their own accessibility and export behavior; this is not a claim of a formal accessibility certification.

## Antislop delivery gate

Direction: user chose warm-paper editorial and application during the build. Design read: analyst possession workbench, ENERGY 2 / RHYTHM 2 / MOTION 1. Reasons are recorded in `../DESIGN.md`.

- R-02 PASS: no decorative em dashes in authored app copy.
- R-03 PASS: rendered 390/820/1280 checks and matching document widths; wide tables contained.
- R-17 PASS: all displayed counts and rates come from saved source-derived tables or model outputs.
- R-18 PASS: no testimonials or invented identities; anonymous frame labels are explicit.
- R-23 PASS: user requested charts/app; official existing StatsBomb attribution asset reused; no invented branding or photos.
- R-24 PASS: heading anchors resolve to existing headings; source links use the pinned repository and verified Hudl article.
- R-25 PASS: authored text/accent palette ratios exceed 4.5:1; captions measured from rendered DOM.
- R-26 PASS: authored selectors exercised by AppTest; tabs, source disclosure, fullscreen and findings download verified in browser.
- R-27 PASS: setup-empty and corrupt-output errors tested; cached data loader has a loading label; no-target/unsupported cases have visible explanations.
- R-28 PASS: no template FAQ.
- R-32 PASS: native labeled comboboxes and keyboard population change verified; visible focus outline retained.
- R-33 PASS: UI authored in app.py/viz.py; no runtime script patches another application's styles or source.
- R-34 PASS: fixed light editorial theme and figures inspected; no nonfunctional theme toggle.
- R-35 PASS: app run, source-based interaction tests, browser click-through, fullscreen and byte-verified download completed.
- R-36 PASS: no security, compliance, customer or counterfactual-performance claims.
- R-37 PASS: user selected direction; explicit dials and reasons in DESIGN.md.
- R-38 PASS: source-based observations only; synthetic test fixtures are labeled and never displayed as findings.
- R-01 PASS: paper supports reading; teal marks candidate lanes and rust marks opponents/recorded action. Native information box marks uncertainty.
- R-04 PASS: no decorative icon library; native widgets keep functional icons.
- R-06 PASS: serif heading/figure titles provide the editorial accent; native sans-serif controls support dense data reading.
- R-07 PASS: the only spatial grid/lines belong to the football pitch or quantitative chart axes.
- R-08 PASS: arrows denote the recorded pass, not decorative calls to action.
- R-09 PASS: no promotional capsules or duplicate eyebrow labels.
- R-10 PASS: no glassmorphism.
- R-12 PASS: no decorative component shadows.
- R-13 PASS: no glows.
- R-14 PASS: no repeated feature-card template; pitch, candidate table and diagnostics have different analytical jobs.
- R-19 PASS: no decorative animation; changes occur in response to selections.
- R-22 PASS: diagrams use actual source observations; no generic illustration.
- Liveliness PASS: explicit 2/2/1 dials, serif pitch-first editorial motif, structural whitespace and selective lane accents, as recorded in DESIGN.md and inspected in rendered views.
- C-1 PASS: major palette, layout, typography, spacing and motion choices have written purposes in DESIGN.md.
- C-2 PASS: all authored controls have tested behavior; source and download actions resolve.
- C-3 PASS: possession, candidate evidence, model validation and methods follow the actual research question; no template filler sections.
- C-4 PASS: responsive checks, empty/corrupt states and keyboard selection completed; native component limitations are not claimed away.
- C-5 PASS: output provenance, source attribution, selection bias and uncertainty accompany observations and estimates.
- R-05 PASS: one content hierarchy separates source selection, pitch, candidate geometry and model evidence.
- R-11 PASS: native control radii retained; no repeated capsule/card styling.
- R-15 PASS: native control/table conventions and shared number formats remain consistent across selections.
- R-16 PASS: copy describes actual measurements and restrictions, with no promotional AI claims.
- R-20 PASS: warm-paper football workbench and stable spatial encodings implement the selected direction.
- R-21 PASS: fixed light theme serves the chosen paper style and static figure consistency.
- R-29 PASS: ink/paper neutrals, teal and rust carry the main visual vocabulary; native information color indicates a real caution state.
- R-30 PASS: original analysis composition; no imitation of another product UI.
- R-31 PASS: purpose statements retained in DESIGN.md.

## Limits of this verification

The GitHub Actions smoke workflow was added but has not been run remotely. Local numerical results were verified on the recorded Python 3.14 environment; cross-version numerical equality is not asserted. No video review, anonymous-player identity audit or observed counterfactual pass outcomes are available. Marginal training-range checks do not establish joint statistical support, calibration on unchosen targets, offside legality or tactical superiority. These limitations remain visible in the app, README and findings.

## GitHub and Vercel publication checks

The public companion adds 12 reproducibly selected held-out cases from 12 distinct matches, with 88 attributed candidate-highlight figures. The analysis JSON contains derived estimates and aggregate scores, with no raw coordinates, snapshots, coefficients or training tables. All 12 cases and target switching were exercised in the browser; evaluation-population changes and the methods view were also checked. The same paper/ink direction and 2/2/1 design dials apply.

The standard-library portfolio build verifies and restores all published project releases without downloading source data or importing analytics dependencies. The test suite now includes static-release hashing, bounded case selection, raw-coordinate exclusion and fresh-output build checks: 44 tests pass locally. JavaScript syntax, Python lint and formatting checks also pass. Responsive checks cover 390, 820 and 1280 pixel widths, native labeled selections, contained tables and visible focus states.

The GitHub workflow includes the static build as well as the real four-match smoke run. Its remote status and Vercel status are reported separately after publication; this local check does not imply that a remote job already succeeded. Raw downloads, local models, unbounded pass-level tables and the unrelated projects in the workspace remain excluded from the publication commit.
