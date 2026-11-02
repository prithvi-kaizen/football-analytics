# Suggested public post (not sent)

What if a defensive midfielder's most important contribution is the pass the opposition never even tries?

I tested two ways to score a passing lane: a 1 m geometric corridor and an approximate defender-arrival model.

The simpler model had stronger agreement with SkillCorner's passing-difficulty categories. Across 832 labelled starts in two pipeline-held-out A-League matches, Spearman rho was 0.293 for geometry and 0.062 for arrival time. The paired difference was -0.230, with a phase-cluster bootstrap 95% interval of [-0.305, -0.153]. The improvement hypothesis was not supported.

These categories use the same tracking inputs. Agreement does not validate prevented passes. None of the eligible held-out starts had all players and the ball detected on camera, so the strict observed-only check was unavailable.

The project includes the code, source audit, sensitivity tests and a pitch replay showing the Defensive Lane Obstruction proxy. Data: SkillCorner Open Data, with PySport.

## Short X version

Can a defender obstruct a pass before it is tried? On 832 starts from two held-out matches, geometry agreed more with provider difficulty than arrival times (rho 0.293 vs 0.062). Shared-input proxies, not validated prevented passes. Data: SkillCorner + PySport.
