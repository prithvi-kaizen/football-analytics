# Publication and hosting

## What is published

- GitHub project: [prithvi-kaizen/football-analytics/projects/tacticai-lite](https://github.com/prithvi-kaizen/football-analytics/tree/main/projects/tacticai-lite).
- Public website: [football-analytics-self.vercel.app/tacticai-lite/](https://football-analytics-self.vercel.app/tacticai-lite/).
- Authored Python/Streamlit source, tests, documentation, provider attribution and aggregate findings are committed.
- Raw events, per-corner tables, frame/player records, downloaded caches, virtual environments and local UI screenshots are ignored and excluded.

The public website is an interactive static companion: delivery and cluster comparisons with tournament/search/minimum-sample filters, exact counts and intervals, filtered aggregate CSV export, fixed model validation and time-window sensitivity. Individual corner/frame inspection and recalculation remain in the local Streamlit application. It is not labelled as a hosted Streamlit app.

## Why this deployment is static

Streamlit starts a Python server and maintains a client connection; see its [architecture documentation](https://docs.streamlit.io/develop/concepts/architecture/architecture). Vercel's [Python runtime](https://vercel.com/docs/functions/runtimes/python) documents supported Python function/framework integration rather than a conventional `streamlit run` host. This release needs neither a server adaptation nor the provider's underlying records on a public server. Static hosting supports the aggregate analytical findings directly.

Vercel serves the existing portfolio build. The root `vercel.json` runs `python3 scripts/build_website.py` and publishes `dist/`. That script restores the existing pressing dashboard and Invisible Runner, and adds TacticAI Lite at `dist/tacticai-lite/`. No environment variables, secrets, paid API or build-time dataset download is required. The Vercel project is already connected to this repository; `main` changes update the production portfolio and other branches can generate previews according to that integration's settings.

For a conventional hosted Streamlit server, [Streamlit Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud) is a separate free deployment option. That is not provisioned by this release; it would also need a deliberate data-loading and provider-terms review for its hosted inspector.

## Reproduce the analytical release

From `projects/tacticai-lite/`, with the documented Python environment active:

```bash
python -m tacticai_lite --all
python -m tacticai_lite.validate
python -m tacticai_lite.report
python -m tacticai_lite.publication
python -m pytest -q
python scripts/build_website.py
python -m http.server 4173 --bind 127.0.0.1 --directory dist
```

`publication.py` exports tournament-level counts, delivery rates, cluster summaries, model metrics and window sensitivity. It rejects a missing/failed source reconciliation or a different reviewed threshold. It never packages individual events, match records, teams, players or coordinates. `web/release.json` records SHA-256 hashes for each public asset/report, and the dependency-free builder refuses altered assets. The JSON itself states its aggregate classification.

From the repository root, `python3 scripts/build_website.py` builds the complete portfolio into `dist/`. Use a clean checkout to validate the same files that Vercel receives. Do not deploy the entire working folder with a generic upload command: generated research caches are for local use only.

## CI

`.github/workflows/tacticai-lite.yml` uses Python 3.12, installs the tested dependency lock, runs unit/publication tests, downloads the real two-match smoke sample, reruns offline and executes the tests again. It then builds the complete portfolio without analytics/network work in the website build step. No raw-data artifact is uploaded.

## Licence and scope

StatsBomb's public-data agreement and official attribution logo are retained. The data is free for the described research context, with commercial and redistribution restrictions. The project's MIT licence covers authored code, not the provider's materials. Public results remain observational and incomplete: sparse 360 coverage, confounding, per-corner Wilson assumptions and the single match-held-out split limit interpretation. The website presents those limits beside the evidence.
