# The Corner That Never Ended

An event-sequence study of the ball after the first corner delivery. **[Interactive explorer](https://football-analytics-self.vercel.app/corner-second-phase/)** · [Article](docs/article.md) · [35-second original animation](media/demo.mp4) · [social copy](docs/social.md)

This investigates **second-phase possession and post-clearance outcomes**, following [TacticAI Lite](../tacticai-lite/README.md)'s initial delivery and corner-routine work. The dataset is men's UEFA Euro 2024 (51 matches, 512 corners) and UEFA Women's Euro 2025 (31 matches, 305 corners), drawn from [StatsBomb Open Data](https://github.com/hudl/open-data) at pinned revision `4b73468fc5b0f1950f9f66fada70ad3a4f9327cb`. It contains no Premier League 2026/27 matches. The [Premier League guidance](https://www.premierleague.com/en/news/4674118/premier-league-sets-football-principles-for-202627-season) and current reporting provide editorial context only.

## Main result, 15-second window

| Measure | Euro 2024 | Women's Euro 2025 | Combined, descriptive |
|---|---:|---:|---:|
| Corners | 512 | 305 | 817 |
| Defensive contact | 445 | 265 | 710 |
| Attacking action strictly after contact | 241 | 148 | 389 (47.6%; match-bootstrap 95% 44.1–51.3%) |
| Corner with recovered second-phase shot | 65 | 61 | 126 (15.4%; 95% 12.9–17.9%) |
| Corner with a box entry after recovery | 64 | 53 | 117 |
| Confirmed defending control | 86 | 52 | 138 |
| Opposition shot within 15s after control | 7 | 2 | 9 |

The published aggregates in [summary.json](results/summary.json) are the machine-readable source of truth; run the pipeline to refresh this table. Among classifiable shots in the 15-second window, 69 came on the first ball, 44 from unopposed continuation and 140 after contact and recovery. **75 further shots have unknown phase** because attacking and defending actions share a recorded timestamp. The first-ball-only count therefore understates known subsequent shooting activity, but the unknown shots prevent an exact share of all danger. No tactical or refereeing causal effect is inferred.

## Reproduce exactly

Python 3.11+, `ffmpeg` and Pillow are needed only to remake the animation. The analysis uses the Python standard library; tests use `pytest`.

```bash
cd projects/corner-second-phase
python3 src/fetch.py
python3 src/analyse.py --cache data/raw/data --output results
python3 src/context_control.py --cache data/raw/data --output results/context_control.json
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests -q
python3 src/make_demo.py
python3 src/build_web.py --output ../../dist/corner-second-phase
```

`fetch.py` downloads the 82 match event files and competition/match inventories from the pinned revision, writes SHA-256 receipts under ignored `data/raw/`, and refuses a corrupted cache. It does not download 360 frames. If the TacticAI Lite cache already exists, `analyse.py` automatically reuses its verified files; pass `--cache` explicitly for an independent reproduction. The pinned source has 817 corners. The local `results/episodes.local.json` contains per-corner derived event summaries and is ignored by Git. Public web assets contain only aggregates and three short, authored sequence summaries. The [source agreement](https://github.com/hudl/open-data/blob/master/LICENSE.pdf) restricts redistribution and commercial use of provider data and asks for StatsBomb logo attribution. The code and original diagrams here do not license the provider's feed.

## Definitions and checks

The [frozen protocol](docs/PROTOCOL.md) defines all states before analysis. A defender's touch is not a clearance; a `Clearance` event is not confirmed defensive control. Attacking recovery requires a later attacking on-ball action. Defensive control requires a defending Pass, Carry, Shot or Dribble with the defender named as `possession_team`. Simultaneous actions remain unknown. A new restart, stoppage or period boundary closes an episode. The analysis validates unique IDs and indexes, ordered events, clocks, possession fields and pinned SHA-256 receipts. See [audit.json](results/audit.json) and [methods/results](docs/RESULTS.md).

One corner is one observation for binary rates. Match-clustered bootstrap intervals resample matches, not the correlated events inside them. The counterattack statistic is conditional on confirmed defending control and is descriptive. The 10/15/20/30-second sensitivity, time-to-event summaries and rare-outcome interval are published with the aggregates. Team-level rankings and a discrete-time hazard model are withheld because these tournaments provide few independent matches per team and phase timestamps include unresolved ties.

## Portfolio build

From the repository root, `python3 scripts/build_website.py` assembles the existing portfolio and this static explorer at `/corner-second-phase/`. The local source project keeps the full research protocol, article, tests and animation script. The website has no runtime Python or paid service. `web/data.json` is generated; the build copies it into `dist/` with the original demo and StatsBomb attribution logo.
