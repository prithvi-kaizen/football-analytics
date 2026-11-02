# Motion v2: exploratory diagnostics

Fixed seeds 301–305; 5 mechanisms; unchanged models. Five trials per case are too few for robust generalization claims. Intervals resample whole trials. Undefined D precision is omitted, never scored as perfect.

| Mechanism | Method | SpellF1 mean [95% trial interval] | MacroF1 | D recall |
| --- | --- | --- | --- | --- |
| ordinary | nearest | 0.093 [0.088, 0.099] | 0.543 | 0.000 |
| ordinary | state_machine | 0.778 [0.665, 0.889] | 0.664 | 0.099 |
| ordinary | hmm | 0.459 [0.365, 0.514] | 0.658 | 0.114 |
| ordinary | hierarchical | 0.552 [0.536, 0.560] | 0.609 | 0.000 |
| stationary_live | nearest | 0.115 [0.107, 0.123] | 0.546 | 0.000 |
| stationary_live | state_machine | 0.777 [0.660, 0.885] | 0.627 | 0.099 |
| stationary_live | hmm | 0.466 [0.363, 0.534] | 0.622 | 0.114 |
| stationary_live | hierarchical | 0.552 [0.536, 0.560] | 0.608 | 0.000 |
| contested | nearest | 0.094 [0.085, 0.105] | 0.543 | 0.000 |
| contested | state_machine | 0.773 [0.661, 0.887] | 0.663 | 0.099 |
| contested | hmm | 0.459 [0.368, 0.514] | 0.660 | 0.114 |
| contested | hierarchical | 0.552 [0.536, 0.560] | 0.609 | 0.000 |
| player_gaps | nearest | 0.085 [0.069, 0.098] | 0.530 | 0.000 |
| player_gaps | state_machine | 0.772 [0.667, 0.887] | 0.656 | 0.092 |
| player_gaps | hmm | 0.450 [0.367, 0.513] | 0.660 | 0.117 |
| player_gaps | hierarchical | 0.552 [0.536, 0.560] | 0.608 | 0.000 |
| identity_switches | nearest | 0.093 [0.088, 0.099] | 0.543 | 0.000 |
| identity_switches | state_machine | 0.778 [0.667, 0.887] | 0.664 | 0.099 |
| identity_switches | hmm | 0.459 [0.367, 0.514] | 0.658 | 0.114 |
| identity_switches | hierarchical | 0.552 [0.536, 0.560] | 0.609 | 0.000 |

These scores must not be pooled with the historical Phase 1/2 benchmarks. The new generator changes the data-generating process. No public Metrica or competition labels enter this evaluation.

Largest noise-free player step: legacy 63.091 m versus v2 0.280 m at 25 fps. This checks kinematic continuity, not realism or tactical validity.
