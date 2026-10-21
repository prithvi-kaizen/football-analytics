# Hosting and release guide

Published route: [football-analytics-self.vercel.app/invisible-runner/](https://football-analytics-self.vercel.app/invisible-runner/). Repository: [prithvi-kaizen/football-analytics](https://github.com/prithvi-kaizen/football-analytics), project folder `projects/invisible-runner`.

## What is hosted

Vercel serves a browser application built from the reviewed full-match analysis. Replays, filters, charts and CSV/provenance exports run in the browser. Three detection profiles are calculated in Python at 4.5, 5.0 and 5.5 m/s before publication. The minimum-distance filter selects qualifying runs from the chosen profile; it does not rerun tracking analysis in JavaScript.

The Python/Streamlit workbench remains the analytical application for recalculation and new matches. The static website uses a portable snapshot so hosting needs no Python server, raw-data download, fitted model, credentials or paid API. It does not claim to run Streamlit inside a Vercel Function.

## Build from a clean clone

```sh
git clone https://github.com/prithvi-kaizen/football-analytics.git
cd football-analytics
python3 scripts/build_website.py
python3 -m http.server 4173 --bind 127.0.0.1 --directory dist
```

Open `/invisible-runner/` on that local server. The root route continues to serve the pressing-trap dashboard. The build uses only the Python standard library and checks compressed/decompressed snapshot hashes and every authored asset/vendor-library hash before copying the release.

## Vercel configuration

The existing `football-analytics` Vercel project is connected to this repository. Keep the repository root as the Root Directory.

| Setting | Value |
| --- | --- |
| Framework | Other / none |
| Install command | Empty |
| Build command | `python3 scripts/build_website.py` |
| Output directory | `dist` |
| Environment variables | None |
| Production branch | `main` |

The root `vercel.json` supplies the build/output settings and canonical trailing-slash directory URLs, so relative assets resolve correctly under `/invisible-runner/`. A push to a development branch creates a preview through the existing Vercel Git integration; a push to `main` publishes production. No new paid service is needed. Deployment is still subject to the account's applicable hosting limits and terms.

If automatic GitHub deployments are delayed, use the existing project's Deployments page and **Create Deployment**, selecting the reviewed branch or commit. Confirm the source commit and Ready status before sharing the new release; do not redeploy an older production commit by mistake.

Configuration references: [Vercel build configuration](https://vercel.com/docs/builds/configure-a-build), [project settings](https://vercel.com/docs/project-configuration/vercel-json). If a persistent hosted Streamlit server is desired later, [Streamlit Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud) is a separate option; it is not part of this deployment.

## Refresh the reviewed release

Reproduce the full-match analysis first, with the analytics dependencies installed:

```sh
cd projects/invisible-runner
source .venv/bin/activate
python -m invisible_runner run --match 1886347 --full
python scripts/package_website.py
python -m pytest -q
```

Then build the repository website from its root, review the local browser version, and commit the updated authored source, `web/bundle.json`, `web/snapshot.json.gz`, results and licenses together. A source asset changed without repackaging intentionally fails its integrity check. Raw data and processed caches remain excluded from Git.

`package_website.py` refuses an analytical code fingerprint or baseline CSV checksum that differs from its full-match manifest. It regenerates all three profiles from real cleaned tracking, checks every valid replay's start/end patch values against its run metrics, strips unnecessary player fields and stores deterministic gzip bytes. The browser validates the decompressed snapshot SHA-256 before rendering.

## License and public scope

SkillCorner's supplied MIT notice is retained in `docs/source/LICENSE` and copied into the website. Plotly.js is bundled under its supplied MIT license in `web/vendor/`. Project code has its own `LICENSE`. No account tokens, raw video, full tracking dump, local file paths or personal player birth dates are published in the replay snapshot. All displayed player identifiers and names originate in the public source dataset.
