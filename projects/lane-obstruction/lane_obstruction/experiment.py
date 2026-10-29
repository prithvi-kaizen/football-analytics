"""Frozen protocol: baseline gate, holdout evaluation, sensitivity and audit exports."""
from dataclasses import replace
import json
from pathlib import Path
import platform
import subprocess
import sys

import numpy as np
import pandas as pd

from .arrival import arrival_obstruction
from .baseline import corridor_obstruction, marginal_obstruction
from .data import EASE, PRESSURE, sha256, start_states
from .evaluation import association, bootstrap, spearman


def scores(state, cfg, moving=True):
    b = corridor_obstruction(state.ball, state.xy[state.target_indices], state.xy[state.defender_indices], cfg['corridor_halfwidth_m'], cfg['endpoint_buffer_m'])
    m, margins = arrival_obstruction(state.ball, state.xy[state.target_indices], state.xy[state.defender_indices], state.velocity[state.defender_indices], cfg, moving)
    baseline, _ = marginal_obstruction(b)
    team, marginal = marginal_obstruction(m)
    return baseline, team, marginal, m, margins


def row_for(e, s, cfg, mid, moving=True):
    geometry, arrival, marginal, individual, margins = scores(s, cfg, moving)
    return dict(match_id=mid, event_id=e.event_id, frame=s.frame, period=s.period,
                phase=f'{s.period}:{e.phase_index}',
                time_block=f'{s.period}:{s.frame//3000}',
                carrier_id=s.carrier, targets=len(s.target_indices),
                ease=EASE.get(e.passing_option_ease_start), pressure=PRESSURE.get(e.overall_pressure_start),
                geometry=float(geometry.mean()), arrival=float(arrival.mean()),
                detected_fraction=float(s.detected.mean()), ball_detected=s.ball_detected,
                all_detected=bool(s.detected.all() and s.ball_detected),
                strong_disagreement_lanes=int(np.sum((geometry == 0) & (arrival >= .5))),
                total_lanes=len(arrival)), marginal, individual


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def run(root, config_path):
    cfg = json.loads(config_path.read_text())
    gate_path = root/'outputs/baseline_validation.json'
    if not gate_path.exists():
        raise ValueError('Run scripts/validate_baseline.py before the proposed method')
    gate = json.loads(gate_path.read_text())
    if gate['status'] != 'passed' or gate['config_sha256'] != sha256(config_path):
        raise ValueError('Baseline gate failed or config changed: revalidate baseline')
    rows, defenders, audits, source_receipts, states_by_match = [], [], [], [], {}
    for mid in cfg['development_matches']+cfg['held_out_matches']:
        meta, states, audit, receipts = start_states(root, mid, cfg)
        states_by_match[mid] = (meta, states)
        for e, s in states:
            row, marginal, individual = row_for(e, s, cfg, mid)
            rows.append(row)
            for i, di in enumerate(s.defender_indices):
                defenders.append(dict(match_id=mid, event_id=e.event_id, frame=s.frame,
                                      defender_id=int(s.ids[di]), mean_individual_obstruction=float(individual[:, i].mean()),
                                      dlo=float(marginal[i]), targets=len(s.target_indices)))
        audits.append(audit); source_receipts.extend(receipts)
        print(f'{mid}: {len(states)} eligible of {audit["possession_rows"]} starts', flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(root/'outputs/possessions.csv', index=False)
    pd.DataFrame(defenders).to_csv(root/'outputs/defender_snapshots.csv', index=False)
    write_json(root/'outputs/data_audit.json', audits)
    held = df[df.match_id.isin(cfg['held_out_matches'])]
    per_match = {str(mid): bootstrap(g, cfg['bootstrap_repetitions'], cfg['seed']) for mid, g in held.groupby('match_id')}
    pooled = bootstrap(held, cfg['bootstrap_repetitions'], cfg['seed'])
    time_blocks = bootstrap(held, cfg['bootstrap_repetitions'], cfg['seed'], cluster='time_block')
    observed = bootstrap(held[held.all_detected], cfg['bootstrap_repetitions'], cfg['seed'])
    support = bool(all(r['delta_rho'] is not None and r['delta_rho'] > 0 for r in per_match.values())
                   and pooled['interval_95'] is not None and pooled['interval_95'][0] > 0)
    results = dict(hypothesis_supported=support, per_match=per_match, pooled=pooled,
                   time_block_sensitivity=time_blocks, all_detected=observed,
                   pressure_association=association(held, 'pressure'),
                   development=association(df[df.match_id.isin(cfg['development_matches'])]),
                   held_out_starts=len(held), held_out_lanes=int(held.total_lanes.sum()),
                   geometry_open_arrival_ge_half=int(held.strong_disagreement_lanes.sum()),
                   mean_player_detection_fraction=float(held.detected_fraction.mean()))
    write_json(root/'outputs/results.json', results)
    variants = [('zero_velocity', {}, False), ('ball_12', {'ball_speed_mps': 12}, True),
                ('ball_18', {'ball_speed_mps': 18}, True), ('defender_4', {'defender_speed_mps': 4}, True),
                ('defender_6', {'defender_speed_mps': 6}, True), ('reaction_0.4', {'reaction_s': .4}, True),
                ('reaction_1.0', {'reaction_s': 1.0}, True), ('width_0.75', {'corridor_halfwidth_m': .75}, True),
                ('width_1.5', {'corridor_halfwidth_m': 1.5}, True), ('spacing_0.25', {'sample_spacing_m': .25}, True),
                ('spacing_1.0', {'sample_spacing_m': 1.0}, True), ('target_range_30', {'max_pass_m': 30}, True)]
    sensitivity = []
    for name, changed, moving in variants:
        varied = dict(cfg, **changed); variant_rows = []
        for mid in cfg['held_out_matches']:
            for e, s in states_by_match[mid][1]:
                ti = s.target_indices[np.linalg.norm(s.xy[s.target_indices]-s.ball, axis=1) <= varied['max_pass_m']]
                if len(ti) < varied['minimum_targets']:
                    continue
                row, _, _ = row_for(e, replace(s, target_indices=ti), varied, mid, moving)
                variant_rows.append(row)
        v = pd.DataFrame(variant_rows)
        a = association(v)
        sensitivity.append(dict(variant=name, **a, mean_obstruction=float(v.arrival.mean())))
    pd.DataFrame(sensitivity).to_csv(root/'outputs/sensitivity.csv', index=False)
    versions = dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__)
    write_json(root/'outputs/provenance.json', dict(config=cfg, config_sha256=sha256(config_path),
               source_revision=json.loads((root/'data/source-lock.json').read_text())['revision'], sources=source_receipts,
               environment=versions, split_warning='Convenience sample; pipeline-held-out matches, previously cached by other projects',
               uncertainty_warning='Intervals condition on these matches; provider labels are dependent proxies'))
    from .replay import build_replays
    build_replays(root, states_by_match[cfg['development_matches'][0]], cfg)
    from .publication import write_report
    write_report(root, results, audits, sensitivity)
    return results
