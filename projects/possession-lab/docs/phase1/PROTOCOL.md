# Phase 1 protocol, fixed before the new suite was evaluated

No fitting or parameter search. Config `configs/phase1.json` defines engineering priors and 12
trial IDs per scenario. Development uses small fabricated fixtures and the old stationary-live
case. These trials are a prospective synthetic stress test for this implementation, not an
untouched benchmark for future iterations. Any later changes must be disclosed and use new trials.

Hypotheses: (1) removing the old hard stationarity override prevents most false D on stationary
live play but loses static dead detection; (2) weak evidence with joint factorized decoding can
retain control while static; (3) masking unavailable quantities avoids invented static evidence;
(4) duration and possession priors suppress flicker but can delay or erase short states;
(5) no tracking-only method can resolve identical complete observation sequences with opposite
live/dead truth. No universal winner is presumed.

Preserve `features.py`, `models.py`, `synthetic.py` and the old benchmark config byte-for-byte.
`baseline_manifest.json` records their hashes and old output hashes. Original state machine/HMM
remain callable unchanged. Two explicitly named counterfactual runs zero only the existing
stationarity feature; these are ablations, not replacements of the originals.

Compare nearest, original state machine, original HMM, the two stationarity-off legacy ablations,
the hierarchical full model, and its four one-factor variants: no stationarity, missing treated
as static (unsafe negative control), no live/dead duration priors, no owner continuity. Keep all
other code/configs, trial observations, period handling and output abstention policy fixed.
Duration is a geometric continuous-time Markov prior, not a learned or explicit minimum duration.
Owner memory is latent while dead and is not an output claim of dead-ball ownership.

New generator: independently sampled schedules/durations, starting teams, formations, ball paths
and observation errors. Mechanisms include MCAR, Markov gaps, state/transition-dependent loss,
camera cropping, moving dead-ball players, live freezes, fully hidden dead balls, slot switches,
outliers and shorter spells. Same trial ID couples methods and, where possible, mechanisms for
paired comparison. Twin scenarios share entire tracking arrays but differ in a target interval's
labels. They are paired counterexamples, not independent examples to pool for precision.

Endpoints per scenario/method: official macroF1 and spellF1; D precision/recall (zero convention
and undefined denominators reported); exact typed possession-start/end boundary precision/recall,
missed/spurious counts and matched absolute latency within +/-25 frames; abstention and graded
frame accuracy; extraction and decoder wall times and real-time factor. Official metrics use their
own X filling; boundary diagnostics use the same filling per true graded block. No invented
boundary annotations on a real match.

Uncertainty: nonparametric 95% percentile bootstrap over *whole synthetic trials*, 2,000 draws,
fixed seed. All methods use the same resampled trial IDs. Report paired mean deltas relative to
the full hierarchy. Each trial is equally weighted; do not bootstrap frames. Intervals quantify
variation only under the declared generator and are not football/competition confidence bounds.
CIs across many exploratory endpoints are not multiplicity-adjusted hypothesis tests. Runtime
is single-process wall time on this host after one warm-up, includes output-probability computation
for the hierarchy and excludes I/O/scoring; timings are descriptive and not deterministic.

No restricted data ingestion, no public-label tuning, no event-derived ground truth, no fabricated
actual-match tags and no paid/hosted inference. DATA.md is read only as public interface documentation.
