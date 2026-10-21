# Football analytics

Football projects built around specific tactical questions, reproducible data processing and interactive analysis.

**Live projects:** [Pressing trap detector](https://football-analytics-self.vercel.app) · [The Invisible Runner](https://football-analytics-self.vercel.app/invisible-runner/)

## Projects

| Project | Football question | Data | Status |
| --- | --- | --- | --- |
| [Pressing trap detector](projects/pressing-trap-detector/) | Where does Spain actually win the ball, and which opposition passing patterns precede pressure? | StatsBomb Open Data, Euro 2024, all 51 matches | Working dashboard and reproducible analysis |
| [The Invisible Runner](projects/invisible-runner/) | How can we measure players who create space without touching the ball? | SkillCorner open A-League 2024/25 tracking; one complete match validated | Python pipeline, Streamlit app and published browser replay |

The first project includes pressure and recovery maps, event-level replays, team comparisons, an exploratory xT model, automated tests and a written investigation. It identifies patterns consistent with pressing traps; event data alone cannot prove intent.

The Invisible Runner includes trajectory cleaning, configurable run detection, defender displacement, receiving-space estimates, three published detection profiles and animated pitch replays. Its [findings](projects/invisible-runner/outputs/1886347-full/findings.md) distinguish fully detected runners from extrapolated contextual tracking. Space changes are associations, not causal player credit.

## Run the website

Requires Python 3.10 or newer. No third-party Python packages are required.

```sh
git clone https://github.com/prithvi-kaizen/football-analytics.git
cd football-analytics
python3 scripts/build_website.py
python3 -m http.server 4173 --bind 127.0.0.1 --directory dist
```

Open [Pressing trap detector](http://127.0.0.1:4173/) or [The Invisible Runner](http://127.0.0.1:4173/invisible-runner/). The build verifies and restores both published releases without downloading raw data or installing analytics dependencies. Keep the server running while using the websites.

## Reproduce the analysis

See the [project README](projects/pressing-trap-detector/README.md) for the download, extraction and test commands; the [methodology](projects/pressing-trap-detector/docs/methodology.md) defines the coordinate frame, recovery rule and denominators. The [article](projects/pressing-trap-detector/docs/where-does-spain-win-the-ball.md) reports findings under fixed five-second and ten-second definitions.

For tracking analysis, use the [Invisible Runner setup](projects/invisible-runner/README.md). It supports a small download for a smoke test and additional explicit match IDs. The full Python/Streamlit app recalculates thresholds; the published browser version uses reviewed profiles at 4.5, 5.0 and 5.5 m/s. No paid API or account is required to run either project locally.

## Deployment

The websites are deployed at [football-analytics-self.vercel.app](https://football-analytics-self.vercel.app) through the repository's Vercel GitHub integration. Pushes to `main` update production; other branches create previews. The root `vercel.json` runs `python3 scripts/build_website.py` and serves `dist/`: the existing pressing dashboard at `/`, and the run analyzer at `/invisible-runner/`. No environment variables or server functions are required. See the [Invisible Runner hosting guide](projects/invisible-runner/docs/deployment.md) and [pressing release guide](projects/pressing-trap-detector/docs/deployment.md).

## Repository conventions

Each project lives in `projects/<project-name>/` with its own README, methods, scripts and tests. Large raw downloads and generated analysis intermediates are excluded from Git. Source revisions and file hashes are retained for reproducibility. The committed website release contains its complete reviewed snapshot, stored losslessly in a compressed archive.

Data sources keep their original terms. The first project's data is supplied by [StatsBomb Open Data](https://github.com/hudl/open-data); its licence and attribution are included in that project. Third-party runtime code in the compiled dashboard is not claimed as original project code or relicensed by this repository.

The Invisible Runner uses [SkillCorner Open Data](https://github.com/SkillCorner/opendata), published with PySport under its supplied MIT notice. The source revision, field audit, license, methods and output hashes are retained in the project. Raw tracking and machine-local caches are excluded from Git; the published replay snapshot contains only the fields needed by the browser.
