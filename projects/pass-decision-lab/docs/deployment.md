# Hosting the project

Public companion: https://football-analytics-self.vercel.app/pass-decision-lab/

The repository's existing Vercel project runs `python3 scripts/build_website.py` and serves `dist/`. This project adds `/pass-decision-lab/` while preserving existing project routes. No runtime Python process, paid API, environment variable or browser dependency download is needed for this companion.

## Two interfaces

- **Local Streamlit app:** all downloaded matches, historical possessions, candidate calculations and model evidence. Run the Python pipeline and `streamlit run app.py` as described in the project README.
- **Public static companion:** 12 attributed analytical case studies, selectable anonymous targets, derived candidate estimates, all aggregate model scores and the report. It publishes no raw event/360 coordinate JSON or training tables. The cases are the first chronological flagged event in each of the earliest six distinct held-out matches per tournament. They are not representative and cannot validate counterfactual pass quality.

Streamlit expects a running Python server with persistent session state. Vercel's native Python Functions use request-oriented WSGI/ASGI entry points; deploying a Streamlit process there is not this project's supported deployment path. See the [Streamlit architecture](https://docs.streamlit.io/develop/concepts/architecture/architecture) and [Vercel Python runtime](https://vercel.com/docs/functions/runtimes/python) documentation. Native WebSocket support alone does not supply the expected server lifecycle.

## Build from a fresh clone

```sh
# From the repository root; only the Python standard library is required.
python3 scripts/build_website.py
python3 -m http.server 4173 --bind 127.0.0.1 --directory dist
```

Open http://127.0.0.1:4173/pass-decision-lab/ . The build verifies every committed asset against `web/bundle.json` and copies the reviewed release. It does not download StatsBomb data, train models or import analytics dependencies.

## Regenerate the publication

```sh
cd projects/pass-decision-lab
source .venv/bin/activate
python -m passlab.pipeline --full --models all --offline
python scripts/package_website.py
python scripts/build_website.py
pytest -q
```

`package_website.py` checks the saved run's hashes and held-out membership before generating case figures and `analysis.json`. The public JSON contains only case citations, derived measurements and aggregate model evidence. The figures carry StatsBomb attribution. No data license is replaced by the project's MIT code license.

After changing authored HTML/CSS/JS, run the packager again to update the release manifest. Do not manually change hashes to bless an unreviewed data release. Case figures are PNG analysis outputs, not browser-readable raw coordinates.

## Deploy

The existing GitHub integration deploys pushes to `main` to the portfolio URL above; other branches receive preview deployments. Vercel uses the root `vercel.json`, with no additional project setup. The project folder can also be built independently with `python scripts/build_website.py --output /path/to/static-output` and that output hosted by any static host.

The CLI may require a separate Vercel login. GitHub publication and the existing Git-connected deployment do not require storing a Vercel token in this repository. Do not deploy the analytics working directory: it contains local raw caches that are intentionally ignored by Git.
