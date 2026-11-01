# Football analytics

Football projects built around specific tactical questions, reproducible data processing and interactive analysis.

**Live projects:** [Pressing trap detector](https://football-analytics-self.vercel.app) · [The Invisible Runner](https://football-analytics-self.vercel.app/invisible-runner/) · [Rest Defence Analyzer](https://football-analytics-self.vercel.app/rest-defence/) · [Pass Decision Lab](https://football-analytics-self.vercel.app/pass-decision-lab/) · [Possession danger](https://football-analytics-self.vercel.app/possession-danger/) · [TacticAI Lite](https://football-analytics-self.vercel.app/tacticai-lite/) · [Possession Lab](https://football-analytics-self.vercel.app/possession-lab/)

## Projects

| Project | Football question | Data | Status |
| --- | --- | --- | --- |
| [Pressing trap detector](projects/pressing-trap-detector/) | Where does Spain actually win the ball, and which opposition passing patterns precede pressure? | StatsBomb Open Data, Euro 2024, all 51 matches | Working dashboard and reproducible analysis |
| [The Invisible Runner](projects/invisible-runner/) | How can we measure players who create space without touching the ball? | SkillCorner open A-League 2024/25 tracking; one complete match validated | Python pipeline, Streamlit app and published browser replay |
| [Pass Decision Lab](projects/pass-decision-lab/) | Which visible ground-pass alternatives warrant review, without leaking recorded endpoints? | StatsBomb Euro 2024 + Women's Euro 2025 event/360, all 82 matches | Validated Python/Streamlit project and published Vercel case-study companion |
| [Rest Defence Analyzer](projects/rest-defence-analyzer/) | How vulnerable is a team to counterattacks while it attacks? | DFL open 2022/23 tracking and events; one complete match validated | Python/Streamlit workbench, independent XML audit and browser replay |
| [Is possession actually dangerous?](projects/possession-danger/) | Does Barcelona's possession create more danger than its rivals? | StatsBomb women's leagues; full Liga F 2023/24 and five-league samples | Python/Streamlit workbench, tested xT model, public browser dashboard and reproducible findings |
| [TacticAI Lite](projects/tacticai-lite/) | Which corner-kick patterns are associated with shot creation? | StatsBomb Euro 2024 and Women’s Euro 2025; all 82 matches | Validated Python/Streamlit project, match-held-out baseline and public aggregate explorer |
| [Possession Lab](projects/possession-lab/) | Who has possession when the ball disappears from the tracking? | Continuous scripted synthetic motion and two unlabelled public Metrica sample excerpts | Tested Python research package, observation-failure playground and paired observability explorer |

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

Open [Pressing trap detector](http://127.0.0.1:4173/), [The Invisible Runner](http://127.0.0.1:4173/invisible-runner/), [Rest Defence Analyzer](http://127.0.0.1:4173/rest-defence/), [Pass Decision Lab](http://127.0.0.1:4173/pass-decision-lab/), [Possession danger](http://127.0.0.1:4173/possession-danger/), [TacticAI Lite](http://127.0.0.1:4173/tacticai-lite/), or [Possession Lab](http://127.0.0.1:4173/possession-lab/). The build verifies and restores the published releases without downloading raw data or installing analytics dependencies. Keep the server running while using the websites.

## Reproduce the analysis

See the [project README](projects/pressing-trap-detector/README.md) for the download, extraction and test commands; the [methodology](projects/pressing-trap-detector/docs/methodology.md) defines the coordinate frame, recovery rule and denominators. The [article](projects/pressing-trap-detector/docs/where-does-spain-win-the-ball.md) reports findings under fixed five-second and ten-second definitions.

For tracking analysis, use the [Invisible Runner setup](projects/invisible-runner/README.md). It supports a small download for a smoke test and additional explicit match IDs. The full Python/Streamlit app recalculates thresholds; the published browser version uses reviewed profiles at 4.5, 5.0 and 5.5 m/s. No paid API or account is required to run either project locally.

Rest defence: see the [project setup](projects/rest-defence-analyzer/README.md) and [findings](projects/rest-defence-analyzer/outputs/J03WPY/findings.md). All 293 published behind-ball counts were independently checked. The fixed score has approximately zero correlation with subsequent ball movement in this match; it is an exploratory diagnostic.

Pass-choice research: see the [Pass Decision Lab setup](projects/pass-decision-lab/README.md) for the four-match smoke download, full 82-match run and local Streamlit app. Its [public companion](https://football-analytics-self.vercel.app/pass-decision-lab/) publishes 12 attributed review cases and aggregate model evidence; the [findings](projects/pass-decision-lab/outputs/findings.md) distinguish observed completion from hypothetical estimates. [Hosting instructions](projects/pass-decision-lab/docs/deployment.md) explain the static Vercel release and full local explorer.

Possession research: the [Possession danger setup](projects/possession-danger/README.md) covers the six-match smoke download and full 240-match Liga F run. The [findings](projects/possession-danger/outputs/liga-f/findings.md) compare Barcelona with opponents in six held-out fixtures. Its browser dashboard uses reviewed derived possession summaries; event-level pitch inspection and recalculation run in the Python/Streamlit workbench.

For corner-kick research, see the [TacticAI Lite setup](projects/tacticai-lite/README.md), [findings](projects/tacticai-lite/reports/findings.md) and [deployment guide](projects/tacticai-lite/docs/deployment.md). Its public site contains aggregate analysis; raw events and player frames remain local under the provider’s terms.

Possession-state inference: see the [Possession Lab setup](projects/possession-lab/README.md), [tracking-only findings](projects/possession-lab/docs/phase1/REPORT.md) and [event-evidence findings](projects/possession-lab/docs/phase2/REPORT.md). Its browser explorer compares models, applies observation failures to public movement or continuous synthetic motion, and shows identical-observation counterexamples. The [motion v2 results](projects/possession-lab/docs/MOTION_V2.md) are separate from historical benchmarks. Synthetic scores are diagnostic; accuracy is withheld for the two public Metrica excerpts. Original benchmarks and scorer remain unchanged.

## Deployment

The websites are deployed at [football-analytics-self.vercel.app](https://football-analytics-self.vercel.app) through the repository's Vercel GitHub integration. Pushes to `main` update production; other branches create previews. The root `vercel.json` runs `python3 scripts/build_website.py` and serves `dist/`: the existing pressing dashboard at `/`, the run analyzer at `/invisible-runner/`, and rest-defence inspection at `/rest-defence/`. No environment variables or server functions are required. See the [Invisible Runner hosting guide](projects/invisible-runner/docs/deployment.md) and [pressing release guide](projects/pressing-trap-detector/docs/deployment.md).

Pass Decision Lab is served at `/pass-decision-lab/` by the same static build. Its committed release contains bounded analytical cases and aggregate model results, without raw StatsBomb snapshots.

Possession analysis is served at `/possession-danger/` by the same build. See its [hosting and release guide](projects/possession-danger/docs/deployment.md). Raw StatsBomb events and event coordinates are excluded from its public release.

TacticAI Lite is served at `/tacticai-lite/` by the same offline portfolio build.

Possession Lab is served at `/possession-lab/` by the same offline portfolio build. Its verified release bundles the Python browser runtime; the full research package and exact synthetic benchmark history live in [the project folder](projects/possession-lab/). See its [hosting guide](projects/possession-lab/docs/deployment.md). The original [Sites release](https://possession-lab-research-explorer.perkyfir10.chatgpt.site/) remains available.

## Repository conventions

Each project lives in `projects/<project-name>/` with its own README, methods, scripts and tests. Large raw downloads and generated analysis intermediates are excluded from Git. Source revisions and file hashes are retained for reproducibility. The committed website release contains its complete reviewed snapshot, stored losslessly in a compressed archive.

Data sources keep their original terms. The first project's data is supplied by [StatsBomb Open Data](https://github.com/hudl/open-data); its licence and attribution are included in that project. Third-party runtime code in the compiled dashboard is not claimed as original project code or relicensed by this repository.

The Invisible Runner uses [SkillCorner Open Data](https://github.com/SkillCorner/opendata), published with PySport under its supplied MIT notice. The source revision, field audit, license, methods and output hashes are retained in the project. Raw tracking and machine-local caches are excluded from Git; the published replay snapshot contains only the fields needed by the browser.

The Rest Defence Analyzer uses the DFL open dataset, authorized under CC BY 4.0 with DFL and Bassek et al. (2025) attribution. Its browser release serves reviewed historical results; the Python/Streamlit app supports reproduction and new match runs. See its [hosting guide](projects/rest-defence-analyzer/docs/deployment.md).

Possession Lab uses [Metrica Sports public sample tracking](https://github.com/metrica-sports/sample-data) with source hashes and attribution, plus clearly labelled synthetic observations. Code is MIT; public dataset and numerical runtime terms remain separate. Restricted competition files and public five-minute possession labels are excluded from its release.
