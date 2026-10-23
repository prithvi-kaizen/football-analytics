# Rest Defence Analyzer

**[Open the browser release](https://football-analytics-self.vercel.app/rest-defence/)** · [Hosting guide](docs/deployment.md) · [Findings](outputs/J03WPY/findings.md)

An open-source Python pipeline and Streamlit workbench for inspecting defensive protection immediately before a team loses possession. It uses the **DFL's seven-match open tracking dataset**, released with Bassek et al. (2025). The working release includes one complete match analysis and a genuine three-minute smoke sample.

## Run the Python/Streamlit workbench

Python 3.11+ (tested locally on 3.14). From this folder:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-lock.txt
pip install --no-deps -e .
streamlit run app.py
```

The app opens the included complete-match results immediately; it needs no API key, paid service or data download. The lock captures the tested environment; `pip install -e '.[test]'` resolves compatible versions from the declared open-source dependencies instead.

## Reproduce, smallest stage first

```sh
# 1. Offline smoke test: bundled real tracking, events and metadata
python -m rest_defence --bundled
pytest -q

# 2. Fresh small download: every player + ball, ~12 MB across 23 ranges
python -m rest_defence --sample

# 3. Complete match: ~372 MB tracking, plus metadata/events
python -m rest_defence --match J03WPY
python scripts/validate_real.py

# 4. Publication chart and concise findings, regenerated from reviewed results
python -m rest_defence.report --result outputs/J03WPY
```

`--bundled` and `--sample` both cover the first 180 seconds of **available tracking**, starting at native frame 10000, slightly after kickoff. They are smoke tests, not representative match samples. The last sample transition is correctly censored. The remote sampler reconstructs valid XML from SHA-256-checked original byte ranges; it refuses servers that ignore `Range`. The source's first bytes alone contain one player and cannot supply a synchronized sample. The bundled compressed XML is ~1.8 MB; no tracking is fabricated.

All seven original match IDs are supported for full downloads: `J03WMX`, `J03WN1`, `J03WOH`, `J03WOY`, `J03WPY`, `J03WQQ`, `J03WR9`. Their exact version-1 file IDs, sizes and MD5s are pinned in [the original Figshare manifest](docs/source/figshare-v1.json). Only `J03WPY` has been fully analyzed and independently audited in this release; support for the other six is not a claim that they have been tested.

Downloads go to `data/raw/`, are checked against original MD5s, and use atomic replacement. Clean Parquet caches use tracking SHA-256, metadata SHA-256, parser version and sample stride; cache files have integrity checks. Raw full-match and clean files are ignored by Git. To force a fresh remote smoke test, remove only `data/raw/J03WPY_tracking_sample.xml`, or call `acquire(sample=True, cache=Path("another-cache"))`. The offline sample and source licence remain separate from the application's code licence.

## What is measured

The baseline detects persistent live-ball possession switches at **25 Hz**, then reconstructs the last complete **5 Hz** player snapshot strictly before the loss. The default analytical scope requires at least two seconds of prior control and the ball in the opposition half. The app can also inspect all eligible live-ball switches.

It measures outfield players behind the ball, goalkeeper cover, numerical coverage relative to forward options, RMS compactness, width/depth/hull area, central unoccupied cells, geometric passing corridors and nearest-defender distances. It follows the new possession for at most ten seconds, ending at a regain, dead ball, half end or incomplete observation. Shots prefer corrected frame references; other timestamp joins are explicitly approximate.

The fixed **0–100 vulnerability diagnostic** averages declared numerical-shortfall, spread, central-space and clear-corridor components. It is not a probability. No model is trained and no held-out performance is claimed. Any future learned model must split by complete match before fitting preprocessing or tuning. See [precise definitions and assumptions](docs/methodology.md) and [the documentation/licence review completed before coding](docs/source-review.md).

## Verified findings

In Düsseldorf–Nürnberg, the pipeline accepted **293** turnovers, including **168** eligible attacking losses with complete outcomes and defined scores. The ball advanced at least 10 m after **94/168**; **1/168** led to a shot within the bounded possession window. Düsseldorf had **62.8%** of known live-ball tracking possession.

The proposed score's rank association with subsequent ball movement was approximately **zero** (Spearman ρ = 0.000075). This is an informative failure of a simple heuristic, not evidence of predictive validity. Equal behind-ball counts also coincided with very different measured central exposure. These observations support spatial inspection; they do not establish defensive intent or causation.

[Read the generated public-post draft](outputs/J03WPY/findings.md) · [PNG chart](outputs/J03WPY/score-validation.png) · [SVG chart](outputs/J03WPY/score-validation.svg) · [Machine-readable findings](outputs/J03WPY/findings.json).

![Score validation](outputs/J03WPY/score-validation.png)

## Published website and validation

The Vercel browser companion filters the same reviewed full-match results and provides pitch overlays, recorded-frame playback, outcome charts, and CSV export. It does not run Streamlit or recalculate detection rules. Build it with only the Python standard library:

```sh
# From the repository root
python3 scripts/build_website.py
python3 -m http.server 4173 --bind 127.0.0.1 --directory dist
```

Open `/rest-defence/`. The original Streamlit workbench below remains available for local research and new match analysis. See [deployment and release refresh instructions](docs/deployment.md).

The light, pitch-led workbench has match/team/half/scope filters, a linked turnover selector, an mplsoccer pre-loss view, recorded-frame scrubbing, Plotly ball-movement and score charts, complete metric definitions, source receipts and filtered CSV export. Coordinates rotate with the losing team's direction; shapes and shirt numbers supplement colour. There is no interpolation in replays.

Tests cover XML parsing, duplicate rejection, timezone offsets, half-specific direction, coordinates, continuity, snapshot timing, persistence, restart/gap exclusion, geometry, score inputs, censoring, event/shot windows, no future-feature leakage, cached/offline real-data runs and Streamlit controls/states. A separate native-XML audit independently confirmed every published behind-ball count. The complete-match pipeline and a fresh network sample download have both been run successfully. See [validation evidence and stage history](docs/validation.md).

The website release verifies source/output hashes, an analytical-code fingerprint, compressed/decompressed snapshot hashes and authored-asset hashes. It uses native browser SVG, Web Crypto and DecompressionStream; no paid service or browser runtime dependency is required.

Outputs are separated by source scope in `outputs/<match-id>/` and `outputs/sample/`: `transitions.csv`, `snapshots.parquet`, `replays.parquet`, `timeline.parquet`, `metadata.json` and an `audit.json` with source/output hashes. The app verifies result integrity before displaying it. Report generation reads those same results. `scripts/make_sample.py` is a release utility for rebuilding the small fixture from the original full source, not a required user setup step.

## Sources, licence and limitations

Data: **Deutsche Fußball Liga (DFL)**. Bassek, M., Rein, R., Weber, H. & Memmert, D. (2025). *An integrated dataset of spatiotemporal and event data in elite soccer*. Scientific Data **12**, 195. [Paper](https://doi.org/10.1038/s41597-025-04505-y) · [Original dataset, version 1](https://doi.org/10.6084/m9.figshare.28196177.v1) · [Authors' repository](https://github.com/spoho-datascience/idsse-data).

The data are **[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)**, with DFL and publication attribution required. Extracts are time-subsetted, coordinates rotated and metrics derived. See [data attribution](data/sample/NOTICE.md). Original project code is MIT-licensed; dependencies retain their own open-source licences.

Seven selected 2022/23 matches, five involving the same club, cannot support league-wide claims. This release's findings concern one match. Optical tracking error, manually annotated event timing, contested possession, excluded non-11v11 snapshots, fixed geometric thresholds and sparse shots limit interpretation. Straight corridors omit speed, orientation, pressure, offside and aerial trajectories. Ball advancement can include passes in flight. No video-labelled tactical ground truth or independent validation of the score is supplied.
