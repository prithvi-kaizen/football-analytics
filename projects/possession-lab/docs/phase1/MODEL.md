# Hierarchical baseline specification

All quantities below are fixed engineering choices. There is no parameter fitting, trained
calibration, or claim that the local heads equal true football conditional probabilities.

For each frame, the live logit adds:

- 1.5 times ball speed / 3 m/s, clipped to [0,1], only for an observed ball;
- 0.4 times collective player speed / 1 m/s, clipped to [0,1], multiplied by observed slot coverage;
- 0.8 times proximity (1 - minimum player distance / 3 m, clipped to [0,1]), available only
  with ball/team geometry and multiplied by observation reliability;
- minus 0.35 if the existing stationary-duration feature is at least 1.2 s and the ball is observed;
- minus 4 times reliability if an observed ball is outside the physical pitch.

NaN speed/proximity contributions are zero evidence. A missing ball does not contribute static
evidence. The explicitly unsafe missing-as-static ablation changes only that last availability
assumption on the stationary term; other masks and the output abstention rule are retained.

The home-given-live logit uses (away nearest distance - home nearest distance) / 1.5 m,
clipped to [-4,4], multiplied by proximity and reliability; it is zero without both distances.
The logistic transform gives local heads q = live probability and r = home given live.
Marginalizing unknown quantities here means neutral evidence, not a learned missingness model.
Player motion can still provide weak evidence while the ball is absent.

Joint states are LH, LA, DH, DA. Per-frame likelihood-ratio potentials are
`[4*q*r, 4*q*(1-r), 2*(1-q), 2*(1-q)]`, raised to power 0.2 to temper correlated repeated
window features. The reference measure is neutral live/owner priors (0.5 each). Missing all
measurements gives four potentials equal to 1, rather than making D more probable simply
because live probability is split across two teams. These are positive model potentials,
not a separately validated generative likelihood of raw positions.

Transitions factor as `T_live_dead ⊗ T_owner`. Live-to-dead and dead-to-live rates are 1/18 s
and 1/6 s, converted exactly to a discrete 2-state continuous-time Markov transition at dt=1/fps.
Owner has a symmetric rate 1/12 s. Its latent process continues while dead and represents a
memory prior, not physically meaningful possession during stoppages. All four initial states
have probability 1/4; every period resets. The no-duration variant replaces only the live/dead
transition with uniform rows; no-continuity replaces only owner transitions with uniform rows.
These are memoryless geometric sojourn priors, not minimum-duration constraints or an HSMM.

Log-space Viterbi returns the joint MAP path. Scaled forward/backward returns smoothed state
marginals, from which P(live) and P(home|live) are derived. Tests compare both outputs against
exhaustive enumeration on a small chain. Live states output H/A and both dead states output D.
Post-processing outputs X outside periods, after 3 seconds without a reliable observed ball,
and throughout wholly unobserved periods. Abstention does not change the internal posterior.
The official scorer charges raw X at frame level and fills it for temporal metrics as usual.

The old coverage proxy is measured per track slot. Fragmented slot counts, correlated tracking
errors, rare outliers, moving dead balls and unobserved referee decisions are substantial limits.
Posterior certainty under these assumptions does not prove real-world identifiability or
calibration. No Smart Tagging channel is used; its future contract is separate.
