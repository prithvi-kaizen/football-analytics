# Limitations and claims boundary

1. **No responsibility labels.** Proximity, motion and local structure cannot establish a team's instructions, communication, defensive intent or error. Real handoff precision/recall and successful-transfer rates are unknown.
2. **Partial observation.** Broadcast-derived extrapolation affects 42.1% and 34.2% of valid player observations in the two inspected files. Empty intervals are common. A gap can be created or hidden by estimated coordinates, even when the three highlighted players are detected.

   Empty-period-frame counts include out-of-play intervals and should not be read as an in-play missing-tracking rate.
3. **Inferred context.** Phase and possession labels conflict at thousands of frames. We exclude known conflicts, unknown possession and inconsistent periods. Surviving context can still be wrong, and provider inference may use future information unavailable to a live analyst.
4. **Small, selected sample.** Two cached matches were selected for practical availability, not randomly. Only one match is an algorithm holdout. Both are men's A-League games from 2024/25; no claim extends to other competitions or women's/youth football.
5. **Hand-built coverage geometry.** Distance, goal-side and predicted-distance thresholds are uncalibrated. Ball height, passing lanes, body orientation, offside, pressing triggers, positional roles and actual defensive zones are not modeled. The second-deepest outfield defender is only a back-line proxy.
6. **Local structural instability.** A defender's nearest teammates and local median depth may change abruptly. Ablation assesses output sensitivity but cannot prove that this structural penalty represents real tactical organization.
7. **Asymmetric abstention.** Nearest defender assigns every eligible frame. The proposed method abstains frequently. Fewer switches partly reflect that difference, so lower switching is not an accuracy improvement.
8. **Hysteresis delays and fragmentation.** Stability can suppress true brief transfers or miss them at a segment boundary. Release conditions can produce short assigned runs. The held-out hypothesis of fewer short runs failed and must remain in publication copy.
9. **Retrospective candidates.** Stable incoming runs and the movement window use later observations for event confirmation. The state estimator is causal, but candidate retrieval is offline; it is not real-time prediction.
10. **Independent choices, shared defenders.** More than one attacker can select the same defender. The shared flag does not estimate that defender's ability to cover both or establish a tactical conflict.
11. **Synthetic truth is geometric.** The simulation favors simple local coverage and Gaussian perturbations. Its high event metrics cannot be transferred to real matches. Identity errors, camera switches, large correlated errors and tactical ambiguity are not realistically simulated.
12. **Uncertainty scope.** Phase bootstrap covers resampling variability within the selected held-out match. Neighboring phases may remain dependent. With one held-out match, between-match uncertainty cannot be estimated credibly.
13. **Illustrative animation.** Replays display 5 Hz from the original 10 Hz analysis and stop at eligibility boundaries. Short gaps can fall between displayed samples. The MP4 stretches source time to half speed and contains no broadcast video or expert adjudication.

## Necessary next validation

Have at least two independent football analysts annotate a match-separated sample of candidate and non-candidate windows using synchronized video when licensed access permits. Predefine transfer, continuous cover, gap, unclear and observation-insufficient labels. Measure inter-rater agreement, preserve disagreement and ambiguous cases, and report event precision/recall with match-cluster uncertainty. Keep that annotation set separate from threshold selection. Until then, use this tool for retrieval and hypothesis generation, not player ranking or defensive blame.
