# 02. Marking Handoffs

**When the nearest defender changes, does plausible coverage persist?**

A Python research pilot for retrieving candidate defensive handoffs from SkillCorner's free broadcast tracking. It builds frame-level opponent graphs, scores plausible cover using distance, relative motion and local team structure, applies causal hysteresis, measures geometric coverage gaps, and exports searchable animated examples.

The output is **candidate handoffs**, never known coaching assignments. Geometry cannot establish that two defenders thought someone else was responsible.

Live project: [marking-handoffs.vercel.app](https://marking-handoffs.vercel.app).

GitHub and methodology: [Marking Handoffs](https://github.com/prithvi-kaizen/football-analytics/tree/main/projects/marking-handoffs).

## Evidence first

The [feasibility assessment](docs/feasibility.md) records actual schema, upstream inventory/licence, measured data-quality issues, the football question and the evaluation protocol before detector implementation. [Related work](docs/related-work.md) covers five published methods/public implementations and the project's modest contribution.

The upstream README still advertises ten matches; the pinned catalogue/tree contain twenty tracking assets. This pilot uses two complete files whose hashes match upstream LFS objects. Development is Brisbane Roar v Perth Glory (1925299); algorithm holdout is Sydney FC v Adelaide United (1996435). Only 57.9% and 65.8% of valid player positions are marked as detected. Extrapolation is preserved and disclosed.

## Recorded result

The baseline passes 1,000 independent real-coordinate distance checks. On 105,492 eligible held-out attacker-frames, the proposed method produces 306 candidates: 226 with continuous geometric cover, 36 with brief gaps and 44 with gaps of at least 0.4 s.

Identity changes decrease from 8.34 to 2.63 per attacker-minute, but assignment availability is 53.6% versus the baseline's 100%. Short interior assignment runs increase from 54 to 62, so the pre-specified real-data short-run hypothesis fails. This is **not an accuracy improvement claim**. Controlled synthetic tests pass the engineering hypothesis; real tactical detection accuracy remains unknown.

Read the generated [results](docs/results.md), [methodology](docs/methodology.md) and [limitations](docs/limitations.md). The primary candidates use both detected and extrapolated coordinates. A stricter detected-only sensitivity has a smaller, separately reported population.

## View the output

- Open `outputs/marking-handoffs.html` directly in a modern browser. It is self-contained and needs no service or API. Search names, match clock or IDs; compare nearest and proposed assignments; inspect gap and observation flags. All 801 candidates from both matches have replays.
- Watch `outputs/marking-handoffs-demo.mp4`, a 32-second tracking-only demonstration. The manifest records the deterministic example selection and playback rate.
- Inspect `outputs/candidates.csv`, `assignments.csv.gz`, `edges.csv.gz`, `sensitivity.csv`, `results.json` and `synthetic-results.json`. CSVs retain frame identifiers for auditing.

## Reproduce

Python 3.14 was used for the recorded run. Core analytics require NumPy; video rendering requires Pillow and the open-source FFmpeg executable. Matplotlib is optional for the publication figure. No paid APIs or private tracking data are needed.

```bash
cd projects/marking-handoffs
python3.14 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
export PYTHONPATH=.

# About 186 MB of pinned tracking plus small metadata/phase files.
.venv/bin/python scripts/prepare_data.py
# Or reuse an existing local directory; hashes are still checked:
# .venv/bin/python scripts/prepare_data.py --cache ../open-body/data/raw

.venv/bin/python scripts/inspect_data.py
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/run_baseline.py
.venv/bin/python scripts/run_experiment.py
.venv/bin/python scripts/build_viewer.py
.venv/bin/python scripts/render_demo.py
.venv/bin/python scripts/build_report.py
.venv/bin/python scripts/verify_exports.py
```

`scripts/reproduce.sh` runs these steps in order with an explicit Python executable. `run_experiment.py` refuses to proceed without successful baseline validation. The configuration is `configs/pilot.json`; a frozen copy and hash accompany every run. Tests use `unittest`, so no test dependency download is required.

For the optional figure, install `matplotlib==3.11.2` and run `scripts/plot_results.py`. The exact environment is recorded in `outputs/environment.json`. FFmpeg rendering uses common system fonts, with a Pillow fallback; font appearance and video bytes may differ by machine while metrics should reproduce.

## Modules

| Module | Responsibility |
|---|---|
| `data.py` | Metadata/JSONL loader, validation, velocity quality, phase alignment |
| `baseline.py` | Shared eligibility, contiguous segments, nearest-defender baseline and independent checks |
| `graph.py` | Pair features and weighted opponent graph |
| `temporal.py` | Causal assignment, hysteresis, candidate and gap extraction |
| `synthetic.py` | Known geometric scenarios, reserved evaluation seeds and event scoring |
| `evaluation.py` | Operational diagnostics and paired phase-cluster bootstrap |

## Public use and attribution

Data: [SkillCorner Open Data](https://github.com/SkillCorner/opendata), revision `4340d274572876239c154c90bc507a9b3250a656`. Preserve [SkillCorner's MIT notice](docs/source/LICENSE.skillcorner) when sharing derived material. The same notice is copied beside the demonstration. Raw data are ignored by Git and downloaded from pinned public URLs with hash verification. No broadcast footage is included.

Suggested publication drafts are in [publication.md](docs/publication.md). They include the failed real-data hypothesis and distinguish synthetic geometry from real tactical validation. No post has been published by these scripts.

The short LinkedIn draft with the live links is [linkedin-post.txt](docs/linkedin-post.txt).

## Static deployment

Run `python3 scripts/package_website.py` to copy the validated viewer, demonstration and SkillCorner licence into the ignored `web/` directory. Deploy that directory with Vercel CLI. The deployment needs no Python runtime or paid API; all analytics are computed ahead of time.
