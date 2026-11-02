# Technical recommendation: gated Smart Tagging integration (design only)

This plan follows public DATA.md, RULES.md and EVALUATION.md at the pinned upstream commit.
No restricted XML was opened, requested or generated. No gated file-loading implementation is
included. Carry out any later integration only in a separate human-controlled environment that
Codex and hosted models cannot access; keep raw inputs, extracts and private logs there.

1. Copy reviewed source into that environment. Keep the official scorer unmodified and pin the
   appropriate optional loader dependencies there. The current lab's official adapter remains
   disabled; no environment variable points this lab at match assets.
2. A human-run adapter should call the supplied standard-library `starter/load_smart_tagging.py`
   loader or a separately pinned SportsCode XML loader. Preserve raw interval times, code and all
   tag pairs in local provenance. The supplied loader returns `start_s`, `end_s`, `start_frame`,
   `end_frame`, `code` and `tags`; feed only normalized in-memory PhaseInterval records to inference.
3. Convert tactical video seconds with `round(seconds * 25)` into half-open [start,stop) intervals.
   Do not subtract one (that correction belongs to participant ATD IDs, not Smart Tagging).
   Validate interval bounds and half compatibility without inventing an offset. Broadcast video
   has its own timeline and is unsupported by this plan.
4. Normalize tag keys and codes case-insensitively. Map source team names explicitly to H/A;
   preserve N/A as unknown. All throw-ins reportedly have unknown Team. A defending-team tag
   is not necessarily the possessor, and a phase interval is not a possession spell.
5. Confidence must remain unknown unless validated outside the competition labels. Actual XML
   does not supply the calibrated semantic probabilities assumed by the synthetic model. Remove
   duplicates using observable fields, retain conflicts and timing uncertainty, and cap evidence.
   Do not feed latent event IDs, correctness flags or inferred truth back into the model.
6. Initially enable only a reviewed SET PIECES/Type vocabulary. The hypothetical synthetic
   `stoppage signal` code is not promised by the official schema; **do not map unrelated phases
   into it**. A restart annotation is a window around an action, not an exact whistle timestamp.
   Absence of tags is no evidence of a stoppage or live play. Set all unvalidated channel weights
   to zero; tagless output must exactly reproduce the original hierarchy.
7. Before enabling fusion, validate category semantics, dependence on tracking, false positives,
   timing distributions and team errors on legitimately labelled other matches with match-level
   splits. Calibrate there if possible, freeze settings, then test counterexamples and shuffled,
   shifted, count-matched and tracking-only controls. No training/tuning on the public five-minute
   challenge labels or any hand labels/human-produced events about that competition match.
8. Compare the unchanged HMM, tagless hierarchy, aligned-tag fusion and disabled-tag operation
   locally. Report abstention-policy differences separately. Validate the final canonical CSV
   (199,319 rows, frame 0..199318, H/A/D/X) using the unchanged official validator. Any legitimate
   private evaluation results remain local and must not be sent into this chat.

The synthetic experiment supports only conditional engineering conclusions. Successful external
validation is required before recommending a nonzero real-data event weight. Do not transfer
synthetic probability assumptions or performance numbers into claims about the competition.
