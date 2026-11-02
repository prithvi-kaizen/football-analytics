# Challenge contract and engineering implications

Reviewed 2026-10-25 at official commit `f8f2629ff1e0985f81d7e59d8413678514ee1530`.
Sources: [official repository](https://github.com/metrica-sports/more-than-a-hack-2027).
Local files inspected: README.md, CHALLENGE.md, DATA.md, EVALUATION.md, RULES.md, FAQ.md,
SUBMISSION.md, games.py, starter/baseline.py, starter/load_atd.py,
starter/load_smart_tagging.py, evaluation/run_evaluation.py,
evaluation/possession_metrics.py and evaluation/validate_submission.py.
`official_manifest.json` pins their bytes and every other tracked upstream file.

## Task and input contract

Produce `frame,label` for all 199,319 tactical video frames at 25 fps, indexed 0..199318.
H and A mean home/away controlled possession with a live ball; D means ball out of play;
X means abstention. There is no contested class. Loose balls, deflections and aerial duels
retain the last controlling team until the opponent gains control. D separates possessions:
H-D-H is two home possessions. The reference is mechanically derived from corrected tracking;
that corrected tracking is not an allowed input.

Published graded ranges are inclusive: 11185..90651 and 110808..190197 (158,857 frames).
Outside them is ungraded. The second block includes 2,934 pre-kickoff dead frames;
its kickoff is frame 113742. Use published period ranges for masks, not a model prediction
of kickoff, and never add new constants inferred by watching particular competition frames.

Tactical ATD contains one record per video frame. `video_frame = frame_id - 1`.
The large per-half offsets in games.py refer to the *corrected reference's* separate counter,
not participant ATD. Some games.py docstrings still describe that older alignment context;
DATA.md and the public ATD loader clarify the distinction. Do not apply these offsets to ATD.

ATD positions are unit coordinates; physical geometry uses explicit dimensions.
games.py says 105.3 x 68 m; export metadata reportedly says 105 x 68 m. Choose and record the
source deliberately. Track slots (46 tactical slots for roughly 22 players) are fragmented
identities, not people; duplicate slots and gaps are expected. Roughly 41% of graded frames
lack a ball observation. Missing players/ball use NaN.

Smart Tagging is automatic, fallible phase evidence, not possession truth. It has title-case
tag columns, upper-case codes and team values including N/A. Intervals are timed in tactical
video seconds: round(seconds * 25), with half-open output from the supplied loader.
No assumption that a whole phase shares one possession is justified.
Homographies map unit pitch coordinates to image pixels; check validity and error.
Broadcast video has 164,488 frames and its own cuts/replays/timeline. There is no supplied
tactical alignment. This lab does not attempt synchronization or video processing.

## Scoring as implemented

The code is authoritative, including where comments or prose simplify it. We import it without
patching constants or functions.

- Ranking: mean same-team possession-spell F1 at temporal IoU thresholds 0.3, 0.4, 0.5,
  0.6 and 0.7. The implementation greedily consumes pairs in descending IoU order, with
  deterministic ties. This is not average precision and not a globally optimal assignment.
- First tie-break: unweighted frame F1 over H, A and D. A class absent from both prediction
  and truth contributes zero, so a short perfect single-class test scores 1/3 macroF1.
- Remaining tie-breaks: transition F1 at the loose tolerance (25 frames), then smaller mean
  absolute matched-transition latency, then filename. Transitions match one-to-one by destination
  label within 12/25 frames. Origin labels need not match by default.
- GT X frames are excluded from frame metrics. Prediction X is a frame miss. Before temporal
  scoring, prediction X is forward-filled within each contiguous non-X truth run, with leading
  X back-filled from the first known prediction. An entirely abstained run remains X. No
  fill crosses the halftime gap. Public truth has only one short graded run, not both full halves.
- Durations assume 25 fps in scorer code. Synthetic benchmarks enforce 25 fps. Fragmentation,
  predicted/true possession counts, D F1 and transition latency diagnose distinct errors.
- Optional bootstrap resamples segments for macroF1 and possessions for spellF1, with fixed
  random seeds. Full-match noise bands quoted upstream do not establish uncertainty on five
  public minutes or on these artificial scenarios.

Validation enforces row count, integer sequential frame indices, nonblank legal labels and
required column names. It tolerates case and surrounding spaces. Our writer emits the stricter
canonical two-column form. We also validate a synthetic full-length 199,319-row file.

## Existing baseline and reproducible sanity check

The supplied raw method assigns the nearest tracked player's team in *metres*, and outputs D
when it cannot assign a team. The smooth variants use centred windows of +/-25, +/-50 and
/-125 frames. The vote counts H and A only: D is output only if neither team appears in the
window. Ties choose H. It is not a three-class majority filter.

The four CSVs already ship in the repo. Without restricted tracking we can reproduce their
evaluation, but cannot regenerate the CSVs from original assets. This distinction is deliberate.

| Supplied file | Public macroF1 | Public spellF1 |
|---|---:|---:|
| baseline_raw | 0.5972 | 0.0378 |
| baseline_smooth25 | 0.6200 | 0.2868 |
| baseline_smooth50 | 0.6207 | 0.3256 |
| baseline_smooth125 | 0.5812 | 0.4242 |

These values were actually reproduced. They are pipeline sanity checks only. The organisers'
published full-match baseline floor (spellF1 0.2433) is their result, not an evaluation we ran.
The best public smoothing variant differs from the best documented full-match variant, which
reinforces why public labels must never select parameters or models.

## Constraints and opportunities

No public-label fitting/tuning, no private truth, no hand labels/corrections on this match,
and no other human-produced event/corrected/possession data about this match. External games
are allowed under their terms. Submission must be regenerated byte-for-byte by inspectable
code, with pinned dependencies and a short technical document. Official submission needs
the CSV, a public repository and technical document; no live leaderboard is promised.
Restricted match assets and reconstructible derivatives must not be redistributed or sent to
third-party hosted models. The user's policy here is stricter still: restricted assets remain
outside Codex's accessible directories and are not inspected by this agent at all.

Useful algorithmic directions are explicit missingness and observation quality, collective
features resilient to track switches, control confirmation instead of proximity flicker,
independent dead-ball evidence, uncertain restart/phase priors, and temporal segmentation.
None is established as an improvement on the competition by the work in this lab.
