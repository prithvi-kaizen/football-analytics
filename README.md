# Football analytics

Football projects built around specific tactical questions, reproducible data processing and interactive analysis.

**Live dashboard:** [Pressing trap detector](https://football-analytics-self.vercel.app) · [Project](projects/pressing-trap-detector/) · [Analysis](projects/pressing-trap-detector/docs/where-does-spain-win-the-ball.md)

## Projects

| Project | Football question | Data | Status |
| --- | --- | --- | --- |
| [Pressing trap detector](projects/pressing-trap-detector/) | Where does Spain actually win the ball, and which opposition passing patterns precede pressure? | StatsBomb Open Data, Euro 2024, all 51 matches | Working dashboard and reproducible analysis |

The first project includes pressure and recovery maps, event-level replays, team comparisons, an exploratory xT model, automated tests and a written investigation. It identifies patterns consistent with pressing traps; event data alone cannot prove intent.


## Run the website

Requires Python 3.10 or newer. No third-party Python packages are required.

```sh
git clone https://github.com/prithvi-kaizen/football-analytics.git
cd football-analytics
python3 projects/pressing-trap-detector/scripts/build_website.py
python3 -m http.server 4173 --bind 127.0.0.1 --directory projects/pressing-trap-detector/dist
```

Open [http://127.0.0.1:4173](http://127.0.0.1:4173). The build verifies and restores the complete reviewed snapshot; it does not download the raw event dataset. Keep the server running while using the dashboard.

## Reproduce the analysis

See the [project README](projects/pressing-trap-detector/README.md) for the download, extraction and test commands; the [methodology](projects/pressing-trap-detector/docs/methodology.md) defines the coordinate frame, recovery rule and denominators. The [article](projects/pressing-trap-detector/docs/where-does-spain-win-the-ball.md) reports findings under fixed five-second and ten-second definitions.

## Deployment

The website is deployed at [football-analytics-self.vercel.app](https://football-analytics-self.vercel.app) through the repository's Vercel GitHub integration. Pushes to `main` update the production website; other branches create preview deployments. The root `vercel.json` builds and serves the first project's static website. See the [Vercel deployment guide](projects/pressing-trap-detector/docs/deployment.md) for settings and how to refresh the packaged release. No environment variables are required.

## Repository conventions

Each project lives in `projects/<project-name>/` with its own README, methods, scripts and tests. Large raw downloads and generated analysis intermediates are excluded from Git. Source revisions and file hashes are retained for reproducibility. The committed website release contains its complete reviewed snapshot, stored losslessly in a compressed archive.

Data sources keep their original terms. The first project's data is supplied by [StatsBomb Open Data](https://github.com/hudl/open-data); its licence and attribution are included in that project. Third-party runtime code in the compiled dashboard is not claimed as original project code or relicensed by this repository.
