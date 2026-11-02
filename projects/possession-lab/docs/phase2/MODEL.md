# Phase 2 implementation and assumptions

The original HMM, hierarchy, feature calculations, generators, configurations and Phase 1
outputs are unchanged. `phase1_freeze.json` pins 408 pre-existing files; the reproduction script
recomputes old results into `outputs/phase2/historical_reproduction`, never their original paths.
No additional dependency, model training or parameter search is introduced.

## Forward world and observation process

`event_worlds.py` implements two action processes. Episode worlds sample live action sequences,
signals, cancelled attempts and eventual restarts. Renewal worlds sample action times from an
independent exponential clock with a different category mix. They share `rule_labels`: an
allowed stop gesture causes D, an allowed restart attempt can leave D, a controlled touch can
change the live controller, and a disallowed action cannot change state. Initial teams and
periods are explicit simulator inputs. The generators share rule semantics and several rendering
simplifications; they are not two independent implementations of football physics.

Tracking uses sinusoidal ball/player paths in the episode family and correlated-velocity paths
in the renewal family, with observation noise and different missing-ball regimes. Off-ball
players can move during stoppages, and live ball movement can freeze. Carrier assignments and
resumption paths can jump. Referee gestures, authorizations and actions do not appear in the
2D tracking arrays. This artificial extra modality is the question being tested.

PrivateAction contains a public ActionCue and a private permission bit. `visible_cues()` drops
the private bit. `synthetic_tags.observe_actions` accepts only cue projections, period axis,
optional shared-view visibility, an RNG seed and annotation configuration. It does not accept
truth, true boundaries or a world object. Changing private permissions while keeping cues fixed
can change truth but must leave the annotation distribution unchanged; tests check this exactly.

Visible restart attempts produce set-piece reports with probability 0.8 before additional
category noise. Ordinary passes can also produce them (0.1). Stop gestures produce stoppage
reports with probability 0.8; advisory gestures can produce the same report (0.15). Other cue
types produce phase/other reports. Additional corruption can change any category, suppress a
detection, or add independent false positives. Intervals are jittered, broadened windows around
actions, not dead-span boundaries. All annotation confidence values are None, including false
positives. Team values can be unknown/wrong; synthetic throw-ins always have unknown team.
Exact duplicate reports and category/team conflicts are added explicitly.

The synthetic `stoppage signal` category is hypothetical and absent from the promised public
schema. A restart-only ablation is required for interpreting relevance to actual Smart Tagging.
Phase-team tags are never treated as possession truth. No synthetic tag is attached to an actual
competition frame; every timeline here is fabricated and marked synthetic.

## Optional event potentials

`infer_events(batch, tags=(), ...)` is an additive interface; the original `infer` entry point
and `hierarchical()` function are untouched. Empty, disabled or zero-weight tags return the
original hierarchy exactly, including its posterior and abstentions.

In probabilistic mode, each uncertain interval defines a uniform distribution of possible action
times. An analytically integrated exponential context gives support after a stop cue, before and
after a restart cue, and weak conditional team support after a restart. Defaults are 6 s context,
3 s pre-restart context, assumed stop correctness 0.85, restart correctness 0.8 and team correctness
0.65. These are transparent engineering assumptions, not empirical/calibrated likelihoods.
Unseen tags give zero evidence, not evidence of D or live play.

Stop support contributes negative live log odds; restart support contributes positive odds after
and negative odds before the uncertain action. Generic phases/other codes contribute nothing.
Team hints affect H/A conditional on live, never a dead-ball ownership output. Exact repeats are
deduplicated from observable fields; overlapping support is averaged and log odds clipped to
[-2,2]. Near-duplicate dependence is only approximately controlled by this averaging/cap.
Conflicting team hints can cancel. A large number of copies cannot independently certify a state.

In conservative mode, only an ordered stop/restart pair in the same period, with non-overlapping
uncertain windows and centres within 18 s, contributes a soft D preference. Its support is the
product of stop-time CDF and complementary restart-time CDF. It does not force D, infer a precise
whistle instant, assign a hard label to a phase, or use conditional team hints.

Event log odds become two logistic heads q=P(live), r=P(home|live) and the same neutral-reference
joint potentials `[4*q*r, 4*q*(1-r), 2*(1-q), 2*(1-q)]` used in Phase 1. Event log potentials are
multiplied by fixed power 0.35 and added to the frozen tracking log potentials. The unchanged
four-state Viterbi/forward-backward decoder and transition priors then run per period. This is
offline inference: a future restart report can provide uncertain context before the restart.
It is not a real-time or calibrated posterior claim.

Event support above a declared threshold can refresh observation coverage during ball occlusion.
The ball-mask ablation disables that refresh while retaining identical event potentials. This
isolates changes to abstention from changes to latent state evidence. Output remains X outside
periods and after the unchanged three-second unsupported-observation limit.

## Information controls and limits

Shuffling/period-local shifting preserve ordinary-world tag counts, categories, widths and team
hints. They can still reveal prevalence and improve a weak model's prior; aligned-minus-control
comparisons are therefore primary. Independent random tags use a fixed Poisson rate and are a
separate, non-count-matched null. On twins, one independently selected donor stream is shared
exactly across the opposing worlds for shuffled/shifted controls; random streams are also shared.
Those controls cannot discriminate the true world, irrespective of downstream confidence.

Twins hold all tracking observations fixed and alter hidden officiating/action cues. Informative
tags may now break the tracking-only ambiguity because the input space has changed. Shared
uninformative tags cannot: balanced target accuracy is bounded by 50%. Raw and temporal-X-filled
target scores are both reported to expose abstention effects. This is not a claim that real
Smart Tagging has independent information, accurate teams, or comparable error distributions.
