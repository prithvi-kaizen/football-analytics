# TacticAI Lite

A reproducible corner-kick intelligence workbench inspired by [TacticAI](https://doi.org/10.1038/s41467-024-45965-x). Built with public StatsBomb events and partial 360 snapshots, Python, Streamlit, mplsoccer and Plotly. It extracts corner sequences, compares deliveries, clusters visible configurations and evaluates a simple match-separated baseline.

**[Open the published aggregate explorer](https://football-analytics-self.vercel.app/tacticai-lite/)** · [Findings](reports/findings.md) · [Research chart](reports/corner-shot-creation.png)

The Vercel website provides interactive aggregate comparisons and downloads. The local Streamlit app adds individual corner inspection, linked player frames and event sequences after downloading directly from the provider. The public website does not distribute those underlying records.

## Quick start

Python 3.11+ (tested on 3.12). No API keys or paid services.

```bash
cd projects/tacticai-lite
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-lock.txt
python -m pip install --no-deps -e .
python -m tacticai_lite --sample 1
python -m pytest -q
streamlit run app.py
```

The smoke sample selects the earliest match from each tournament: **2 matches, 16 corners, 11 linked frames**. The classifier refuses to fit such a small sample.

For the complete analysis:

```bash
python -m tacticai_lite --all          # 82 matches, about 813 MB raw JSON
python -m tacticai_lite.validate       # independent real-source audit and sensitivity
python -m tacticai_lite.report        # public chart, aggregate table and findings
python -m pytest -q
streamlit run app.py
```

Downloads are cached with SHA-256 receipts at a pinned source revision. `--offline` forbids network requests. `--sample N` selects N chronological matches per tournament. `--tournament euro2024` or `weuro2025` restricts scope. `--horizon 10 --output outputs/window10` builds a variant. Set `TACTICAI_OUTPUT` to an absolute output folder to inspect it in the app. Launch Streamlit from this project directory to load its light theme.

## Data and terms

[StatsBomb Open Data](https://github.com/statsbomb/open-data), revision `4b73468fc5b0f1950f9f66fada70ad3a4f9327cb`: Men’s Euro 2024 (55/282, 51 matches) and Women’s Euro 2025 (53/315, 31 matches). Direct official JSON downloads only. Read the [pre-code audit](docs/DATA_AUDIT.md), [specifications](docs/source/README.md) and [original agreement](docs/source/LICENSE.pdf).

**The data is freely accessible for research, but not unrestricted open-source data.** StatsBomb’s agreement restricts commercial exploitation and redistribution, and requires source/logo attribution for publications. The provider asks users to register interest through its resource centre. Raw data, individual events, frames and per-corner artifacts stay in ignored `data/` and `outputs/`; do not bundle them for public distribution. Authored code is MIT; provider materials retain their terms.

![StatsBomb](assets/SB%20-%20Icon%20Lockup%20-%20Colour%20positive.png)

## Method

- **Shot creation:** an attacking-team shot within 15 seconds, inclusive, in the same period and possession, before a restart or stoppage. Multiple shots count once; incomplete recordings remain unknown. Period-relative millisecond clocks handle half-time and extra time. Directly shot corners are inspectable but excluded from comparisons/prediction because their target is automatically positive.
- **Delivery:** recorded inswinging/outswinging/straight technique; short means pass length ≤15 standardized units. Unknown technique remains unknown. These are observed-delivery descriptions, excluded from the frame-only predictor.
- **Spatial analysis:** normalize width in 120×80 coordinates; count visible players, centroids, spread and nearest-defender distances. Defensive density uses the visible polygon’s intersection with the penalty area. Missing players/frames are not zero density.
- **Clustering/model:** outcome-free k-means and configuration search; logistic regression versus a constant-rate baseline. Whole-match 70/30 split, seed 2026; preprocessing fits training data only. See [implementation details](docs/IMPLEMENTATION.md).

## Findings and validation

The full run contains **817 corners, 485 linked frames and 484 usable configurations**. Outswinging deliveries had higher observed shot rates than inswinging deliveries in both tournaments, under this definition. That association does not establish tactical causation. Logistic regression did **not** beat the constant baseline on held-out Brier score (0.2204 versus 0.2191).

[Findings report](reports/findings.md) · [Reproducible chart](reports/corner-shot-creation.png) · [Aggregate rates](reports/delivery_summary.csv) · [Window sensitivity](reports/window_sensitivity.csv) · [Validation receipt](reports/validation.json)

**46 tests pass**, including parsing, coordinates, timing, calculations, cache integrity, leakage invariants, real-data end-to-end replay, pitch-render coordinates, Streamlit control/export/error-state tests and publication checks. Independent reconstruction checked all 817 labels and shot counts with zero mismatches. See [QA evidence](docs/QA.md). Real-data tests explicitly skip until data is downloaded. GitHub Actions runs the unit tests, a real two-match download, verified offline replay and the portfolio website build.

## Public website and Vercel

The website is a static, aggregate-only release at `/tacticai-lite/` within the existing portfolio. It requires no account, Python server or paid API for visitors. Build it from this project directory with `python3 scripts/build_website.py`, then serve `dist/` with any static server. From the repository root, `python3 scripts/build_website.py` builds all published projects together, preserving the existing sites.

To update the public findings, reproduce the full analysis, run `python -m tacticai_lite.validate`, `python -m tacticai_lite.report`, then `python -m tacticai_lite.publication`. Commit the reviewed `web/` release and reports. The offline builder checks release hashes and never downloads provider data. The repository's existing Vercel Git integration builds changes pushed to `main`; see the [deployment guide](docs/deployment.md).

## Limits and scope

360 is partial broadcast snapshots, not tracking. It cannot recover runs, player identities, marking assignments or intent. Visibility selection, small categories, tournament mix and threshold choices affect results. Wilson intervals assume independent corners; a single model split has substantial uncertainty. Team overlap across different matches remains possible.

This is inspired by TacticAI, not a reproduction of its proprietary model. The GNN stretch experiment is deferred; the validated baseline and limited frame sample come first.

Citation: Wang et al. (2024), *TacticAI: an AI assistant for football tactics*, Nature Communications 15, 1906. [DOI](https://doi.org/10.1038/s41467-024-45965-x).
