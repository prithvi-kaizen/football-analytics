# Inspection record

This is engineering inspection of tracking replays, not independent tactical annotation. No success/error labels were invented. The separate 18-row `outputs/review-queue.csv` leaves reviewer and tactical-label columns blank.

| Candidate | Inspection | Implication |
|---|---|---|
| `1996435-118-560893-10278`, E. Alagich, 17:06.8 | Animation shows the proposed link moving from P. Klimala to C. Hollman; measured zero-cover time is 0.0 s. The selected trio is detected over the measurement window, while other players can be extrapolated. | A continuous-cover candidate, not a verified successful tactical handoff. Included in the video by the manifest's deterministic rule. |
| `1996435-109-560893-9704`, E. Alagich, 16:09.4 | Replay and transfer details show a 1.9 s geometric gap and 1.8 s unassigned interval. Timeline distinguishes the two. The incoming confirmation frame has plausible cover, while earlier frames show zero cover. | Hysteresis delay and geometric gap are distinct quantities. This example cannot establish a communication failure. |
| `1996435-24-18573-2022`, J. Lolley, 03:21.2 | At confirmation the two best plausible scores differ by about 0.939 m-equivalent. The outgoing and incoming players are close to the attacker; the interface exposes the close-alternatives flag. | A sharp assignment label can conceal competing geometrically plausible options. No uniquely correct marker is adjudicated. |
| `1996435-137-25534-12511`, A. Ouahim, 20:50.1 | Viewer shows a 1.7 s geometric gap and shared-incoming flag for B. Vriends. The assignment export confirms independent choices allow shared defenders. | Shared responsibility estimates need contextual review. The flag is not proof that the defender is overloaded or at fault. |

The video contains a continuous and a gap example selected as the first lexicographic ID within held-out, detected-trio, sufficiently long, non-ambiguous, non-shared strata. This favors visual inspectability. It is not random or representative of all candidates.

Engineering verification independently recomputed all 801 candidate gap measurements, all main operational counts and all 21,078 replay-frame bindings from exported CSV records. That reconciliation checks consistency of the implementation, not validity of the tactical construct.
