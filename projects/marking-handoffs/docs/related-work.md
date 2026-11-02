# Related methods and contribution

Primary sources inspected on 28 October 2026. These five references delimit the contribution; this is not a claim of a new marking-network concept.

| Source | Established idea | Relation to this implementation |
|---|---|---|
| [Chacoma, Kuperman & Billoni, 2022, *Complexity emerges in measures of the marking dynamics in football games*](https://arxiv.org/abs/2207.09992), published in Physical Review E | Temporal bipartite proximity networks between opponents; collective marking dynamics and synthetic motion experiments. | Establishes that proximity graphs and simulation are prior art. Here the unit is an individual candidate transfer with explicit uncovered intervals and abstention. |
| [Fernández & Bornn, 2018, *Wide Open Spaces*](https://www.lukebornn.com/papers/fernandez_ssac_2018.pdf), Sloan paper | Motion-aware spatial influence and space occupation/generation. | Motivates including relative movement; a proximity switch alone does not establish territorial control or responsibility. This pilot does not reproduce or calibrate a pitch-control probability. |
| [Laurie Shaw / Friends of Tracking, *Metrica_PitchControl.py*, 2020](https://github.com/Friends-of-Tracking-Data-FoTD/LaurieOnTracking/blob/master/Metrica_PitchControl.py) | Public implementation of reaction-time and travel-time pitch control drawing on Spearman's work. | A practical precedent for inspectable tracking code. Our scores remain metres-equivalent heuristics, not interception probabilities; no source code is copied. |
| [Groom et al., 2026, *A Machine Learning Framework for Off Ball Defensive Role and Performance Evaluation in Football*](https://arxiv.org/html/2601.00748v1), preprint | Covariate-dependent HMM inferring time-varying man-marking and zonal roles for corners, with role-conditioned counterfactual evaluation. | Temporal inference of responsibility is already researched. Our open-play pilot is deliberately simpler, requires no private labels/model fitting and abstains from defensive-value attribution. No superiority to this model is tested. |
| [Calero-Sanz et al., 2026, *Beyond marking networks in soccer: Coordination, similarity and entropy*](https://doi.org/10.1016/j.chaos.2026.118819), Chaos, Solitons & Fractals | Publisher abstract describes proximity/directional bipartite networks, coordination projections and entropy on 99 matches. | Confirms close prior work on marking networks. Only the publisher abstract was accessible; thresholds and detailed validation were not inspected. No detailed replication claim is made. |

## Modest original contribution

The contribution is an open, reproducible engineering package for **candidate handoff retrieval** on broadcast tracking: a validated nearest-defender baseline, causal heuristic scoring, hysteresis with explicit missing-data resets, gap measurement separate from assignment delay, observation-quality flags, deterministic review clips and a searchable catalogue. It tests robustness against known geometric changes and reports sensitivity, failure cases and within-match uncertainty. It does not introduce marking graphs, discover coaches' instructions, prove communication failures, or establish a new state of the art.

## What remains unknown

No reviewed source supplies tactical ground truth for these A-League matches. Even apparently continuous coverage may be intentional zonal positioning or incidental proximity. A small independently annotated study with explicit ambiguous/unknown labels, agreement statistics and match-level splits would be required for meaningful tactical detection accuracy. A label-free role model or calibrated pitch-control surface would be a later comparison, not a justified addition to this first pilot.
