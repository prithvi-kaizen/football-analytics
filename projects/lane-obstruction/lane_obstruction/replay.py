"""Development-only examples; fixed target identities and defender-state ablations."""
from dataclasses import replace
import json
import numpy as np
from .data import load_tables, read_tracking, snapshot
from .experiment import scores, write_json


def build_replays(root, development, cfg):
    meta, starts = development
    mid = meta['id']
    _, events, phases = load_tables(root, mid)
    # Earliest eligible longer possessions; never selected for a flattering metric.
    candidates = [(e, s) for e, s in starts if e.frame_end-e.frame_start >= 30][:60]
    wanted = {f for e, _ in candidates for frame in range(int(e.frame_start), min(int(e.frame_end), int(e.frame_start)+50)+1, 5)
              for f in range(frame-cfg['velocity_window_frames'], frame+1)}
    records, _ = read_tracking(root/f'data/raw/{mid}_tracking_extrapolated.jsonl', meta, wanted)
    examples = []
    names = {p['id']: p['short_name'] for p in meta['players']}
    for e, initial in candidates:
        frames = []
        targets = initial.ids[initial.target_indices]
        defender_ids = initial.ids[initial.defender_indices]
        for frame in range(initial.frame, min(int(e.frame_end), initial.frame+50)+1, 5):
            s, why = snapshot(records, meta, phases, frame, initial.carrier, initial.team, cfg)
            if s is None or not np.array_equal(s.ids, initial.ids):
                break
            # Fix target identities to keep changes free of target-set composition effects.
            ti = np.array([int(np.flatnonzero(s.ids == pid)[0]) for pid in targets])
            s = replace(s, target_indices=ti)
            geo, team, marginal, individual, margins = scores(s, cfg)
            frozen_xy, frozen_velocity = s.xy.copy(), s.velocity.copy()
            frozen_xy[s.defender_indices] = initial.xy[initial.defender_indices]
            frozen_velocity[s.defender_indices] = initial.velocity[initial.defender_indices]
            frozen = replace(s, xy=frozen_xy, velocity=frozen_velocity)
            frozen_team = scores(frozen, cfg)[1]
            frames.append(dict(frame=frame, t=(frame-initial.frame)/cfg['fps'],
                xy=s.xy.round(3).tolist(), ball=s.ball.round(3).tolist(), detected=s.detected.tolist(), ball_detected=s.ball_detected,
                geometry=geo.tolist(), obstruction=team.tolist(), marginal=marginal.tolist(),
                individual=individual.round(6).tolist(), margins_s=margins.round(6).tolist(),
                frozen_obstruction=frozen_team.tolist(),
                defender_state_effect=(team-frozen_team).tolist()))
        if len(frames) < 7:
            continue
        start_period = next(p['start_frame'] for p in meta['match_periods'] if p['period'] == initial.period)
        examples.append(dict(event_id=e.event_id, match_id=mid, period=initial.period,
            clock_seconds=(initial.period-1)*2700+(initial.frame-start_period)/10,
            carrier=initial.carrier, attacking_team=initial.team, attack_sign=initial.sign,
            ids=initial.ids.tolist(), teams=initial.teams.tolist(), names=[names[i] for i in initial.ids],
            numbers=[next(p['number'] for p in meta['players'] if p['id'] == i) for i in initial.ids],
            target_ids=targets.tolist(), target_names=[names[i] for i in targets],
            defender_ids=defender_ids.tolist(), defender_names=[names[i] for i in defender_ids],
            frames=frames))
        if len(examples) == 3:
            break
    if not examples:
        raise ValueError('No valid development replay; do not invent one')
    write_json(root/'outputs/replays.json', dict(match=f'{meta["home_team"]["short_name"]} vs {meta["away_team"]["short_name"]}',
        length=meta['pitch_length'], width=meta['pitch_width'], config=cfg, examples=examples,
        selection='First three eligible chronological development possessions with >=3 seconds of valid replay',
        replay_sampling_hz=2, scoring_history_hz=10,
        warning='Fixed initial target identities for temporal comparison; scores are uncalibrated proxies.'))
