# The Invisible Runner

How can we measure players who create space without touching the ball? This project detects forward off-ball runs in real SkillCorner tracking and measures nearby defenders' displacement and changes in a teammate's fixed receiving patch. It reports associations; causal credit remains an open question.

Built with Python, NumPy, pandas, SciPy, mplsoccer, Plotly and Streamlit. No API key, paid service, video download or scraping is needed.

**[Open the published analyzer](https://football-analytics-self.vercel.app/invisible-runner/)** · [Findings](outputs/1886347-full/findings.md) · [Methodology](docs/methodology.md) · [Hosting and release guide](docs/deployment.md)

The browser version includes animated replays, team/type/visibility filters, a space timeline, a run-distance comparison and filtered CSV/provenance exports. It contains three Python-calculated speed profiles: 4.5, 5.0 and 5.5 m/s, for one complete match. It runs from an integrity-checked static release on Vercel. The Streamlit app below supports additional threshold recalculation and analyzed matches.

## Findings from the validated match

Auckland FC vs Newcastle, 30 November 2024, produces 303 qualifying runs at the baseline settings and 299 valid receiving-space comparisons. Of those 299 estimates, 217 have a positive patch change, with a median of +14 m². Those situations overlap and are not independent observations.

223 of the 303 runners are detected throughout the run, but only 5 also have every contextual player and the ball detected at both endpoints. That difference limits claims about space creation. There is no human-labelled accuracy study or causal model.

![Run distance and estimated change in receiving space](outputs/1886347-full/space-change.png)

## Run the published website locally

From the repository root, only Python's standard library is required:

```sh
python3 scripts/build_website.py
python3 -m http.server 4173 --bind 127.0.0.1 --directory dist
```

Open [localhost:4173/invisible-runner](http://127.0.0.1:4173/invisible-runner/). No raw tracking download is needed for this packaged browser release. JavaScript, Web Crypto and gzip-stream support are required for interactive replay in a current browser. Plotly.js is bundled locally with its license; no CDN is used.

## Run the small MVP

Python 3.11+; the exact tested environment is Python 3.14.2 on macOS arm64. Use compatible dependency ranges below, or `requirements-lock.txt` with Python 3.14 for the recorded environment.

```sh
cd projects/invisible-runner
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m invisible_runner run --match 1886347 --seconds 300
python -m pytest -q
streamlit run app.py
```

Open [localhost:8501](http://127.0.0.1:8501). The first run downloads a bounded 3,000-frame tracking prefix plus matching event/phase files (about 10 MB total). Subsequent runs verify and reuse local source/clean caches. The app loads local analyzed outputs and never starts a hidden download. Empty/error states explain how to reproduce missing data. `Recalculate runs` changes exploratory thresholds; it does not overwrite the published report.

For a complete match, then additional explicitly selected matches:

```sh
python -m invisible_runner run --match 1886347 --full
python -m invisible_runner list-matches
python -m invisible_runner run --match 1899585 1925299 --full
```

Use `python -m invisible_runner run --help` for speed/distance options. A full match downloads roughly 100–200 MB. Each match/scope has separate outputs; all become selectable in the app. Delete an affected raw or processed cache entry to refresh it; no cache is keyed solely by a filename. Internet access is needed only for initial dependencies and uncached source downloads.

## What works

| Stage | Deliverable | Independent checks |
| --- | --- | --- |
| 1 | Pinned downloads, prefix mode, receipts, strict parser, segmented smoothing | `tests/test_data.py` |
| 2 | Configurable rule detector and geometric metrics | `tests/test_analysis.py` |
| 3 | Real-data CSVs, sensitivity, chart and report | `tests/test_e2e.py` |
| 4 | Streamlit filters, animated pitch, keyboard frame control, Plotly timeline, CSV export | `tests/test_app.py`, browser inspection |
| 5 | Portable browser release, three reviewed profiles, snapshot hashes, Vercel build | `tests/test_website.py`, browser inspection |

The baseline was implemented and tested on the small sample before the interface. It was then run end to end on Auckland FC vs Newcastle, 30 November 2024, across both halves. See the generated [complete-match findings](outputs/1886347-full/findings.md), [reproducible chart](outputs/1886347-full/space-change.png) and [portable provenance](outputs/1886347-full/provenance.json). The sample has its own [findings](outputs/1886347-sample-300s/findings.md). All numbers in those reports are generated from actual pipeline outputs. They are not league-wide player rankings.

## Sources and license

Data: [SkillCorner Open Data](https://github.com/SkillCorner/opendata), published with [PySport](https://pysport.org/), revision `4340d274572876239c154c90bc507a9b3250a656`. Retain the original [MIT license](docs/source/LICENSE) and credit SkillCorner when reusing its data or derived figures. The source README says ten 2024/25 A-League matches; its pinned index actually lists twenty. We preserve this discrepancy and scope every analysis by match ID and loaded frames. Season aggregates are available upstream but are excluded from run-level inference.

The [pre-coding source audit](docs/data-audit.md) lists confirmed fields, timing checks, license, inaccessible linked PDF specifications and limitations. [Methodology](docs/methodology.md) defines every metric, coordinate convention and exclusion. Project code is MIT licensed separately; third-party data and packages retain their own notices.

## Interpretation and validation

- Broadcast tracking includes extrapolated off-camera locations and identity errors. The app distinguishes runner visibility from context visibility and offers a strict endpoint-observation filter. Missing contextual metrics remain missing.
- Receiving space counts 1 m² cell centres in a fixed 6 m patch around a teammate's start location, at least 3 m from opponents. It omits passing lanes, reachability, offside and body orientation.
- Unknown carrier identities and estimated ball locations limit touch-free classification. Thresholds can fragment a single football action into several detected intervals.
- Centred smoothing is retrospective. Provider-label overlap checks alignment, not independent accuracy. There is no human-labelled validation set or causal model.
- No learned model is used. Future models must split by match before fitting preprocessing or tuning; do not use provider outcomes or season aggregates containing test matches as predictors.

Raw and processed tracking remain untracked in `data/raw/`. Small CSV results, charts, source notices and portable provenance are committed. Machine-specific runtime manifests are ignored and regenerated by the pipeline. `web/snapshot.json.gz` contains reviewed metrics and 2 Hz sampled replay positions; source calculations use 10 Hz tracking. Browser positions are rounded to 1 mm for display. The release omits birth dates, raw downloads, absolute workspace paths, local caches and credentials. See [validation](docs/validation.md) for the checks performed and their limits.
