# Validation receipt

Completed 23 October 2026. No publication or deployment was performed. The local Streamlit app is available at http://127.0.0.1:8512 while its process is running.

## Real-data coverage

| Run | Matches | Training / held out | Purpose |
| --- | ---: | ---: | --- |
| Liga F smoke test | 6 | 4 / 2 | Small end-to-end example |
| Five-league sample | 30 | 20 / 10 | Six matches per league; schema and application compatibility |
| Full Liga F | 240 | 192 / 48 | Barcelona and domestic-rival analysis |

The full Liga F run processed 835,429 events and 70,148 analytical possession phases. All 30 Barcelona league fixtures are in the source selection, with six in the chronological holdout. The other four complete league seasons are supported by the ingestion interface but were not analysed in full.

## Checks actually run

- `.venv/bin/python -m pytest -q`: **34 passed**. Covers timestamp parsing, halftime/stoppage timing, coordinates/grid edges, score-before-event order, own goals, shootouts, pass outcomes, overlapping durations, possession boundaries, opposing attacks inside provider chains, weighted rates, zero denominators, closed-form xT, failure absorption, leakage rejection, cache integrity, failed-build preservation, repeated real-data runs and Streamlit controls.
- Every full-season final scoreline reconciles with event goals.
- All source passes, shots and shot xG reconcile with possession totals. This check exposed the provider-chain-starter issue; the final implementation retains opposing on-ball attacks and splits the analytical sequence.
- Event IDs and analytical sequence keys are unique. Training/test match sets are disjoint. Active time never exceeds sequence elapsed span.
- Team possession shares sum to 100% within floating-point tolerance (maximum error approximately 1.42 × 10⁻¹⁴ percentage points).
- Score-state and team-match xT/time totals reconcile with sequence totals in real-data tests.
- All saved output hashes match their manifests for all three datasets. The repeated sample run checks byte-identical CSVs, summary, PNG and SVG files.
- The full model converged in 83 iterations, with Bellman residual approximately 6.61 × 10⁻¹¹. On 83,472 held-out actions, shot-choice Brier score is 0.00997 versus 0.01447 for the constant training-rate baseline. This is a one-step diagnostic, not full xT calibration. No held-out action starts in an unseen training cell.
- Exactly one tiny negative source duration is repaired to zero and reported with its original value. No source JSON is edited.

## Application and exports

Streamlit AppTest exercises every sample league, held-out/training/all-match selection, team selection, match and sequence selection, threat/territory switch, duration/xT thresholds and the empty-result message. All controls rerun without application exceptions.

Rendered review used the in-app browser. The team-comparison, Match lab and methods views were opened. The source audit disclosure was expanded and its reconciliation correction was visible. Keyboard adjustment of the duration threshold changed its value. Desktop and narrow mobile views were inspected; page scroll width equalled the viewport width. Native tables and tab strips retain internal scrolling where necessary. Screenshots: [desktop](dashboard-desktop.png), [mobile](dashboard-mobile.png).

The team-comparison CSV downloaded and contains the 16 Liga F teams. The findings Markdown and reproducible PNG also downloaded; their hashes match the generated full-league files. Downloads were verified after registration of the browser's download event.

The server was restarted after final source edits so the delivered app uses the final imported modules. Browser logs contain expected transient health-check failures during restarts; the reloaded application subsequently displayed the correct scope and values without a visible error. Final rendered inspection also found and fixed Streamlit's faded captions; their opacity is now 1. The two application tests were rerun after that style-only change.

## Observed result and limits

Barcelona's six held-out fixtures average 68.4% active possession-time share, 94.0% final-third completed-pass share and 88.2% positive move xT share. Barcelona generates 3.17 positive move xT per 100 analytical possessions versus 0.45 for opponents in those same fixtures. The paired difference is +2.72, with a 95% fixture-bootstrap interval of +2.42 to +3.01 (2,000 resamples, seed 2026).

These are descriptive results for six fixtures under an explicit segmentation rule and location-only model. The interval omits model-refit uncertainty. Active time is not official possession; field tilt is not tracked spatial control; positive xT can count repeated advances. Low immediate threat can still be tactically useful. No causal interpretation or opponent-strength adjustment is claimed.

The code, dependency lock, original source licence, source audit, manifests, generated report and chart are retained together in this project. Raw JSON and row-level CSVs remain local and Git-ignored.
