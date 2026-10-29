# Executed pilot results

Data: SkillCorner Open Data, with PySport. All scores are model-derived proxies, not validated prevented passes.

The pre-specified hypothesis is **not supported** under the recorded criterion. No parameters were selected using the test results.

| Match | Eligible / possession starts | All players + ball detected | Missing ease among all starts |
| --- | ---: | ---: | ---: |
| Auckland FC vs Newcastle (1886347) | 442 / 990 | 0 | 80 |
| Brisbane FC vs Perth Glory (1925299) | 444 / 1054 | 0 | 118 |
| Sydney FC vs Adelaide United (1996435) | 412 / 1005 | 0 | 107 |

Exclusion counts and full tracking coverage are in `data_audit.json`. Categories above are missingness before eligibility filters, not an additional exclusion count.

## Held-out associations with provider passing difficulty

| Match | Joint labelled n | Geometry rho | Arrival rho | Difference | Paired phase-bootstrap 95% interval |
| --- | ---: | ---: | ---: | ---: | --- |
| 1925299 | 439 | 0.324 | 0.016 | -0.308 | [-0.413, -0.190] |
| 1996435 | 393 | 0.269 | 0.096 | -0.173 | [-0.275, -0.073] |
| Pooled | 832 | 0.293 | 0.062 | -0.230 | [-0.305, -0.153] |

The pooled bootstrap uses 433 provider possession-phase clusters and 1000 paired resamples stratified by match. These intervals condition on only two selected matches. They do not quantify between-match or league uncertainty. The alternate five-minute-block interval is [-0.2933777013393721, -0.16175315423587586].

Across 6337 candidate lanes at 856 held-out starts, 1554 are unblocked by geometry but have arrival obstruction >=0.5. This is model disagreement, not observed missed interceptions.

Mean detected-player fraction at eligible held-out starts: 69.6%. The all-22-players-and-ball-detected analysis has n=0; association is unavailable.

## Pressure and sensitivity

Unadjusted overall-pressure association: geometry rho=0.280, arrival rho=0.039 (joint n=832). Pressure is a separate provider-derived construct and not an obstruction label. No causal interpretation or pass-accuracy claim follows.

| Variant | n | Geometry rho | Arrival rho | Difference | Mean obstruction |
| --- | ---: | ---: | ---: | ---: | ---: |
| zero_velocity | 832 | 0.293 | 0.115 | -0.177 | 0.425 |
| ball_12 | 832 | 0.293 | 0.078 | -0.215 | 0.539 |
| ball_18 | 832 | 0.293 | 0.062 | -0.231 | 0.355 |
| defender_4 | 832 | 0.293 | 0.072 | -0.221 | 0.391 |
| defender_6 | 832 | 0.293 | 0.057 | -0.235 | 0.471 |
| reaction_0.4 | 832 | 0.293 | 0.160 | -0.132 | 0.550 |
| reaction_1.0 | 832 | 0.293 | 0.014 | -0.279 | 0.329 |
| width_0.75 | 832 | 0.259 | 0.062 | -0.197 | 0.435 |
| width_1.5 | 832 | 0.323 | 0.062 | -0.261 | 0.435 |
| spacing_0.25 | 832 | 0.293 | 0.067 | -0.226 | 0.437 |
| spacing_1.0 | 832 | 0.293 | 0.041 | -0.252 | 0.429 |
| target_range_30 | 831 | 0.306 | 0.182 | -0.125 | 0.329 |

Sensitivity rows are descriptive alternatives, not uncertainty intervals or a parameter search for a publishable winner. The target-range sensitivity changes the target population and may change the eligible denominator. All-detected filtering cannot remove extrapolation bias when it yields no data.

## What the pilot establishes

The source loader, finite corridor geometry, past-only arrival heuristic, per-defender ablations and temporal replays execute on real open data. The test reports agreement with dependent provider categories. It does not validate perception, intent, pass completion, tackles avoided, prevented passes or a player ranking. DLO remains a mathematical marginal-obstruction indicator.

Read `../docs/methodology.md` and `../docs/limitations.md` before reusing any figure. Exact CSV rows and JSON receipts accompany this report.
