# One Step Behind

[Live explorer](https://one-step-behind-pk02ib2if-prithvirajs-projects-b40fa6af.vercel.app) · [Public code and methodology](https://github.com/prithvi-kaizen/football-analytics/tree/main/projects/one-step-behind)

**When a defensive line steps forward, does one defender remain behind?**

A two-match SkillCorner tracking pilot with an interpretable Python detector and a pitch-first browser replay. The frozen method retrieved **0 candidates in 49 development steps and 0 in 44 held-out steps**. The instantaneous 3 m baseline flagged two held-out steps; neither passed the full temporal rules. Candidate duration and recovery distributions are therefore unavailable. The project preserves that negative result.

In the clearest example, Adelaide's Fabian Talladira reaches a **3.53 m** gap behind his peers' median depth. He has still advanced **1.76 m**, against a peer median advance of **2.36 m**. All four line players are marked detected throughout the clip. Deeper position and lagging movement are different measurements.

## Inspect the work

- [Frozen protocol, feasibility and three research approaches](docs/protocol.md)
- [Generated evaluation, denominators, coverage and sensitivity report](docs/results.md)
- [731-word analytical article](docs/article.md)
- [LinkedIn draft](docs/linkedin-post.txt), with deployment status made explicit
- [Real replay evidence](outputs/replays.json), [32-second silent MP4](outputs/demo.mp4), [video timing and provenance](outputs/video-manifest.json)
- [Independent scalar gap checks](outputs/independent-checks.json)

The three examples are two instantaneous baseline flags and a comparison step, **not three detected lagging events**. Selection is documented in the evaluation report. No broadcast footage or simulated tracking is presented as real.

## Method and limitations

Normalize the defending team's forward direction by half. Use metadata-listed central defenders and fullbacks only when they form a plausible last line: three to five active players, at least two central defenders, exactly the deepest N outfield players, at least 12 m wide and at most 12 m deep. Other shapes are excluded. Three- and four-player units occur here; five-player support is unit-tested, not observed in this sample.

From a line initially within 3 m, require sustained forward advance by at least N−1 players over one second. For each player, compare depth to the median of the other line players. A candidate needs a growing ≥3 m gap, compact peers, at most half their forward movement and ≥0.5 s persistence. Recovery means the whole line returns within tolerance for ≥0.5 s; missing positions and context changes censor follow-up. All thresholds live in [configs/pilot.json](configs/pilot.json), whose hash is recorded in results.

Only **57.89% / 65.80%** of valid player coordinates are marked detected in development / holdout. Complete geometry can still be extrapolated. An observed-only rerun has a separate denominator: 8 / 22 steps and no candidates. It must not be read as a matched validation subset. Held-out candidate counts remain zero across 2–4 m tolerance and 0.3–0.8 s persistence. Development has one candidate at 2 m, a sensitivity result only.

These restrictive rules select orderly, role-backed lines and can miss genuine defensive reorganizations. Detection flags do not establish identity correctness. The two matches were selected from an available cache and are not representative of a league; the author previously used this dataset for a different question. No tactical ground truth, accuracy estimate, offside-trap diagnosis, defensive-error claim or causal attribution is supplied.

Unlike Marking Handoffs, this studies within-line depth during forward movement, not opponent-coverage transfers. Unlike Rest Defence Analyzer, it does not measure protection around possession losses.

## Reproduce the analysis

Recorded environment: Python 3.14.2, NumPy 2.5.4, Pillow 13.0.0 and FFmpeg 8.0. Core analysis needs NumPy; Pillow and FFmpeg are for rendering. Exact package versions are pinned. Python 3.11+ should run the source, subject to compatible package availability; the recorded environment is the tested path.

```sh
cd projects/one-step-behind
python3.14 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
export PYTHONPATH=.

# ~186 MB, pinned upstream files, validated by LFS SHA-256 / Git blob SHA-1.
.venv/bin/python scripts/prepare_data.py
# Optional verified local cache instead of another download:
# .venv/bin/python scripts/prepare_data.py --cache ../marking-handoffs/data/raw

.venv/bin/python scripts/audit_data.py
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/run_analysis.py
.venv/bin/python scripts/export_replays.py
.venv/bin/python scripts/build_report.py
.venv/bin/python scripts/render_demo.py
.venv/bin/python scripts/verify_outputs.py
.venv/bin/python scripts/build_website.py
```

`scripts/reproduce.sh` runs these stages using the Python executable passed as its first argument. Raw files stay in ignored `data/raw/`; no other project's results are imported. The loader and downloader were adapted from this repository's Marking Handoffs source, then kept local so this project has no runtime dependency on it.

## Portfolio build

The root Vercel build now includes `/one-step-behind/`. It uses only Python's standard library and precomputed outputs. It does not need raw tracking, NumPy, a backend, an API key or a CDN.

```sh
# From repository root:
python3 scripts/build_website.py
python3 -m http.server 4173 --bind 127.0.0.1 --directory dist
```

Open `http://127.0.0.1:4173/one-step-behind/`. Play/pause, step frames, scrub, switch between three real sequences, change the local positional tolerance and inspect observation flags. The slider recalculates the clip interpretation; published aggregate counts retain the frozen configuration. The default replay is the fully detected Adelaide example. Dark view and native keyboard controls are available.

The standalone explorer is deployed on Vercel at the live link above, with public access explicitly approved. Source and the portfolio route `/one-step-behind/` are integrated into `main`. The LinkedIn post remains a draft. Unrelated workspace changes were not published.

## Attribution

Data: [SkillCorner Open Data](https://github.com/SkillCorner/opendata), revision `4340d274572876239c154c90bc507a9b3250a656`. Preserve [SkillCorner's MIT notice](docs/source/LICENSE.skillcorner), copied beside the browser release and demo. [Source receipts](data/provenance.json) give pinned URLs, byte sizes and hashes. The catalogue/tree and LFS pointers are retained in `docs/source/`. Original code is MIT-licensed. Public coordinates are time-subsetted, rotated for display and used to derive geometric metrics. No match-video rights are implied.
