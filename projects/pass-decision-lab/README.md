# Pass Decision Lab

Explore a historical possession, the pass actually played, and anonymous teammates visible in the corresponding StatsBomb 360 frame. A fixed logistic model supplies experimental candidate estimates; boosted trees provide an independent model comparison. No account, paid API or scraped data is required.

The project answers **“Can AI identify missed progressive passes?”** with a review tool, not a claim to know the right tactical choice. Alternative passes have no observed outcomes. See [findings](outputs/findings.md), the [reproducible chart](outputs/calibration.png), and the [pre-coding source audit](docs/data-audit.md).

## Published website

[Open Pass Decision Lab](https://football-analytics-self.vercel.app/pass-decision-lab/).

The Vercel companion contains 12 reproducibly selected held-out case studies, candidate selection, attributed pitch diagrams, aggregate model evidence and downloadable findings. The full Streamlit app below explores all locally downloaded matches. The public companion shares analytical figures and derived estimates rather than raw 360 snapshots or training tables. See [hosting and release instructions](docs/deployment.md).

## Run locally

Python 3.11+; the committed lock file records the exact Python 3.14 environment used for this run.

```sh
cd projects/pass-decision-lab
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'

# Stage 1: four real matches, logistic baseline, small download (~35 MB).
python -m passlab.pipeline --sample 2 --models baseline --output outputs/smoke
PASSLAB_OUTPUT=outputs/smoke streamlit run app.py

# Stage 2: all 82 matches, logistic + fixed gradient boosted trees.
python -m passlab.pipeline --full --models all
streamlit run app.py
```

`--sample N` selects the earliest N matches **per tournament**, with at least two per tournament needed for a match-separated split. The four-match smoke run deliberately omits target models when the recipient-proxy sample is too small. The full run caches roughly 800 MB of public JSON; allow additional space for local intermediate tables. Ingestion processes four matches at a time.

```sh
# Verified-cache-only reproduction; no network calls.
python -m passlab.pipeline --full --models all --offline

# Unit tests, then complete real-data checks (no network in pytest).
pytest -q -m 'not integration'
pytest -q
ruff check passlab tests app.py
```

Real-data integration tests skip explicitly until outputs exist. To run them against only the smoke output:

```sh
PASSLAB_TEST_OUTPUT=outputs/smoke pytest -q
```

To reproduce the recorded dependency environment, install `requirements-lock.txt` after creating a Python 3.14 environment, then `pip install --no-deps -e .`. The normal editable install resolves compatible releases on other supported Python versions. A package upgrade can change fitted results; compare the recorded versions and artifact hashes. In restricted environments set `MPLCONFIGDIR` to a writable local directory.

## Evidence and definitions

**Sources.** [StatsBomb Open Data](https://github.com/hudl/open-data) at revision `4b73468fc5b0f1950f9f66fada70ad3a4f9327cb`: UEFA Euro 2024 (55/282, 51 matches), Women's Euro 2025 (53/315, 31). Events v4.0.0 and 360 v1.0.0 specifications were read before coding. Files are cached with source URLs and SHA-256 receipts; corruption fails explicitly. Event `id` joins to frame `event_uuid`; duplicates fail rather than multiplying observations.

**Population.** Untyped ground passes with either foot in periods 1–4. Missing outcome means complete; known unsuccessful outcomes mean incomplete; Unknown is excluded. This is a deliberately restricted MVP, excluding aerial passes, named set-piece/recovery/interception types and shootouts. Counts and exclusions appear in local `audit.json`.

**Geometry.** Already actor-oriented 120 × 80 normalized StatsBomb coordinates, never flipped again at halftime. Euclidean distance, sine/cosine of target direction, x gain, nearest passer/target opponent, Gaussian proximity (sigma 5), minimum distance to the *interior* passing segment and count within 3 units. These coordinates are not surveyed metres. Finite off-pitch frame players remain in defender geometry and are audited separately; off-pitch targets receive no probability. Event timing uses period-relative timestamps and event indices; nominal match clocks are for display, not ordering across stoppage time.

**Leakage control.** Recorded endpoints, provider length/angle, outcomes, duration, future receipts, player and match IDs do not enter prediction features. The pressure tag is display-only because collection can overlap event duration. Actual endpoint displacement and its solid arrow are descriptive only.

**Two distinct experiments.**

1. **Context:** event origin + period, versus those features plus 360 origin pressure and visible-player counts. These use exactly the same framed passes with observed defenders. They do not distinguish recipients. The event-only baseline is intentionally narrow, not Hudl's full target-aware baseline.
2. **Target proxy:** the pass's annotated intended recipient must have an earlier same-team actor location within 5 seconds. Match it to the nearest current teammate only within 3 units and with a 2-unit nearest-neighbor margin. This uses no endpoint or future event. Geometry-only and geometry-plus-spatial models use the same restricted cohort. Geometry comes from 360/history, so geometry-only is **not** a pure event-only model. Identity remains unverified and recently involved players are overrepresented.

**Validation.** Fixed seed 2026, 25% of entire matches per tournament held out (61 train, 21 test in the full run). Fit imputation and scaling on training only. Logistic regression C=1 precedes fixed histogram gradient boosting (100 iterations, 7 leaves, learning rate .05, L2=2); random-row early stopping is disabled. Hyperparameters, probability guards and review thresholds are not tuned on test results. The app always uses the training-only logistic models, including when inspecting training matches, which are labeled in-sample. Scores include log loss, Brier, AUC, calibration counts, per-tournament breakdowns and conditional 95% match-cluster bootstrap intervals for log loss. These intervals do not include model-retraining uncertainty.

**Candidates.** Every valid visible non-actor teammate is a hypothetical stationary ground-pass target with a frame-local anonymous label. Withhold probability if any required feature is missing, outside its training 1st–99th percentile, or target visibility is unknown/outside. Marginal guards do not establish joint support or causal validity. Missing/off-camera defenders are never treated as proof of an open lane.

**Territorial proxy.** Forward gain = target x minus origin x. Expected positive gain = xPass × max(gain, 0), with zero on failure and no turnover penalty. It is not xT, goal value, line-breaking credit or tactical quality. A review flag needs a supported inferred chosen target and another supported target ≥10 units forward, probability ≥0.70, and ≥5 more expected positive units. These fixed exploratory cutoffs only create a video-review queue.

## Findings and limits

The full pinned run contains 54,200 eligible passes. On 13,082 held-out context observations, logistic log loss changes from 0.2232 (origin + period) to 0.2022 (with 360 context). The target proxy retains only 2,122 passes, so target-model evaluation and candidate suggestions require particular caution. Exact metrics, coverage, selection rates and the experimental review count are generated in [the findings report](outputs/findings.md).

360 omits off-camera players, sometimes lacks camera polygons or actor flags, and contains no persistent teammate identities, velocities, body orientation or verified offside state. Target annotation, inferred anonymous identity, selection bias and unobserved alternatives prevent a claim that a flagged lane was available or better. No player rankings or invented tactical explanations are provided.

## Build the website

From the repository root, run `python3 scripts/build_website.py` and serve `dist/` with any static server. This needs only the Python standard library and restores the hash-verified committed release; no source downloads or analytics dependencies are needed. To regenerate its 12 cases from a validated local run, use `python scripts/package_website.py` from this project folder after installing the Python dependencies.

## Outputs and stages

- `passlab/data.py`, `features.py`, `geometry.py`: pinned caching, parsing and testable spatial baseline.
- `models.py`: prespecified models, tournament-stratified match splits, metrics and transparent JSON logistic inference; no untrusted pickle loading.
- `choices.py`: candidate geometry, training-range guards and held-out review queue.
- `app.py`, `viz.py`: Streamlit possession explorer, mplsoccer pitch and Plotly calibration.
- `outputs/findings.md`, `calibration.png/.svg/.csv`, `metrics.csv`, `run-summary.json`: shareable aggregate research outputs.
- Local-only outputs: pass tables, snapshots, model coefficients, source receipts, parsing audits, per-tournament scores, review queue, and full `provenance.json` with source and artifact hashes.
- [Validation record](outputs/validation.md): completed tests and UI checks.

First run the small baseline; then enable tree comparisons and the full cohort. Each layer has separate tests. Data and row-level derived outputs are ignored by Git; another researcher downloads source files from StatsBomb rather than receiving a bundled dataset.

## Terms and citations

[StatsBomb Public Data User Agreement](docs/source/LICENSE.pdf), dated 8 September 2023, permits this research use and sharing attributed analysis but restricts commercial exploitation and raw data redistribution. It is not an OSI open-source data license. Read the agreement before reuse. The project code is MIT; data, source documentation and branding retain upstream terms. All Python dependencies are open source; [dependency license metadata](outputs/dependency-licenses.json) and the lock file record the tested environment.

Conceptual reference: Conor Sharpe, [xPass 360: Upgrading Expected Pass Models](https://www.hudl.com/blog/xpass-360-upgrading-expected-pass-xpass-models), Hudl, 17 June 2025. This implementation does not reproduce Hudl's proprietary target-imputation model or its reported benchmarks.

![Data supplied by StatsBomb](assets/statsbomb-logo.png)
