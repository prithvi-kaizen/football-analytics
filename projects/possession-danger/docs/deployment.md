# GitHub and Vercel release

Repository: [prithvi-kaizen/football-analytics](https://github.com/prithvi-kaizen/football-analytics). Project directory: `projects/possession-danger/`.

Website route: `/possession-danger/` on the existing Football Analytics Vercel project. The Python/Streamlit workbench remains available locally; Vercel serves a static browser companion with reviewed analytical results. The hosting build installs no analytics packages, trains no model, downloads no source matches, and needs no account keys.

## What is published

The public snapshot contains derived team-match measures, score-state summaries, analytical possession summaries, a fitted xT surface and fixture context. It includes the full 240-match Liga F season and a clearly labelled six-match sample from each of the five leagues. Held-out matches are the default. A training/all-match switch is explicitly descriptive; the fitted xT surface never changes when a view filter changes.

The browser provides possession-versus-threat/territory plots, weighted per-possession comparisons, score-state rates and exposures, match timelines, long quiet possessions, threshold-based styles, possession summaries, source explanations and downloads. It does not refit xT or provide event-coordinate pitch replays. Those are available through the Python/Streamlit workbench after an explicit source download.

Raw event JSON, cleaned event/action CSVs, player records and event coordinates are excluded from Git and the hosted snapshot. The provider licence, credit and original StatsBomb logo accompany the research. Derived research publication does not remove StatsBomb's restrictions on commercial exploitation or raw-data redistribution. Code and vendored Plotly retain their separate notices.

## Build from a fresh clone

```sh
git clone https://github.com/prithvi-kaizen/football-analytics.git
cd football-analytics
python3 scripts/build_website.py
python3 -m http.server 4173 --bind 127.0.0.1 --directory dist
```

Open `http://127.0.0.1:4173/possession-danger/`. Existing routes at `/` and `/invisible-runner/` remain available. Python 3.10+ and its standard library are sufficient for this build. The checked-in `web/snapshot.json.gz` supplies the reviewed results; no local caches or ignored CSVs are required.

The build verifies the compressed snapshot, its decompressed content, source asset hashes, download hashes and safe paths before publishing files. The browser verifies the decompressed snapshot hash again. A modern browser with `DecompressionStream` support is required; the report and charts are also downloadable independently.

## Vercel settings

Keep the existing repository-root deployment configuration:

| Setting | Value |
| --- | --- |
| Root directory | Repository root |
| Framework | Other / none |
| Install command | Empty |
| Build command | `python3 scripts/build_website.py` |
| Output directory | `dist` |
| Environment variables | None |
| Production branch | `main` |

The root `vercel.json` preserves trailing-slash URLs and immutable caching for hashed snapshot assets. The existing GitHub integration deploys pushes automatically. A branch push can be reviewed as a preview; a `main` push updates the configured production site. Confirm the source commit and deployment's Ready status in Vercel before presenting a new deployment as live. Hosting remains subject to the account's applicable free-plan limits and terms.

References: [Vercel project configuration](https://vercel.com/docs/project-configuration), [build configuration](https://vercel.com/docs/builds/configure-a-build), and [Streamlit Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud) if a persistent hosted Streamlit workbench is wanted separately.

## Refresh the analysis and browser release

```sh
cd projects/possession-danger
source .venv/bin/activate
python -m possession_danger.cli download --full
python -m possession_danger.cli run --full --offline --output outputs/liga-f
python -m possession_danger.cli download --league all --sample 6
python -m possession_danger.cli run --league all --sample 6 --offline --output outputs/all-leagues-sample
python scripts/package_website.py
python -m pytest -q
```

`package_website.py` refuses modified analytical source fingerprints or analytical output checksums. It selects the public fields explicitly, includes the original provider attribution, serializes the derived snapshot deterministically, and records hashes in `web/bundle.json`. It uses the repository's existing MIT-licensed Plotly runtime. Commit the source, tested release bundle, reports, charts and notices together. Do not commit raw caches, row-level local CSVs, virtual environments or credentials.

The `Possession danger` GitHub Actions workflow checks a fresh-clone build and unit/browser-metric parity tests, downloads the real six-match sample, reproduces the pipeline offline and runs the available real-data tests. Full-season local validation is documented separately; CI does not imply a fresh download of every league season.
