# Hosting and release guide

Repository: [prithvi-kaizen/football-analytics](https://github.com/prithvi-kaizen/football-analytics), folder `projects/rest-defence-analyzer`.

Browser route: [football-analytics-self.vercel.app/rest-defence/](https://football-analytics-self.vercel.app/rest-defence/).

## What is published

The browser companion serves the same 293 reviewed turnovers, pre-loss metrics, source receipts and recorded player positions as the complete-match Streamlit workbench. Team, half, attacking-loss and event-corroboration filters, pitch overlays, recorded-frame playback, score/ball-movement charts and CSV export run locally in the browser. It does not rerun the Python detector or fit a model.

The package contains a roughly 1.5 MB losslessly compressed snapshot, three authored HTML/CSS/JavaScript files, and report/source downloads. It has no browser library dependency, remote API, paid data source, account requirement or server-side computation. Hosting remains subject to the existing Vercel account's applicable limits and terms; no plan upgrade or new paid service is configured.

The Streamlit application remains the local analytical workbench. This deployment uses static hosting rather than trying to run that persistent Python application as a function.

## Clean-clone build

From the repository root, Python 3.10+ and the standard library are sufficient:

```sh
python3 scripts/build_website.py
python3 -m http.server 4173 --bind 127.0.0.1 --directory dist
```

Open `/rest-defence/` on that server. The existing pressing and Invisible Runner routes remain in the root build. The per-project builder also accepts `--output PATH`.

The build verifies every HTML/CSS/JS asset, the compressed archive, and its decompressed SHA-256 before copying. The browser independently verifies decompressed content before rendering. Serve over HTTPS or localhost HTTP: Web Crypto and gzip DecompressionStream are required. Opening `index.html` directly through `file://` is not supported. A failed load displays a recoverable error message.

## Existing Vercel project

Keep repository-root settings:

| Setting | Value |
|---|---|
| Framework | Other / none |
| Root directory | Repository root |
| Install command | Empty |
| Build command | `python3 scripts/build_website.py` |
| Output directory | `dist` |
| Environment variables | None |
| Production branch | `main` |

The repository's existing GitHub integration deploys pushes to main. Root `vercel.json` preserves canonical directory URLs and adds immutable caching only for the content-hashed snapshot path. No Vercel credentials are committed. A separate CLI preview can be deployed from the built directory, but it is not needed for the repository integration.

## Refresh the public snapshot

Install the analytics dependencies and reproduce the full source match before packaging:

```sh
cd projects/rest-defence-analyzer
python -m rest_defence --match J03WPY
python scripts/validate_real.py
python -m rest_defence.report --result outputs/J03WPY
python scripts/package_website.py
python scripts/build_website.py
pytest -q
```

Commit authored assets, `web/bundle.json`, `web/snapshot.json.gz`, reviewed results and attribution together. Packaging refuses changed analytical sources or result checksums: the full-match audit records a SHA-256 fingerprint of parsing, detection, geometry and pipeline code. Build verification intentionally rejects modified assets that have not been repackaged.

Native 25 Hz timeline anchors and 5 Hz player replays are preserved. Timeline maxima are checked against the published progression metric for every transition. No interpolation or synthetic player locations are generated. Raw full XML, clean caches, local environments and duplicate network-smoke outputs remain ignored by Git.

The static snapshot contains public player identifiers, short names and shirt numbers from the CC BY 4.0 data. No tokens, local home paths, player birth dates or video are included. Original code is MIT; source and derived data retain CC BY 4.0 with DFL/publication attribution.
