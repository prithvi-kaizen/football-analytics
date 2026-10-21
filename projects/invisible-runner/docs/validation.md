# Validation record

Local verification: 21 October 2026. Python 3.14.2 on macOS arm64. Exact package versions are recorded in `requirements-lock.txt` and both portable provenance files.

## Automated checks

Final command, from this project:

```sh
MPLCONFIGDIR=/private/tmp/invisible-runner-mpl \
XDG_CACHE_HOME=/private/tmp/invisible-runner-cache \
.venv/bin/python -m pytest -q
```

Result: **33 passed in 4.26 seconds**. Unit fixtures are synthetic and confined to tests. Integration tests use the actual public data. `git diff --check` also passed. A GitHub Actions workflow downloads the bounded sample and runs the suite; remote CI has not been executed in this session.

| Check | Evidence |
| --- | --- |
| Parsing | Reject malformed JSON, duplicate/reversed frames and duplicate players; count null periods, unknown IDs and invalid positions |
| Coordinates | Preserve physical metres; test linear 6 m/s movement, opposite attacking directions and mirrored-pitch metric invariance |
| Timing | First-period frame 28 maps to 1.8 s; second-period frame 27824 maps to 45:02.4; test phase boundaries and possession exclusions |
| Cleaning | Break missing frames, reject jumps before smoothing, exclude segment boundaries |
| Calculations | Exact fixed-cell free area, stationary-defender zero changes, defender displacement, line crossing and missing-roster exclusions |
| Cache | Hash verification, bounded prefix, cache reuse, corruption recovery and failed-download cleanup |
| Leakage | Provider off-ball-run/outcome fields absent from detector inputs; no fitted model |
| End to end | Fresh public sample download, cached rerun, reports/charts/CSV generation; complete-match direction and clock checks across both periods |
| Replay | First and last timeline areas equal the corresponding published run metrics |
| AppTest | Dataset/team/type/quality filters, empty result, frame control, return to start and threshold recalculation |

## Real-data execution

- Sample: match 1886347, first 3,000 source frames, 63,008 valid player rows. Seventeen detected runs and seventeen valid patch comparisons.
- Full match: 59,061 source frames, 956,037 valid player rows. Thirty-nine invalid positions were excluded; twelve player rows were flagged at raw jumps. The detector found 303 qualifying runs and 299 valid patch comparisons.
- Full match: 223 runners were detected throughout the run. Only five runs also have all contextual players detected at both endpoints and the ball detected at both endpoints.
- Both scopes use the same source revision. Final provenance code fingerprints match the current analytical module sources. Source, output and clean-cache SHA-256 values are retained. Matching dependency versions are part of the processed-cache key.

These checks establish execution and arithmetic consistency. They do not establish detector accuracy against human labels or causal effects.

## Browser verification

Verified in the in-app browser at normal width and desktop/phone viewport overrides. Actual CSS widths reported by the browser were 1,163 px for desktop and 354 px for phone. At both, document scroll width equalled viewport width; there was no page-level horizontal overflow. A clipped mobile heading was corrected and rechecked. Temporary viewport overrides were reset.

| Authored control/view | Observed behavior |
| --- | --- |
| Dataset selector | Full match shows 303 runs; bounded sample shows 17 |
| Team selector | Auckland sample shows 3 runs; returning to All is covered by AppTest |
| Run type | Behind-line Auckland sample shows 1 run |
| Observation coverage | Strict sample filter shows 0 runs with an explicit recovery message; All estimates restores the population |
| Speed/distance sliders | Keyboard changes to 5.5 m/s and 6 m; Recalculate runs shows 205 runs, 203 valid patch comparisons; defaults restored |
| Run selection | Changing filtered population selects the corresponding real player and clock |
| Play/Pause | Frame advances and Pause becomes enabled; Pause stops playback |
| Replay slider | Right-arrow advances from frame index 1 to 2 and from source frame 56 to 61 |
| Return to start | AppTest verifies the control without an exception |
| Pitch | Player markers, runner star, teammate diamond, ball, movement trace and fixed-area cells render |
| Timeline/distribution | Lines and scatter points render with units, legends and hover data; valid replay endpoints reconcile with CSV |
| Run records | Expander opens a real table with the selected player and behind-line flag |
| Methods | Expander opens metric definitions, quality audit, source links and provenance export |
| Filtered CSV | Browser download contains exactly 3 records, all team ID 4177, matching the displayed Auckland sample filter |

Browser console inspection returned no warning/error entries at the desktop inspection checkpoint. Empty-result and loading states were exercised. The missing-file/checksum error branch was reviewed in source, not deliberately injected in the browser. This is a functional review, not an accessibility certification or an exhaustive browser/device matrix. No claim of touchscreen or screen-reader certification is made.

## Anti-slop delivery gate

User chose application during implementation and the light editorial analyst-desk direction. `DESIGN.md` records the design read, dials and reasons. No skill installation or entry-file modification was required.

| Gate item | Status and concrete evidence |
| --- | --- |
| R-02 authored copy | PASS: authored UI uses ordinary punctuation; third-party source documentation is preserved verbatim |
| R-03 responsive layout | PASS: desktop and phone screenshots reviewed; DOM width measurements show no global horizontal overflow; mobile heading repaired |
| R-17/18/36/38 evidence | PASS: displayed players and numbers originate in pinned real data; no testimonials or marketing claims |
| R-23 assets/direction | PASS: user explicitly requested charts, pitch visuals and real metrics; user selected light editorial direction; text-only project name |
| R-24 navigation | PASS: no marketing navigation; source links point to the inspected pinned repository and license |
| R-25 contrast | PASS: contrast checker gives ink/paper 13.98:1, teal/paper 6.33:1, rust/paper 6.44:1, caption/paper 7.39:1 |
| R-26 controls | PASS: filters, threshold form, play/pause, frame inspection, records and CSV export exercised as recorded above |
| R-27 states | PASS: explicit loading, empty and error branches; loading/empty exercised and error branch reviewed |
| R-28 FAQ | PASS: none introduced |
| R-32 keyboard | PASS: native labelled controls; keyboard threshold and replay changes observed; custom visible focus ring retained |
| R-33 source edits | PASS: authored UI/CSS written directly through patches, without an external source-rewriting script |
| R-34 themes | PASS: fixed light direction requested by user; no custom theme toggle |
| R-35 execution | PASS: live Streamlit process, automated app tests and recorded browser interactions; charts inspected |
| R-37 direction | PASS: explicit user direction and `DESIGN.md`, ENERGY 1 / RHYTHM 2 / MOTION 1 |
| Purpose gates | PASS: paper/ink aid reading, teal/rust encode roles, shapes encode visibility, serif heading supplies editorial voice; reasons written in `DESIGN.md`; no decorative gradients, icons, glows, badges or stock illustrations |
| Liveliness | PASS: declared dials; pitch is the detail focal point; whitespace separates controls/replay/evidence; sparse role colours and repeated pitch geometry supply identity |
| C-1/C-3/R-05/R-31 | PASS: each view serves selection, movement inspection, comparison or provenance; design reasons documented; no template marketing sections |
| C-2/C-4/C-5 | PASS: tested behavior, explicit unavailable values and evidence-based copy; bounded review limits disclosed above |
| R-11/R-15/R-16 | PASS: native control geometry, specific action labels and factual prose |
| R-20/R-21/R-29/R-30 | PASS: requested light editorial identity, restrained teal/rust palette and original football-specific composition |

## Remaining scientific limitations

No human-labelled run-detection accuracy study, causal identification, learned model, or complete ten-match analytical survey is claimed. The MVP validates one full match and a bounded excerpt, and supports additional explicit match IDs. Extrapolated defenders can dominate the space estimate even when the runner is fully detected. Provider-label overlap is descriptive agreement against annotations derived from the same source tracking. The linked formal PDF specifications were inaccessible through the web reader; only inspected repository documentation and actual fields govern the baseline.

## GitHub and Vercel publication review

The publication stage adds an independently buildable browser version in `web/`, three reviewed detection profiles and five release tests. The final expanded local suite passed **38 tests in 5.46 seconds**. `node --check web/app.js`, `git diff --check` and the standard-library-only combined repository build also passed. The existing pressing dashboard release is copied unchanged to the root route.

The gzip snapshot contains 444, 303 and 209 runs at 4.5, 5.0 and 5.5 m/s respectively. Browser filter checks reproduce those counts and the 5-run strict-observation subset. Run-type filters reproduce 21 behind-line, 47 wide-channel and 57 toward-space runs. All 956 packaged replays pass endpoint/frame/identity checks; source positions are sampled at 2 Hz for display while metrics retain the original 10 Hz calculations.

Browser checks exercised profile/team/type/quality filters, minimum-distance selection, reset, empty-result recovery, run selection, playback, pause and keyboard frame inspection. Playback advanced a 7.3 s run to its final frame; pausing a replay left it at 0.5 s and restored the Play label. The filtered CSV download contained exactly 5 Auckland records, all with runner and endpoint-context detection fractions equal to one, matching the selected filter.

Pitch traces, visibility markers, changing free-patch cells, timeline and scatter points rendered without recorded console warnings/errors. Desktop and phone layouts were inspected; at phone size the DOM reported a 354 px viewport and 341 px document width, without horizontal overflow. The initial source/loading state has an explicit message; an empty filter combination shows an explicit recovery message. Snapshot SHA-256 verification occurs in the browser before rendering. Corrupted asset rejection and path/privacy checks are automated.

Publication UI gate: **PASS**. The recorded user direction continues in the browser layout; no new logos, stock images, fictitious measurements or marketing claims were introduced. Native controls retain keyboard focus; controls have explicit labels and minimum 44 px height. The existing colour contrast measurements apply to the reused paper, ink, teal and rust palette. Source/project links, chart and data downloads preserve attribution and units. No new analytics claim is implied by hosting the snapshot.
