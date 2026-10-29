# Publication drafts

These are drafts, not published posts. Attach the 32-second video and a repository link when publishing; no hosted repository URL for this new project is assumed here.

## LinkedIn

When an attacker moves across the defensive block, which defender becomes the plausible cover?

I built a small tracking-data project to retrieve candidate marking handoffs. It combines attacker-defender proximity graphs with relative motion, a local team-structure reference and temporal hysteresis.

On one held-out SkillCorner match, it retrieved 306 candidates, including 44 with a geometric coverage gap of at least 0.4 seconds. Identity changes fell from 8.34 to 2.63 per eligible attacker-minute, while the method assigned a defender on only 53.6% of eligible frames.

The tradeoff matters. Short assignment runs increased from 54 to 62, so my pre-specified hypothesis of fewer short runs failed. Synthetic tests with known geometric changes passed, but real tactical accuracy still needs independent labels.

The video shows a continuous-cover candidate and a temporary geometric gap. These are candidate handoffs. Tracking positions cannot reveal what either defender was instructed to do, and broadcast extrapolation can create or hide apparent gaps.

Data: SkillCorner Open Data, MIT licence. Python code, reproducible configuration, sensitivity checks and the full candidate catalogue accompany the project.

## X thread

1/ I built a Python tool to retrieve candidate marking handoffs from free SkillCorner tracking. On one held-out match: 306 candidates, 44 with geometric gaps >=0.4 s. The animation shows how the covering-defender estimate changes.

2/ Identity changes fell from 8.34 to 2.63 per attacker-minute, with assignment available on 53.6% of eligible frames. Short runs increased 54 to 62, so that hypothesis failed. Fewer switches do not prove better tactical accuracy.

3/ These are candidate handoffs, not known coaching assignments. Synthetic geometric tests passed; real tactical labels are still needed. Extrapolated tracking can create or hide gaps. Data: SkillCorner Open Data (MIT).

## Claim checks

Every numeric claim above comes from `outputs/results.json` or `synthetic-results.json`. No improvement in real marking accuracy, prevention of goals, defender intent, communication failure or match outcome is claimed. The user's suggested communication-failure hook is a hypothesis that this dataset cannot verify, so it is not presented as a result.
