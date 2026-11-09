# Validation record

Recorded 9 November 2026. The project is integrated into the static portfolio build. On 9 November 2026 it was published on an isolated GitHub branch, subsequently renamed `one-step-behind` at the user’s request and deployed as a standalone Vercel preview. Public access was enabled with explicit user approval. The portfolio production site and unrelated workspace changes are unchanged; no social post has been sent.

## Analytical checks

- 17 targeted unittest cases pass: coordinate direction, peer median geometry, 3/4/5-player line eligibility, stationarity, persistent lag, recovery, censoring, translation invariance, short fluctuation rejection, missing positions, extrapolation-only exclusion, phase/possession reset, duplicate frames, unknown identities and out-of-bounds coordinates.
- All six cached source files pass pinned upstream LFS SHA-256/size or Git blob SHA-1 checks. A fresh public download of held-out metadata independently matches SHA-256 `f54179645d3c3f308a7094086283277f2a7c99da5f3919302e622cbd82f9d065`. Full tracking was reused from the verified local cache; it was not downloaded again.
- 12,307 independent scalar `statistics.median` gap checks pass across all exported step search windows. This checks geometry, not tactical correctness.
- A second verifier bypasses the analysis loader and compares all 2,926 replay player coordinates and flags directly to raw JSONL across 133 exported frames. Every coordinate/observation flag agrees. Reference medians and individual gaps also agree to export precision.
- All primary step counts, durations and baseline counts reconcile with the event catalogues. Exclusive eligibility reasons sum to two team-scans of each match. Configuration hashes match.
- Development ran before held-out detection. No frozen thresholds were changed after seeing results. Sensitivity is reported separately. The serialization repair converted NumPy integer endpoints to Python integers; it changed no thresholds or detector behaviour.
- Primary result: 0/49 development and 0/44 holdout. Candidate recovery/gap-duration distributions are unavailable. No tactical accuracy is reported.

## Browser checks

The local built explorer was opened in the Codex in-app browser. Its default Adelaide replay renders real players, line membership, the median reference, bracket and linked gap chart. Tested all three selections, play/pause, scrubbing to the 3.53 m frame, previous/next frame, tolerance changes, all four evidence disclosures and both themes. Playback visibly advanced source frames. Arrow keys changed both sliders; Enter toggled theme; focus had a visible approximately 3px outline. Browser error/warning log was empty.

Responsive tests used requested viewport overrides 1360×1000 and 390×844. The browser's measured CSS document widths were 1222 and 341 respectively. Desktop scrollWidth equalled clientWidth. A mobile research-table overflow was found and fixed by constraining grid children; the final mobile scrollWidth and clientWidth both equal 341. Desktop light/dark and mobile light renderings were visually inspected. Mobile pitch numbers are small at full-pitch scale; the accompanying line table provides readable player names, shirt numbers, flags and gaps.

Text contrast checks passed: muted light text 5.63:1, amber on pale pitch 5.25:1, muted dark text 7.22:1, blue on dark pitch 6.26:1. Layout and text inspected in screenshots; no automated claim about all possible browser/font combinations is made. The optional human-tone audit helper is absent from the installed skill; the publication drafts received a manual language pass.

## Video and deployment checks

FFprobe confirms H.264, 1600×900, 30 fps, 32.000 seconds. Five rendered checkpoint PNGs were generated; the peak-gap frame was visually inspected for typography, pitch and annotation placement. The same verified coordinates drive the explorer and video. The video is silent, uses held real samples rather than interpolated positions, discloses slow replay/held peak and makes no candidate-recovery claim. The source MIT notice is beside the MP4.

The complete root portfolio build passed all existing project integrity checks: Pressing Trap Detector, Invisible Runner, Pass Decision Lab, Rest Defence Analyzer and Possession Danger. The new `/one-step-behind/` route builds using standard-library Python only. Existing results were not edited. Root README and build registration were edited narrowly on top of the user's pre-existing modifications; vercel.json was not changed by this work.

## Antislop delivery gate

One line per applicable rule, with concrete evidence. These checks describe the local deliverable, not production deployment.

- R-02 PASS: authored explorer text has no em dashes; numerical minus signs have mathematical meaning.
- R-03 PASS: final measured mobile document and scroll width both 341px; grid overflow repaired.
- R-17 PASS: numbers bind to frozen JSON results, raw-verified replay positions or independently computed displacement.
- R-18 PASS: no testimonials or fictional people appear; player identities come from source metadata.
- R-23 PASS: pitch and tracking animation explicitly requested; no logos, avatars or invented asset claims added.
- R-24 PASS: portfolio root, evidence anchor, real repository and packaged article/data/video destinations exist in the built release.
- R-25 PASS: four limiting foreground/background pairs checked with the skill contrast tool, all ≥5.25:1.
- R-26 PASS: every button/select/slider was exercised and changed its intended visible state.
- R-27 PASS: loading/error branches and explicit no-primary-candidate state are implemented; real replay rendered successfully.
- R-28 PASS: no FAQ or generic filler section exists.
- R-32 PASS: native sliders accept arrows, theme accepts Enter, visible focus outline observed; controls remain native focusable elements.
- R-33 PASS: UI authored in viewer/index.html and revised directly; no runtime source/CSS patch script.
- R-34 PASS: light and dark desktop views inspected; theme switches foregrounds, pitch, chart, controls and surfaces together.
- R-35 PASS: root build passed; every explorer control and disclosure exercised, error log empty; packaged routes checked in build.
- R-36 PASS: no fabricated security, performance or customer claims.
- R-37 PASS: design follows user-requested portfolio consistency; Design Read and dials recorded in DESIGN.md before generation.
- R-38 PASS: all match content derives from the two verified sources; negative result is prominent.
- R-01 PASS: no gradients or glow; amber bracket has the stated measurement purpose.
- R-04 PASS: no decorative icon library or generic icons.
- R-06 PASS: Georgia editorial title follows the existing portfolio direction; system sans supports dense labels, reason recorded.
- R-07 PASS: no decorative background grid; football pitch markings encode actual geometry.
- R-08 PASS: one direction arrow labels normalized forward movement, not decoration on actions.
- R-09 PASS: no capsule badges or repeated eyebrow headline.
- R-10 PASS: no glassmorphism.
- R-12 PASS: no component shadows.
- R-13 PASS: no glows.
- R-14 PASS: no uniform feature-card grid; pitch and evidence have distinct roles.
- R-19 PASS: only user-initiated coordinate playback animates; motion serves the football question.
- R-22 PASS: all illustration is requested real-coordinate pitch geometry.
- Liveliness/dials PASS: ENERGY 1 / RHYTHM 2 / MOTION 2 declared and reflected in restrained controls, varied pitch/evidence structure and deliberate replay.
- Liveliness/focus PASS: pitch dominates the workbench; amber bracket repeats the gap measurement in the linked trace.
- Liveliness/space PASS: whitespace separates question, replay and evidence rather than filling cards.
- Liveliness/identity PASS: tactical-board palette, median line and measurement bracket form the repeated motif.
- Liveliness/read PASS: DESIGN.md was written before explorer generation with user direction and reasons.
- C-1 PASS: colour, type, layout and motion each have written content-based reasons in DESIGN.md.
- C-2 PASS: every authored control is functional and was exercised.
- C-3 PASS: selection, replay, gap trace, line table and evidence each answer a specified user need.
- C-4 PASS: light/dark, narrow/desktop and keyboard checks passed; empty/error branches exist.
- C-5 PASS: no invented testimonial, statistic or match event.
- R-05 PASS: pitch workbench followed by research evidence, no generic marketing template.
- R-11 PASS: controls use 4px corners, pitch 6px, player circles have semantic meaning; no pill treatment throughout.
- R-15 PASS: action labels specify Play, frame steps, theme, evidence and investigation.
- R-16 PASS: no AI marketing buzzwords or hype claims.
- R-20 PASS: football pitch, player flags and peer-depth chart are specific to this investigation.
- R-21 PASS: default light follows portfolio direction; complete optional dark view is implemented.
- R-29 PASS: neutral base, slate and blue team colours, one amber measurement accent.
- R-30 PASS: no imitation of a generic SaaS/Linear/Vercel interface.
- R-31 PASS: visual decisions each have an explicit one-line rationale in DESIGN.md.

## Video opening revision, 9 November 2026

The 32-second MP4 now opens at real source frame 41228 (match clock 66:59.8), with a 3.53 m peer-median gap and the exact overlay “3.53m behind the line. But was he actually late?”. At four seconds it explicitly cuts back to the step start, then replays the real sequence with a forward-displacement counter. The peak comparison still reports +1.76 m for Talladira and +2.36 m for peers. No tracking coordinates or analysis thresholds were changed.
