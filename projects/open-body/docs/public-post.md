# LinkedIn draft

We talk about receiving on the half-turn constantly. I wanted to test what shoulder orientation can actually tell us at reception.

I built Open Body using two free SkillCorner / PySport matches: 25 Hz body pose, 10 Hz tracking and player-possession events. The target was narrow: a successful pass gaining at least 5 metres within 2 seconds.

On 647 held-out receptions, adding orientation reduced log loss from 0.5751 to 0.5599. The reverse split also improved. But both conditional uncertainty intervals include zero, and the midfield-only check is mixed. The pilot criterion was not met.

One useful engineering finding: exact clock alignment did not guarantee that pose and tracking positions agreed. I added consistency gates and kept the exclusions visible.

The project includes reproducible Python modules, full-match coverage audits, per-event predictions, a 2D/3D viewer and a 30-second demo. Shoulder direction is a proxy; this does not measure scanning or prove a causal benefit.

Data credit: SkillCorner and PySport. I’ve kept the code, audits and demo together for review.

# X draft

Open Body: a two-match SkillCorner/PySport pilot. Adding shoulder orientation lowered held-out log loss from 0.5751 to 0.5599, but uncertainty includes zero and midfield results are mixed. Reproducible code + 2D/3D viewer. Preliminary, not causal.

# Publication note

These drafts are not posted. Add the actual public project link only after publishing the code/artifacts. Do not claim a player ranking, causal gain, validated half-turn label or measured head scanning. The LinkedIn numbers describe the chronological matched-sample comparison, not the all-eligible baseline.
