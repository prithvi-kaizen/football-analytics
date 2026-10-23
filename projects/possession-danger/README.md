# Is possession actually dangerous?

A reproducible Python and Streamlit project separating possession volume from territorial control and attacking value in women's football. Uses only free StatsBomb research data and open-source Python packages. No account, API key, paid service or scraping is needed.

**Website:** [Possession danger dashboard](https://football-analytics-self.vercel.app/possession-danger/) · **Code:** [project on GitHub](https://github.com/prithvi-kaizen/football-analytics/tree/main/projects/possession-danger)

The website runs from reviewed derived results in the browser. It includes the comparison charts, score-state analysis, match timelines, quiet-possession list and style thresholds. The Python/Streamlit workbench adds event-level pitch inspection and recalculation after a source download. See the [hosting and release guide](docs/deployment.md) for the distinction and deployment settings.

The app includes a possession-versus-threat scatterplot, team comparisons, action-level score-state rates, an interactive match timeline, longest quiet possessions, mplsoccer sequence maps and an inspectable xT surface. Exploratory style labels use visible thresholds.

## Run the small MVP

To view the published browser release from a clean clone, without analytics dependencies or raw data:

```sh
python3 scripts/build_website.py  # Run from the repository root
python3 -m http.server 4173 --bind 127.0.0.1 --directory dist
```

Open `http://127.0.0.1:4173/possession-danger/`. The commands below instead run the analytical Python/Streamlit workbench.

Python 3.11+ can resolve compatible packages. The exact lock was tested with Python 3.14.2 on macOS.

```sh
cd projects/possession-danger
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-lock.txt
python -m pip install -e . --no-deps

# Six real matches, including Barcelona and unrelated Liga F fixtures.
python -m possession_danger.cli download --sample 6
python -m possession_danger.cli run --sample 6 --offline
python -m pytest -q
python -m streamlit run app.py
```

For Python versions incompatible with the exact lock, install `python -m pip install -e '.[test]'` instead. Use the manifest to identify the actual resolved versions. The sample is a functional test and deliberately cannot support season conclusions. Downloads require internet; cached reruns, tests and the dashboard run offline.

## Full Liga F and the other leagues

```sh
# 240-match season, including Barcelona's 30 league fixtures.
python -m possession_danger.cli download --full --workers 6
python -m possession_danger.cli run --full --offline --output outputs/liga-f

# Verify a six-match sample from every released league.
python -m possession_danger.cli download --league all --sample 6
python -m possession_danger.cli run --league all --sample 6 --offline --output outputs/all-leagues-sample

# Or select wsl, bundesliga, serie-a or nwsl; --full selects the whole league.
python -m possession_danger.cli download --league wsl --full
python -m possession_danger.cli run --league wsl --full --offline --output outputs/wsl
```

The five-season catalog is supported. Full Liga F and the 30-match cross-league sample were exercised here; the other four complete seasons have not been analysed. Full Liga F's cached JSON is roughly 800 MB; derived CSVs require additional space. Downloads retry, use at most eight workers, and cache an immutable source revision. To redownload a corrupt cache record, remove that record and its receipt; integrity failures never silently replace data.

Select the generated dataset, match split, league and team in the sidebar. The primary view defaults to held-out matches. Training and all-match views are explicitly descriptive. Global scope applies to charts, tables and exports. The timeline window and style thresholds apply only inside Match lab.

## Sources and licensing

The [source audit](docs/source-audit.md) was written before analytics code. It records field inspection, terms and limitations. The [official release](https://www.hudl.com/blog/statsbomb-free-womens-data-wsl-ligaf-bundesliga-seriea-nwsl) identifies these seasons:

| League | Competition / season ID | Season |
| --- | --- | --- |
| Liga F | 182 / 281 | 2023/24 |
| WSL | 37 / 281 | 2023/24 |
| Frauen Bundesliga | 135 / 281 | 2023/24 |
| Serie A Women | 131 / 281 | 2023/24 |
| NWSL | 49 / 107 | 2023 |

[StatsBomb Open Data](https://github.com/hudl/open-data) is pinned to revision `4b73468fc5b0f1950f9f66fada70ad3a4f9327cb`. It is free research data under its [Public Data User Agreement](docs/source/LICENSE.pdf), **not an unrestricted open-source data licence**. The terms restrict commercial exploitation and raw-data redistribution and require StatsBomb credit and its original logo. Raw downloads and row-level outputs stay local and Git-ignored. The app and public chart include attribution. Review the supplied terms before a new use; this project's MIT licence covers original code only. Provider data, documentation and branding retain their terms.

Dependencies include NumPy (BSD), pandas (BSD), Requests (Apache-2.0), Streamlit (Apache-2.0), Plotly (MIT), mplsoccer (MIT), Matplotlib (PSF-based) and pytest (MIT). See the pinned dependency list and the packages' original notices.

## Method

1. Validate IDs, timestamps, locations and durations. Reconstruct the score before each indexed action; reconcile every final score with the fixture metadata. Count own-goal-against once and exclude penalty shootouts.
2. Segment contiguous provider possession IDs at period boundaries, then split again whenever a pass, carry, shot, dribble, miscontrol, dispossession or shield is performed by the other team. `possession_team` identifies the provider chain's starter and can persist through an opposition counterattack. Preserve that starter separately; defensive pressures, blocks and tackles do not switch the analytical owner. Require at least one such on-ball anchor per sequence. Reconcile all source passes, shots and shot xG to sequence totals.
3. Calculate elapsed span, unioned active action-duration intervals, attempted/completed passes, final-third passes, start/end/peak x, net territorial progression, shots and supplied xG.
4. Hold out the latest 20% of fixtures **per competition**, rounding up. Fit one 12 × 8 xT grid on training matches only. Model files expose training match IDs and cell counts.
5. Solve `V = r + T V`: `r` is non-penalty goals per eligible action; `T` is completed pass/carry transitions divided by all eligible actions in the start cell. Failed passes, miscontrols, dispossessions and failed dribbles absorb at zero. All restarts except penalties are included. No supplied xG or test outcomes enter fitting; unseen cells remain zero.
6. Value successful passes/carries with `V(end) - V(start)`. Keep signed net xT, positive-only move xT and turnover losses separate. Positive xT can count repeated advances; it is not a possession scoring probability. Supplied shot xG provides a separate descriptive outcome measure.

The possession percentage is **active possession-time share**, not an official provider statistic. Field tilt is the share of completed passes **starting** at x ≥ 80. Coordinates use StatsBomb's 120 × 80 pitch, already facing the action team's attacking right; no halftime rotation or conversion to metres. Team xT per 100 possessions divides summed xT by summed possession counts; headline shares are arithmetic means of fixture-level shares.

Every shot terminates the model path, including misses; a rebound can continue the analytical possession but starts a new valuation path. This is one reason the fitted surface is not automatically calibrated to whole-possession goal probability.

Score-state tables assign actions using the score before the action. A goal shot therefore belongs to the pre-goal state. Rates divide by the team's active possession minutes in that state, not total match minutes. Sequence labels describe the state at sequence start.

The style rules are deliberately simple: high volume / low threat = elapsed ≥ 30 seconds **or** ≥ 10 passes, positive xT < 0.01 and no shot; direct / high threat = elapsed ≤ 15 seconds, ≤ 4 passes and positive xT ≥ 0.05; otherwise Other. Match lab lets you vary duration and low-xT thresholds. They are exploratory labels, not learned tactical classes.

References: [Karun Singh's original xT explanation](https://karun.in/blog/expected-threat.html), [socceraction's xT reference](https://socceraction.readthedocs.io/en/stable/documentation/valuing_actions/xT.html), and the official [event specification](docs/source/events.pdf). This is an independently implemented NumPy baseline, not copied pretrained weights.

## Findings and reproducible outputs

The [full Liga F report](outputs/liga-f/findings.md) answers the Barcelona question on held-out fixtures, with a paired opponent comparison and fixture-bootstrap interval. The [PNG](outputs/liga-f/possession-vs-threat.png) and [SVG](outputs/liga-f/possession-vs-threat.svg) are suitable for a technical post. All are generated by the full pipeline command above; nothing is manually entered. The sample report is labelled as a smoke test.

In the six held-out Barcelona fixtures, Barcelona averaged **68.4% active possession-time share** and **88.2% positive move xT share**. It generated **3.17 positive move xT per 100 analytical possessions**, compared with **0.45** for opponents in those same fixtures. These reconciled results describe measured on-ball danger in that schedule under this model, not a causal effect of possession or an official possession statistic.

Every run writes a source-and-output `manifest.json`, `summary.json`, transparent `xt_model.json`, the report, both chart formats and local CSV tables. The manifest records source URLs, file hashes, dependency versions, exact match splits, configuration and code hashes. The sample end-to-end test repeats the run and checks byte-identical analytical outputs and chart files.

To rebuild only the report and charts, run `python -m possession_danger.cli render --output outputs/liga-f`. This checks the saved analysis hashes first and records presentation code hashes separately; it does not refit or alter analytical tables. After changes to analysis code, use the full `run` command.

## Validation, cleaning and limits

Tests cover parsing, successful/failed pass semantics, coordinates and grid edges, halftime/stoppage timing, score-before-event ordering, own goals, shootout exclusion, interval overlap, possession boundaries, denominator-zero handling, weighted rates, closed-form xT values, failure probability, leakage rejection, caching and Streamlit filters. Real-data checks reconcile scores, team shares, sequence totals and score-state totals. Run `python -m pytest -q`; real-data tests skip clearly if their downloads/outputs are absent.

The completed run passed **34 tests**. See the [validation receipt](docs/validation.md) and [design review](docs/design-review.md) for the checks actually performed, export verification and desktop/mobile screenshots.

Publication adds five release tests, including browser/Python metric parity: **39 tests pass locally**. Fresh clones intentionally skip cache-dependent tests until source matches are downloaded; the CI workflow performs the real six-match download and offline smoke run. Static release checks run without those caches. The [publication review](docs/publication-review.md) records static-site checks and the remaining browser review limits.

Full-season inspection found one interception in match 3911552 with duration −0.090642 seconds. The explicit rule sets finite durations in [−0.1, 0) to zero, retains `raw_duration`, and reports all affected records. Larger negatives fail. Missing durations contribute zero time; missing locations exclude an event from xT fitting rather than creating coordinates.

The held-out diagnostic compares one-step shot-choice Brier score with a constant training-rate baseline. It does **not** establish full xT probability calibration. The bootstrap resamples matched Barcelona fixtures 2,000 times with seed 2026; it omits model-refit uncertainty and has few Barcelona observations. This release contains one season per league, with uneven schedules and no opponent-strength adjustment. The pooled cross-league sample is a compatibility check, not evidence of league equivalence.

Event durations do not measure all ball-in-play time. Final-third passes do not reveal off-ball territorial occupation. xT uses only location, reflects empirical finishing, and can be unstable in rare cells. Provider shot xG training provenance is unknown, so it is not a leakage-free benchmark. A low immediate-threat possession may still protect a lead, rest the team or draw opponents out; this data cannot establish those tactical purposes. No causal explanation is inferred.

## Implementation stages

- Stage 1: source audit, pinned cached ingestion, deterministic possession/score baseline and six-match smoke test.
- Stage 2: tested grid xT, chronological match holdout, full Liga F validation and cross-league samples.
- Stage 3: Streamlit comparison, timeline, pitch inspection and transparent style thresholds; application tests and rendered review.
- Stage 4: reproducible chart, generated findings, dependency lock and validation/design receipts.
- Stage 5: derived browser snapshot, hash-checked static build, browser/Python parity tests and Vercel hosting guide.

Each stage can be checked independently: `tests/test_data.py`, `tests/test_events.py`, `tests/test_analysis.py`, `tests/test_xt.py`, `tests/test_real_data.py` and `tests/test_app.py`.
