# Possession Lab

**Who has the ball when the ball disappears?** An open football analytics research
project with an interactive model comparison, deterministic tracking failure
playground and paired observability explorer. Public Metrica excerpts demonstrate
tracking inference without claiming quantitative accuracy. Research modules,
historical results and scorer remain independent of the frontend.

Build and run the public demo using [explorer/README.md](explorer/README.md).
Code is MIT licensed; public data and numerical runtime terms remain separate.
The sections below retain the original research history and reproduction commands.

## Original preparation scope

Local preparation for More Than A Hack 2027 while restricted competition assets are unavailable.
This is a tested engineering scaffold, not a competition submission or an estimate of competition
performance. It uses synthetic labels and Metrica's public anonymized sample tracking only.

## Phase 1 update

Failure-driven development adds a hierarchical probabilistic model, four controlled ablations,
two legacy stationarity ablations, independent randomized trial families, exact-observation
counterexamples and a future in-memory Smart Tagging contract. Original feature calculations,
state machine, HMM, generator and benchmark configuration remain unchanged; 108 old truth/prediction
CSVs reproduce byte-for-byte. There are now **130 passing tests**.

Read the [Phase 1 findings](docs/phase1/REPORT.md), [full experimental report](outputs/phase1/report.md)
and [per-scenario comparison with uncertainty](outputs/phase1/comparison.md). The evaluation has
12 trials per mechanism, 14 scenarios and 10 methods (1,680 method runs), with whole-trial bootstrap
intervals, paired ablation deltas, D precision/recall, boundary errors and measured runtime.
This is a synthetic stress evaluation, not competition validation or a model-selection result.

```bash
bash scripts/reproduce_phase1.sh
```

Individual run: `.venv/bin/python -m possession_lab.cli phase1`. Configuration is in
`configs/phase1.json`; the [prospective protocol](docs/phase1/PROTOCOL.md) records the hypotheses
and evaluation design. The new method is also available as `infer(batch, "hierarchical")`, with
optional `HierarchicalConfig` and local/smoothed probabilities in the result's `probabilities`.
Its probabilities are uncalibrated. No tag inputs were fused in this phase.

The hierarchy avoids most stationary-live false D predictions but loses on some ordinary scenarios
to the original HMM. Moving-dead and invisible stoppages remain unresolved. Identical-observation
pairs demonstrate why no tracking-only model can resolve every such state. Missing-as-static also
slightly improved aggregate macroF1 in these synthetic trials, contrary to the proposed benefit of
masking, so the current suite cannot establish a superior missingness policy.

The remaining sections document the original preparation phase and its unchanged 81-run suite.

The detailed [challenge review](docs/CHALLENGE_REVIEW.md) records the task, scoring edge cases,
baseline implementation and constraints. The [restricted-data boundary](docs/SECURITY.md) explains
why the official-data adapter is intentionally disabled here.

## Reproduce

Tested on macOS arm64, Python **3.14.2**. The complete environment is pinned in
`requirements.lock.txt`; portability to other platforms/Python versions has not been verified.
Install the package in editable mode so its research configuration and scorer manifest remain
beside the source. No network access is required after setup and the public downloads.

From this directory, with the official repo as sibling `../more-than-a-hack-2027`:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
.venv/bin/python -m pip install --no-build-isolation --no-deps -e .
bash scripts/reproduce.sh
```

The script runs dependency validation, tests, supplied-baseline sanity evaluation, synthetic
experiments and both public CSV sample matches if their checkout is present. It never downloads
anything or looks for competition assets. Individual commands:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m possession_lab.cli sanity
MPLCONFIGDIR=.mpl-cache .venv/bin/python -m possession_lab.cli benchmark
.venv/bin/python -m possession_lab.cli sample \
  --home ../public-sample-data/data/Sample_Game_1/Sample_Game_1_RawTrackingData_Home_Team.csv \
  --away ../public-sample-data/data/Sample_Game_1/Sample_Game_1_RawTrackingData_Away_Team.csv \
  --out outputs/sample_game_1
```

Pinned source checkouts used:

| Source | Commit | Use |
|---|---|---|
| [Official challenge](https://github.com/metrica-sports/more-than-a-hack-2027) | `f8f2629ff1e0985f81d7e59d8413678514ee1530` | public documentation, supplied baseline CSVs and unchanged evaluator |
| [Metrica public samples](https://github.com/metrica-sports/sample-data) | `e706dd506b360d69d9d123d5b8026e7294b13996` | unscored CSV adapter and inference checks on Games 1/2 |

For a fresh workspace, clone these public repos as siblings and check out those commits. The
sample repository can use sparse checkout for `data/Sample_Game_1` and `data/Sample_Game_2`.
Game 3 is EPTS/JSON and is not supported by the CSV adapter. Attribution: tracking samples are
provided by Metrica Sports; use is subject to their published terms. No sample data is copied into
this package. Scorer integrity is checked against every tracked official file's SHA-256, and a
changed upstream checkout fails explicitly rather than silently changing the experiment.

## What is implemented

`TrackingAdapter.load() -> TrackingBatch -> infer(batch, method, config) -> InferenceResult`
is the common path. An adapter supplies sequential zero-based rows, global increasing timestamps,
explicit periods (0 outside play), ball `(n,2)` and per-team slot arrays `(n,p,2)` in metres.
H/A identity does not flip with attacking direction. NaNs stay missing and off-pitch coordinates
are retained. Invalid shapes, infinities, repeated period blocks and source alignment conflicts
raise errors. The future adapter has the same interface but refuses restricted ingestion.

| Module | Responsibility |
|---|---|
| `schema.py`, `csv_io.py` | physical dimensions, period boundaries and canonical H/A/D/X CSVs |
| `synthetic.py` | seeded latent spells, observation noise and controlled failures |
| `features.py` | nearest-team/distance, ball and collective player speed, coverage/reliability, observation masks/age and stationarity |
| `models.py` | fixed state machine and separate fixed-emission HMM/Viterbi |
| `adapters/metrica_csv.py` | explicit three-header public CSV parser, synchronized team axes and ball consistency checks |
| `official.py` | unchanged scorer import, integrity checks and isolated supplied-baseline sanity command |
| `experiments.py`, `plots.py`, `cli.py` | local configurations, metrics, manifests, predictions and failure charts |

No fitting is implemented. Parameters in `configs/benchmark.json` are transparent engineering
priors, fixed before the reported experiments. The public five-minute labels never enter feature
extraction or inference and never select a model/parameter. Public evaluation accepts only the
four hashed supplied predictions. The new models are **not** evaluated on those labels.

The diagnostic `nearest` method writes X on missing/ambiguous observations. It is distinct from
the official raw baseline, which maps failure to D. Do not compare its synthetic scores with the
official competition floor.

The state machine requires a player within 2.5 m and a 0.7 m advantage, adequate observation
coverage, and 0.32 s of consecutive evidence to confirm control. A temporary gap holds the last
state for up to 3 s, then abstains. Dead-ball evidence is observed out-of-bounds geometry or
sustained low ball **and** collective-player movement. Neither cue is definitive referee evidence.

The HMM uses hidden H/A/D, fixed categorical emission probabilities (0.9 for a supported state,
0.05 for alternatives; uniform when unsupported), a 0.985 self-transition prior, and log-space
Viterbi separately per period. X is an output abstention mask, not a physical state. It is offline
and can use future evidence; the state machine is causal. Emissions and outputs are not calibrated
probabilities. Motion uses a 0.4 s displacement and a trailing stationarity window; implausible
slot speeds above 12 m/s are excluded from the collective median. A fixed >45 m/s ball-speed
quality penalty is a crude observation check, not a measured error model.

## Synthetic assumptions

Every seed uses the same explicit two-period schedule: 121 seconds total, including outside-play
gaps, eight team possession spells and four stoppages. Seeds change spatial layout, phase, noise,
missingness and slot permutations, **not** spell timing. Thus seed variation is observation
variation on one artificial schedule, not uncertainty across independent matches.

Players move around simple formations, with one carrier placed near a smooth 2D ball path.
Motion may jump at possession changes; there are no realistic pass trajectories, ball height,
referee decisions, learned team tactics, camera visibility or cross-team identity errors.
Stoppages freeze the scene. These simplifications deliberately make basic control easy and expose
the weak stationarity assumption. This generator cannot establish football validity.

Controls include coordinate noise, framewise ball occlusion, contiguous ball gaps, per-slot
missingness, within-team slot identity switches, brief opponent proximity without control,
stoppages, unseen transitions, stationary live play and completely invisible stoppages. The
contested mask and latent labels are diagnostics only and never passed to inference.

## Results actually run

All four supplied baseline scores reproduced (see `outputs/public_sanity/scoreboard.csv`), using
the public evaluator and no restricted assets. This re-scores committed predictions; it cannot
regenerate their tracking-dependent inputs without access. Official files remain unchanged.

The fixed synthetic suite has nine scenarios x three seeds (101, 202, 303) x three methods = 81
runs. Below are equal-weight means across the three observation seeds. Macro/spell values are
descriptive engineering diagnostics, not expected competition scores.

| Synthetic scenario | State machine macro / spell | HMM macro / spell |
|---|---:|---:|
| clean | 0.8372 / 1.0000 | 0.9102 / 1.0000 |
| noisy | 0.8281 / 1.0000 | 0.9061 / 1.0000 |
| occlusion and burst gaps | 0.5914 / 0.6768 | 0.7500 / 0.8786 |
| player gaps | 0.5818 / 0.7086 | 0.9012 / 1.0000 |
| within-team identity switches | 0.8188 / 1.0000 | 0.9041 / 1.0000 |
| brief contests | 0.8281 / 1.0000 | 0.9232 / 1.0000 |
| invisible transitions | 0.6294 / 0.6333 | 0.7880 / 0.8667 |
| stationary live play | 0.2282 / 0.0000 | 0.2454 / 0.0000 |
| invisible stoppages | 0.6243 / 0.6857 | 0.6266 / 0.7143 |

The failures matter more than the easy scores. Both temporal models incorrectly interpret
stationary live play as dead. With the ball absent for an entire stoppage, both have D F1 **0**.
The state machine can also fail to collect eight consecutive reliable observations under dense
missingness. Viterbi recovers some boundaries using future context, a capability the causal
method does not have. Perfect spell F1 on simple scenarios still coexists with poor D timing:
loose IoU matching can tolerate substantial boundary errors.

Both complete public samples loaded and ran through all three methods: Game 1 has 145,006 frames
(14/14 home/away slots), Game 2 has 141,156 frames (14/12 slots), and both have two periods.
No events were loaded, no heuristic possession states were called truth, and no accuracy was
reported for these samples. Sample receipt files record source hashes and observed coverage.

Outputs are entirely local under `outputs/`: per-run truth/prediction CSVs, official detailed
metric JSON, feature/failure CSVs, a consolidated metrics table, mean/sample-SD summaries and
configuration/environment/source-hash manifests. Exact per-run results, rather than rounded
numbers above, are the audit trail. Figures use seed SD only; there is no inferential interval.

![Synthetic scores](outputs/synthetic/metrics.png)

![Synthetic failure modes](outputs/synthetic/failure_modes.png)

## Verification and next steps

All **88 tests passed**, and dependency validation found no broken requirements. The tests cover
metric edge cases, exact control boundaries, H/A/D/X, missing/partial values,
physical scaling, period endpoints/reset, stable outputs, identity-switch invariance of geometry,
public sample schema conflicts, unchanged scorer hashes, supplied baseline reproduction and
byte-identical prediction/metric reruns of the end-to-end harness. A full-length synthetic CSV
passes the official validator. Test evidence is in `outputs/validation/pytest.txt` after reproduction.

Next work should retain this configuration as a regression suite and add independently designed
spells, coherent passes/duels and state-dependent visibility. Resolve the dead-ball ambiguity
with an explicit uncertain evidence channel, first tested using synthetic event noise and conflicts.
Evaluate on other *legitimately labelled* matches if available, with match-level splits and no
competition-game labels. Only after those checks consider duration-aware semi-Markov inference.
Official ATD/Smart Tagging integration must happen in the separate human-run environment described
in SECURITY.md. No competition improvement is claimed, and no model was selected using its labels.
