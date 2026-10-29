# Validation record and antislop delivery gate

Scope: the smallest local research version. Analytical validity and UI craftsmanship are different questions. All engineering checks below passed; the football improvement hypothesis did **not** pass. There is no independent prevented-pass validation.

## Analytical and source checks

- PASS: 12 pinned source files verified by SHA-256 before scoring; source URLs, sizes, licence and revision are retained in `data/source-lock.json` and `outputs/provenance.json`.
- PASS: fresh-access endpoint check identified Git LFS pointers at raw tracking URLs; all three tracking URLs now use GitHub media endpoints. A 1925299 media prefix was verified as actual JSONL. Full network re-download was unnecessary because cached payload hashes match the pinned lock.
- PASS: four geometry/ablation tests and a real development baseline gate ran before the arrival method was implemented. The saved baseline has 442 eligible starts, nonconstant values in [0,0.875] and the frozen configuration hash.
- PASS: 22 Python tests, including physical/directional behaviour, phase boundaries, past-only history, no inferred missing carrier, offside, duplicate-frame rejection and bootstrap pairing. Executed-output tests separately reconstruct rank correlations in pure Python, reconcile all exclusion waterfalls and check no double-counted marginal totals.
- PASS: both holdouts scored with the recorded configuration. Paired phase-cluster and five-minute-block bootstrap results use 1,000 resamples, not independent frame resampling. Twelve descriptive sensitivity variants and the unavailable strict visibility subset are retained.
- PASS: output figures and text trace to exact CSV/JSON records. Negative primary results remain in README, results, viewer, video and public draft. No post was sent or site deployed.

## Browser evidence

`outputs/browser-validation.json` records the Chromium run. It covers all three selects, previous/next, keyboard range, play/pause, freeze, corridor toggle, exact-table disclosure, results JSON download, skip link and four local documentation links. No uncaught page errors occurred. Layouts were checked at 320, 390, 640, 820, 1060 and 1365 px, plus 200% root text size at 390 px. Separate documents exercised malformed and empty embedded data. Screenshots are saved as `outputs/viewer-desktop.png` and `outputs/viewer-mobile.png` and were visually inspected. No physical-device, assistive-technology or full screen-reader audit is claimed.

## Delivery gate

Each line reports a rule or closely related rule group. Evidence for control behaviour is the browser receipt; exact contrast ratios and portable checksums are in `outputs/verification.json`.

### Hard gates

- R-02 PASS: rendered viewer text contains no em dash; the release verifier checks the built HTML.
- R-03 PASS: no document horizontal overflow at six checked widths; tables are contained and mobile controls stack.
- R-17 PASS: every displayed statistic comes from executed results/replay JSON or the documented configuration.
- R-18 PASS: no testimonials, avatars or invented people appear.
- R-23 PASS: the explicitly requested pitch visualization, quantitative figures and demo use verified data; no marketing imagery or logo assets were added.
- R-24 PASS: four local documentation destinations return HTTP 200; external source links identify the verified publisher and PySport.
- R-25 PASS: text/mark palette ratios were computed, including pitch backgrounds; text pairs exceed 4.5:1 and control/pitch boundaries exceed 3:1.
- R-26 PASS: every select, button, checkbox, range and disclosure has executed behaviour recorded in the browser receipt.
- R-27 PASS: loading text precedes embedded-data parsing; separate empty and malformed exports show actionable messages.
- R-28 PASS: no FAQ exists.
- R-32 PASS: controls use native keyboard behaviour and visible 3 px focus outlines; keyboard range navigation was exercised. No modal or focus trap exists.
- R-33 PASS: all UI behaviour and styles are authored in `viewer.html`; the builder only binds the single JSON data token.
- R-34 PASS: fixed light appearance follows the documented prior project direction; no untested theme is offered.
- R-35 PASS: built viewer ran in Chromium; all controls and local destinations were exercised; desktop/mobile screenshots were inspected.
- R-36 PASS: no security, customer or performance claims appear.
- R-37 PASS: `DESIGN.md` carries the prior Invisible Runner direction; the user chose during-construction filtering in this chat.
- R-38 PASS: names, shirt numbers, coordinates, labels and scores come from verified inputs. No invented tactical scene or label is presented.

### Purpose gates

- R-01 PASS: paper/ink, teal attack and rust defence follow written semantic reasons in `DESIGN.md`; no gradients are used.
- R-04 PASS: no decorative icons or emoji are used.
- R-06 PASS: Georgia headings and system body text follow the existing editorial project direction; numeric controls remain readable.
- R-07 PASS: pitch markings represent field geometry; no decorative page grid or technical texture exists.
- R-08 PASS: no ornamental button arrows exist.
- R-09 PASS: no capsule badges or duplicate eyebrow labels exist.
- R-10 PASS: no glass or backdrop blur exists.
- R-12 PASS: no floating card shadows exist.
- R-13 PASS: no glows or decorative status lights exist.
- R-14 PASS: no feature-card grid exists; pitch, timeline, exact table and paired interval plot serve distinct analytical tasks.
- R-19 PASS: playback is explicitly initiated, stops at the final frame and pauses when the document hides; no decorative motion exists.
- R-22 PASS: no stock or generated illustration exists; graphics show the requested mechanism and evidence.

### Liveliness

- Dials PASS: ENERGY 1 / RHYTHM 2 / MOTION 1 are declared in `DESIGN.md` and reflected in a restrained page with functional replay motion.
- Focal point PASS: a full-width football pitch leads the workbench; controls precede it and the evidence comparison follows.
- Whitespace PASS: separate replay, metrics and evidence sections make the reading sequence visible without ornamental cards.
- Accent PASS: rust identifies defenders and the selected lane; teal identifies attack/current availability, both with shapes/line styles as redundant encodings.
- Identity PASS: the repeated finite corridor, actual shirt numbers and current/frozen comparison are specific to the passing-lane question.
- Design Read PASS: documented before viewer construction and based on the adjacent project's existing direction.

### Craftsmanship and consistency

- C-1 / R-31 PASS: reasons for colour, typography, layout, spacing and functional animation are written in `DESIGN.md`.
- C-2 PASS: browser receipt records the actual action for every shipped control.
- C-3 / R-05 PASS: sections follow source evidence and the football question; no generic hero/cards/testimonials template exists.
- C-4 PASS: native controls, empty/error states, six widths and enlarged text were checked; physical-device and screen-reader limitations are explicit.
- C-5 PASS: no fictional statistics, people or causal conclusions are presented.
- R-11 PASS: small consistent control radii; no pill-shaped component system.
- R-15 PASS: buttons specify replay, frame movement and results download actions.
- R-16 PASS: no marketing buzzwords or inflated results language in the viewer.
- R-20 PASS: the workbench is composed around finite lanes, actual tracking and a failed improvement test.
- R-21 PASS: fixed light theme preserves the existing user-directed editorial style.
- R-29 PASS: paper/ink neutrals plus teal/rust semantic colours; no rainbow palette.
- R-30 PASS: no commercial product layout or visual identity was cloned.

## Publication check

The public draft keeps the user's proposed question and uses short factual paragraphs. One relevant user-authored writing reference was inspected privately for tone; it is not retained in this repository. The optional human-tone lint script was absent from its installed skill folder, so the draft received a manual phrase/fact review. Every number is generated in `publication.py`; the short X variant is provided separately. Neither draft implies independent football validation.

## Reproducibility receipt

`scripts/verify_release.py` reruns the analytical tests, validates the browser receipt, computes contrast, verifies the 30-second H.264 file and records source/code/config/output hashes in `outputs/verification.json`. This is an engineering receipt, not a statistical-validity certificate. Browser screenshots, exported figures and sampled video frames were inspected visually. Raw tracking is excluded from version control; upstream data retains its own MIT notice.
