# Live-demo correctness audit

Audited 2026-11-01 at https://football-analytics-self.vercel.app/possession-lab/.
The initial served release matched commit `5e75768`; this audit also clarifies
three UI descriptions while preserving models, fixtures, scores and history.

## Verdict

The checks found no numerical or data-integrity mismatch. The software's published
synthetic predictions and metrics agree with fresh native execution. This does not
establish real-match possession accuracy: the public Metrica clips have no trusted
possession labels here, and the simulator remains simplified.

## Evidence

| Check | Result |
| --- | --- |
| Served assets | All 36 HTTP responses were 200; SHA-256 matched the reviewed release, including Python and numerical packages |
| Fresh native inference | All 304 model prediction sequences and metric sets matched served fixtures exactly, including both public samples |
| Independent metric reconstruction | Eight fields recomputed for each of 276 synthetic model outputs, all matched |
| Fields independently checked | MacroF1, spellF1, D precision/recall, predicted/true spell counts, graded frames and abstentions |
| Coordinate/feature check | Nearest distances independently reconstructed; maximum discrepancy 0.001612 m, within rounding tolerance for millimetre-rounded exports |
| Observability | Both worlds have identical full tracking; no-evidence/shared-null target accuracy stays at or below 50%; all six pair summaries recalculated |
| Public samples | Both retain null truth and null accuracy for all 14 models; browser suppresses metric tables |
| Native tests | 170 Python tests pass |
| Frontend request tests | Four Node tests pass: deduplication, retry, timeout and bounded fixture names |
| Historical integrity | All 34 official source files and 408 frozen Phase 1 files unchanged |

The metric reconstruction used separate confusion-count and run/IoU calculations,
not the explorer's metric helper. Its X policy matched the official documented
policy: ignore ground-truth X, count predicted X as a frame miss, and fill X within
graded runs for temporal scoring. No competition labels were fitted or tuned.

Reproduce the independent metric/geometry checks after the standard-library
website build:

```sh
python scripts/audit_fixture_metrics.py --data dist/data --output outputs/audit/metrics.json
```

This command needs the project’s NumPy environment. It does not import the official
scorer or explorer metric helper. Its input is the explicit public/synthetic release
fixture directory.

Machine-readable evidence: [asset hashes](live-audit/assets.json),
[independent calculations](live-audit/independent_metrics.json),
[native inference parity](live-audit/native_parity.json).

## Browser checks

Browser Python loaded and ran all 14 models with a non-default request:
seed 321, contested mechanism, gap starting at 20 s lasting 8 s, noise 0.18 m,
random ball loss 0.2. Every displayed metric row agreed with a fresh native run
to the displayed precision. Browser Python 3.13.2/NumPy 2.2.5 differs from native
Python 3.14.2/NumPy 2.5.4. Full served-fixture label parity was checked separately;
this is not a claim that every possible cross-runtime request is byte-identical.

Playback advanced frames; pause, stepping and end-of-clip inspection worked.
Switching to clean tracking while a previous computation ran kept the newly
selected view intact. Both public samples showed no accuracy table. The static
paired example showed 50.0% without evidence, 92.6% with the illustrative noisy
independent cues, then 50.0% with shared null tags. The invisible no-evidence pair
also showed 50.0%. The browser error log was empty in these checks.

## Presentation issues clarified

1. **Observation weight, not calibrated confidence.** The feature combines visible
   ball, coverage over tracking slots and an implausible-speed penalty. Sample 1
   includes 14 slots per team but only 11 appear in the excerpt. Inactive substitute
   columns lower this heuristic even if all on-pitch players are visible. The UI
   now calls it an observation weight and states this limitation. Its values and
   all original model calculations remain unchanged.
2. **Paired timelines display World A.** World B's selected-model prediction appears
   below its pitch; the pair score uses both worlds. This is now stated next to
   the timeline to avoid implying that one event-model row represents both worlds.
3. **Halftime qualification.** Research temporal models reset at the break. The
   unchanged reference majority-vote windows can span it. The frame inspector now
   makes the same distinction already made by the methodology.

## Limits that remain

- Correctly implementing a model does not make its possession estimates correct
  on a real match. No trusted real possession labels were available for this audit.
- HMM and hierarchy decode offline, so future observations can affect earlier
  frames. They are not evaluated as causal broadcast systems.
- A high spellF1 can coexist with unknown frames because temporal scoring fills X.
  The default HMM and hierarchy each abstain on 75 graded frames; the original
  state machine abstains on 141. The UI reports the raw X states.
- Web scenarios are single scripted examples. Phase 1 report means use 12 trials
  per scenario with independently varied schedules/layouts. Those means should not
  be read as the displayed demo score for one fixture.
- Synthetic event cues are a hypothetical information source. Their benefit is
  conditional on the simulator's sensor assumptions and does not demonstrate
  equivalent information in real Smart Tagging exports.

No restricted match assets, footage, manual match labels or private logs were used.
