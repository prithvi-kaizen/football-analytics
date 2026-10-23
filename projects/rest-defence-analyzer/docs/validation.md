# Validation record

Executed locally on 22–23 October 2026, using Python 3.14.2 and the dependency versions in `requirements-lock.txt`. **Ready for method demonstration and match case study, with the limitations in the methodology.** This record does not certify predictive accuracy or league-wide applicability.

## Independently testable stages

1. **Source review, before analytical implementation.** Read the data paper, original authors' parser and repository licensing; inspected the version-1 Figshare API, real match metadata/events and a tracking byte range. Saved `source-review.md` and the original manifest before coding the pipeline.
2. **Small baseline.** Built parsing, native possession switches, strictly pre-loss snapshots and bounded outcomes. The bundled real-data extract produced 17 candidates. The initial 20 parsing/timing/baseline tests passed before adding geometric features or the frontend.
3. **Geometry and full ingestion.** Added compactness, central cells, clear segments and fixed-score functions. The 27-test suite passed. Downloaded and verified the complete J03WPY tracking XML against original Figshare size and MD5. Full-match ingestion and analysis completed successfully.
4. **App, association and reporting.** Built the Streamlit views from verified outputs, tested controls and empty/error states, added no-future-feature and report-denominator checks, and generated/visually inspected the standalone PNG/SVG. The final suite passes **36 tests**. A timeline check caught a 5 Hz plot-baseline offset; the final ball timeline retains 25 Hz and its first new-control frame, and a real-data regression check confirms the plot's maximum equals the outcome measure.

## Real-data end-to-end evidence

| Check | Observed result |
|---|---|
| Full source match | J03WPY, Fortuna Düsseldorf vs 1. FC Nürnberg |
| Original tracking XML | 371,688,499 bytes; MD5 `e56ff1336a334f8da51110fbe7cab764` |
| Source tracking rows read | 3,362,853 |
| Native ball frames | 146,211 |
| Clean 5 Hz player rows | 643,346 |
| Invalid coordinates / unknown entities | 0 / 0 under the declared cleaning bounds |
| Stable live-ball candidates / accepted | 293 / 293 |
| Rejected pre-loss snapshots | 0; every accepted snapshot has 22 players and one goalkeeper per side |
| Attacking-loss report denominator | 168 uncensored transitions with a defined score |
| Ball advanced ≥10 m / shots in this subset | 94 / 1 |
| Undefined score | 1 of all 293; the clipped central grid has no cell centres |
| Full-match censored windows | 0 |
| Event-corroborated attacking losses | 120 / 168 within ±2 s; not an exact-alignment guarantee |
| Persistence sensitivity | 293 candidates at 0.4 s; 258 at 0.8 s; 232 at 1.2 s |
| Independent XML count audit | All 293 behind-ball counts, ball x coordinates and 22-player snapshot counts match; zero mismatches |

The independent audit (`scripts/validate_real.py`) reads native XML directly, reconstructs roster goalkeeper flags and half directions itself, and does not call parsing, orientation or geometric analysis helpers. It is an independent arithmetic/selection check, not independent provider or video ground truth. Its machine-readable result is `outputs/J03WPY/independent-validation.json`.

### Small download and offline run

* Built a verified index of **23** source byte ranges: 22 active players and the ball, native frames 10000–14500. Frame-line payload: **11,304,666 bytes**, plus ~711 KB original metadata/events and reconstructed XML wrappers. The sample is not a prefix of the entity-major file.
* A **fresh network download into `/tmp/rest-defence-remote-sample`** succeeded. Every response was HTTP 206 with the requested Content-Range and SHA-256. Its 17 accepted transitions match the bundled extract.
* The offline bundled pipeline succeeds without network access. It detects 17 turnovers, 5 with ≥10 m advancement, no shots, and 1 right-censored source-end window.
* All 17 sample anchors have identical pre-loss features in the full-match release. Their last outcome differs appropriately when the complete match extends beyond the sample cut.
* Clean-cache reruns reproduce identical DataFrames. Tampered result files fail integrity validation. Raw full files, compressed sample files, byte ranges and published outputs have separate integrity checks.

## Scope of tests and UI inspection

`pytest -q`: **36 passed**. Tests include true timezone equivalence, native duplicate rejection, real metadata/event parsing, half-specific rotation, exact snapshot precedence, persistence/dead-ball/gap/half exclusions, static corridor endpoint handling, known RMS/hull calculations, empty geometry, censoring, shot team/half/window membership, corrected-frame preference, actual pitch-length thresholds, future-event/player perturbations, cached real-data end-to-end runs, report denominator reconciliation, and Streamlit interactions.

Streamlit AppTest exercises match/sample switching, team and half filters, attacking/corroboration filters, score ranges and empty selections, turnover selection, replay frame changes and recoverable source-error display. Native browser inspection additionally exercised the replay slider with ArrowRight, all three tabs and the CSV download control. The slider's displayed relative time changed from −0.12 to +0.08 s. Source links expose the original DOI/licence destinations.

The rendered pitch and standalone publication chart were visually inspected. The app was viewed at 1280 px and a 561 px CSS viewport; the latter reflowed metrics into a single column, retained the pitch/tabs/controls, and measured document width 561 px with viewport width 561 px. No horizontal page overflow was present at the tested narrow width. Smaller devices and screen-reader behaviour have not been exhaustively tested.

Computed contrast: charcoal `#202c2b` on `#faf9f5` **13.69:1**; white on red `#9f2936` **7.38:1**; white on teal `#086b67` **6.35:1**. Team role is also encoded by circle/triangle shapes and shirt numbers. Keyboard controls and visible focus are retained; no focus outlines are removed.

## Material remaining limits

Only J03WPY has received the full ingestion and independent audit; the other six manifest IDs are supported but untested. There are no video-labelled turnover/intent annotations. Event timestamps remain imperfect, corridor availability is static geometry, and the score has approximately zero within-match rank association with ball movement. No learned model or held-out test result is presented. The included CI workflow has been authored but has not run on GitHub in this session.

## GitHub/Vercel publication checks

The public browser companion is packaged from the same verified full-match outputs. The extended suite passes **39 tests**, including every exported transition, native timeline maxima, snapshot/player completeness, analytical-code fingerprints and modified-asset rejection. The root website build uses only the Python standard library and preserves the existing project routes.

Local browser checks confirmed the default 168-turnover / 94-advance / 1-shot scope, Düsseldorf's 81 / 47 / 1 selection, and all-turnover totals of 293 / 153 / 13. Combined half/event filters, native keyboard frame stepping and recorded-frame playback were exercised. Static replay coordinates are recorded 5 Hz positions, with no interpolation; the 25 Hz outcome timeline begins at the native new-control frame.

No full raw tracking, clean cache, environment, credentials or unrelated local project is part of the release. See `deployment.md` for the publication architecture and refresh commands.
