# Phase 1: failure-driven possession inference

Synthetic results only. No public-label fitting/tuning, restricted-data ingestion, actual-match
tag fabrication, or competition-performance claim. The original temporal baselines and scorer
remain unchanged. The report is generated from saved results, not manually selected examples.

## Checked failure mechanism

On the old stationary-live case (seed 101), 89.3% of live frames
crossed the stationarity threshold. The evidence function overwrote 2,000
valid team-control observations with D, despite 0 live out-of-bounds frames.
The state machine predicted D on 89.5% of live frames; the HMM on
88.9%. This was checked from distances, speed features, evidence and decoded
outputs (`legacy_trace.csv`). The feature takes trailing medians of 0.4 s endpoint speeds;
after enough observed values remain below 0.8 m/s, it accumulates stationary seconds. Short
gaps can still leave enough values in the trailing window. `evidence()` assigns H/A first,
then overwrites with D at >=1.2 s. Repeated D evidence resets the state-machine observation age
and reconfirms D; the HMM repeatedly assigns a 0.9 versus 0.05 emission advantage. Temporal
stickiness compounds the error but is not its initial cause.

## Model and controlled comparisons

The hierarchy has latent states live-H, live-A, dead-with-H-memory and dead-with-A-memory.
The latter two both output D and do not claim dead-ball ownership. Two fixed logistic heads
estimate live/dead and owner given live from geometry, motion and observation masks. Local
probabilities become likelihood-ratio potentials relative to neutral hierarchical priors;
this avoids favouring D merely because team evidence is absent. Weak stationarity evidence
is additive, never a hard override. An explicit output mask abstains after 3 s without a
reliable ball and on completely unobserved periods. It is separate from hidden-state inference.
Live/dead duration and team continuity use independent Markov transition factors. Joint Viterbi
finds the MAP path; scaled forward/backward gives normalized marginals. Inference is offline.
The scores and marginals use uncalibrated engineering priors, not learned probabilities.

Frame potentials are tempered by 0.2 because successive window-derived features are correlated;
this is a declared heuristic, not an estimated correction. Feature coverage still counts track
slots, not physical players, so fragmented slot inventories can alter apparent reliability.
No calibration, log-loss validation or transfer to the official ATD distribution is established.

All one-factor ablations retain the other inputs, priors and abstention rule. Legacy
stationarity-off variants zero only the stationarity feature in a copy; the original functions
are untouched. Hierarchical variants remove stationarity, make the unsafe missing-as-static
assumption, remove live/dead durations, or remove owner continuity. Full parameters and the
prospective protocol are in `config.json` and `../../docs/phase1/PROTOCOL.md`.

## Independent synthetic evaluation

12 trials per scenario; 14 scenarios; 10 methods; 1,680 method runs.
Trial schedules, durations, starting teams, formations and trajectories vary. Observation
families change the data-generating mechanism, not just the seed: IID loss, Markov bursts,
transition-dependent loss, camera cropping, moving dead-ball players, live freezes, invisible
stoppages, slot switches, outliers and short spells. All methods see identical observations
within a trial. Synthetic player/carrier jumps and simple referee-state mechanisms remain
major limitations. No parameters were selected using this evaluation.

Intervals below are 95% whole-trial percentile bootstrap intervals (2,000 draws), conditional
on this generator. Methods use the same trial resamples. They are exploratory, unadjusted
for multiple comparisons, and do not estimate uncertainty on real football matches.

| Scenario | SM spell | HMM spell | Hierarchy spell [95%] | Hierarchy macro [95%] |
|---|---:|---:|---:|---:|
| bursty | 0.789 | 0.867 | 0.816 [0.765, 0.868] | 0.723 [0.686, 0.765] |
| camera_window | 0.219 | 0.302 | 0.331 [0.216, 0.460] | 0.344 [0.259, 0.421] |
| identity_switches | 0.880 | 0.930 | 0.850 [0.803, 0.895] | 0.778 [0.735, 0.824] |
| iid | 0.879 | 0.935 | 0.845 [0.794, 0.894] | 0.778 [0.735, 0.824] |
| invisible_stoppages | 0.718 | 0.760 | 0.761 [0.691, 0.818] | 0.588 [0.580, 0.595] |
| moving_dead | 0.719 | 0.768 | 0.776 [0.713, 0.824] | 0.564 [0.553, 0.575] |
| outliers | 0.847 | 0.935 | 0.848 [0.794, 0.902] | 0.778 [0.736, 0.824] |
| short_spells | 0.454 | 0.778 | 0.688 [0.614, 0.769] | 0.673 [0.616, 0.737] |
| state_dependent | 0.743 | 0.933 | 0.831 [0.768, 0.888] | 0.768 [0.724, 0.817] |
| stationary_live | 0.054 | 0.041 | 0.851 [0.802, 0.897] | 0.777 [0.735, 0.824] |
| twin_invisible_dead | 0.167 | 0.167 | 0.167 [0.122, 0.211] | 0.296 [0.294, 0.297] |
| twin_invisible_live | 1.000 | 1.000 | 1.000 [1.000, 1.000] | 0.301 [0.292, 0.310] |
| twin_static_dead | 0.975 | 0.992 | 0.167 [0.122, 0.211] | 0.264 [0.256, 0.273] |
| twin_static_live | 0.244 | 0.200 | 1.000 [1.000, 1.000] | 0.333 [0.333, 0.333] |

Every method, including nearest and every ablation, has per-scenario macroF1, spellF1, D
precision/recall, boundary errors and timing with confidence intervals in `comparison.md` and
`confidence.csv`. `metrics.csv` contains every trial, denominator and raw error count.

## D detection, possession boundaries and cost

D precision is undefined if no graded frame was predicted D; D recall is undefined if there
is no true D. These are n/a, not zero or perfect. Confidence tables include the number of
defined trials, so conditional precision must be read with predicted-D counts and recall.
Boundary diagnostics type both starts and ends by team, exclude known period edges, and
match one-to-one within each graded block at +/-25 frames after the official X filling.
The matched latency excludes missed boundaries; read missed/spurious counts beside it.

| Scenario | Hierarchy D P / R | Missed / spurious boundaries | Matched MAE (frames) |
|---|---:|---:|---:|
| bursty | 1.000 / 0.319 | 7.2 / 5.8 | 4.4 |
| camera_window | n/a / 0.000 | 14.8 / 4.0 | 3.0 |
| identity_switches | 1.000 / 0.385 | 4.7 / 4.1 | 2.5 |
| iid | 1.000 / 0.385 | 4.7 / 4.4 | 2.2 |
| invisible_stoppages | n/a / 0.000 | 8.5 / 4.7 | 0.8 |
| moving_dead | n/a / 0.000 | 8.3 / 5.7 | 0.8 |
| outliers | 1.000 / 0.385 | 4.8 / 4.5 | 2.4 |
| short_spells | 1.000 / 0.387 | 5.0 / 3.1 | 3.2 |
| state_dependent | 1.000 / 0.378 | 5.0 / 4.2 | 3.3 |
| stationary_live | 1.000 / 0.384 | 4.7 / 3.9 | 2.4 |
| twin_invisible_dead | n/a / 0.000 | 2.0 / 0.0 | n/a |
| twin_invisible_live | n/a / n/a | 0.0 / 0.0 | n/a |
| twin_static_dead | n/a / 0.000 | 2.0 / 0.0 | n/a |
| twin_static_live | n/a / n/a | 0.0 / 0.0 | n/a |

Runtime below is a descriptive mean over ordinary scenarios/trials on this host, after warm-up
with counterbalanced method order. It includes extraction plus decoding, and excludes scoring
and I/O. The hierarchy also computes posterior marginals; baselines output labels only.
No peak-memory benchmark or deployment-throughput claim is made. Per-scenario cost intervals
are in the full table. Both Viterbi implementations use O(T K^2) time and O(T K) memory.

| Method | Frame macroF1 | SpellF1 | Feature ms | Decode ms | Total ms | Real-time factor |
|---|---:|---:|---:|---:|---:|---:|
| nearest | 0.478 | 0.039 | 37.7 | 0.0 | 37.7 | 0.00035 |
| state_machine | 0.590 | 0.630 | 37.7 | 0.7 | 38.4 | 0.00036 |
| hmm | 0.671 | 0.725 | 37.7 | 9.5 | 47.2 | 0.00044 |
| hierarchical | 0.677 | 0.760 | 37.7 | 20.6 | 58.3 | 0.00055 |

These pooled means weight the declared scenarios equally; they are not a general ranking.

## Ablations and failed hypotheses

Deltas below are ablation minus full hierarchy, first averaging ordinary scenarios within
each trial ID, then bootstrapping the 12 trial clusters. This retains correlation between
mechanisms sharing latent matches. Positive F1 deltas favour the ablation, not the full model.

| Ablation | SpellF1 delta [95%] | macroF1 delta [95%] |
|---|---:|---:|
| hier_no_stationary | -0.001 [-0.004, +0.002] | -0.000 [-0.000, +0.000] |
| hier_missing_as_static | -0.000 [-0.005, +0.004] | +0.005 [+0.003, +0.007] |
| hier_no_duration | -0.387 [-0.420, -0.352] | +0.005 [-0.003, +0.015] |
| hier_no_continuity | -0.743 [-0.794, -0.692] | -0.065 [-0.072, -0.058] |

Removing the hard stationarity rule is not a complete dead-ball solution. On stationary-live
trials the original SM and its stationarity-off variant have mean spellF1 0.054 and 0.816; on moving-dead trials the full hierarchy has D recall 0.000.
Tracking stationarity is neither necessary nor sufficient for dead ball. Model confidence
does not establish identifiability. Duration priors are not a replacement for missing referee
evidence. In this suite, removing them increased aggregate frame macroF1 slightly but severely
reduced spellF1, including on short-spell trials. Use the
scenario-specific paired deltas rather than interpreting an aggregate as universal benefit.

The hypothesized consistent benefit of masking missingness was not supported by this suite:
the unsafe missing-as-static variant slightly increased aggregate macroF1, while its spellF1
delta included zero. This exposes a weakness of these observation mechanisms as a validation
of missing-data policy; it does not turn absent coordinates into physical static-ball evidence.
Removing the already weak stationarity term also had little aggregate effect. The hierarchy
is worse than the original HMM on several ordinary mechanisms, even though it rescues live
freezes. It is not a universal replacement for the baseline.

## Identifiability counterexamples

Each twin family supplies the same complete tracking sequence, missingness, timestamps and
periods for a live world and a dead world. Only an interval's truth differs. Static twins
include a nearby apparent controller; invisible twins hide the ball while players move.
Common visible motion before and after the target can represent either a live pass or a
restart; the referee decision is absent. The inputs are noisy tracking observations, not
a claim that every latent physical detail is equal in both worlds.
No tracking-only deterministic method can output different labels for identical inputs.
On the differing interval its two frame accuracies sum to at most 1 (possibly less when it
abstains). Under an equal prior over the two worlds the maximum expected target accuracy
is 50%, including for randomized rules. This is a frame-classification bound, not a bound
of 0.5 on macroF1 or spellF1. Future context cannot help because the whole sequences match.
`ambiguity_checks.json` verifies identical predictions across both worlds for every method
and trial. Twin-live cases lack D and A, so even a perfect all-H frame prediction has
official macroF1 1/3; absent classes are scored zero. Target accuracy and denominator counts
in `metrics.csv` make this explicit. Twin worlds are not pooled as independent matches.

## Recommendations and Smart Tagging seam

Keep the original models as regression controls. Treat stationary live and moving-dead
failures as negative controls in any further work. Use genuinely independent labelled other
matches and match-level splits before calibrating or selecting priors. Expand physically
coherent passing/referee scenarios with new trial IDs for later model revisions.
Read `docs/phase1/SMART_TAGGING.md` in the package for the future interface derived from public
DATA.md. Phase intervals must retain unknown teams, overlap conflicts and unknown confidence;
a restart window is not an exact whistle timestamp. The implementation validates loader-shaped
records in memory using fictional examples only and never converts phases to truth labels.
No tags are ingested or fused in this experiment. Restricted integration remains disabled
here and belongs in a separate human-run environment outside Codex access.
