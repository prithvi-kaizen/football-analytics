"""Strict source validation and past-only snapshot construction."""
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

EASE = {'very_easy': 1, 'easy': 2, 'medium': 3, 'hard': 4, 'very_hard': 5}
PRESSURE = {'no_pressure': 1, 'low_pressure': 2, 'medium_pressure': 3, 'high_pressure': 4, 'very_high_pressure': 5}
SUFFIXES = ('match.json', 'dynamic_events.csv', 'phases_of_play.csv', 'tracking_extrapolated.jsonl')


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def verify_sources(root, match_id):
    lock = json.loads((root / 'data/source-lock.json').read_text())
    entries = {e['file']: e for e in lock['files']}
    receipts = []
    for suffix in SUFFIXES:
        name = f'{match_id}_{suffix}'
        p = root / 'data/raw' / name
        if name not in entries or not p.exists() or sha256(p) != entries[name]['sha256']:
            raise ValueError(f'Missing or corrupt pinned source: {name}; run scripts/fetch_data.py')
        receipts.append(entries[name])
    return receipts


def load_tables(root, mid):
    meta = json.loads((root / f'data/raw/{mid}_match.json').read_text())
    events = pd.read_csv(root / f'data/raw/{mid}_dynamic_events.csv', low_memory=False)
    phases = pd.read_csv(root / f'data/raw/{mid}_phases_of_play.csv')
    required = {'event_id', 'match_id', 'frame_start', 'frame_end', 'period', 'player_id', 'team_id', 'event_type', 'phase_index'}
    if not required.issubset(events):
        raise ValueError('Missing event schema')
    if events.event_id.isna().any() or events.event_id.duplicated().any():
        raise ValueError('Event IDs missing or duplicated within match')
    for df in [events, phases]:
        if not df.match_id.eq(mid).all() or not df.period.isin([1, 2]).all():
            raise ValueError('Match or period mismatch')
        if df[['frame_start', 'frame_end']].isna().any().any() or (df.frame_start > df.frame_end).any():
            raise ValueError('Invalid interval')
    for period, group in phases.groupby('period'):
        g = group.sort_values('frame_start')
        if (g.frame_start.to_numpy()[1:] < g.frame_end.to_numpy()[:-1]).any():
            raise ValueError('Overlapping phase intervals')
    for field, mapping in [('passing_option_ease_start', EASE), ('overall_pressure_start', PRESSURE)]:
        present = events[field].notna()
        if not events.loc[present, field].isin(mapping).all():
            raise ValueError(f'Unknown category in {field}')
        if not events.loc[present, field].map(mapping).eq(events.loc[present, field + '_id']).all():
            raise ValueError(f'Category/ID disagreement: {field}')
        if events.loc[present, 'event_type'].ne('player_possession').any():
            raise ValueError('Provider schema changed: labels on non-possession rows')
    return meta, events, phases


def read_tracking(path, meta, wanted):
    """Audit every source record, retain only requested snapshots and their histories."""
    with Path(path).open() as source:
        return _read_tracking(source, meta, wanted)


def _read_tracking(source, meta, wanted):
    keep, audit = {}, Counter()
    audit['source_frames'] = 0
    last = -1
    known = {p['id'] for p in meta['players']}
    periods = {}
    for number, line in enumerate(source, 1):
        try:
            rec = json.loads(line)
            frame = rec['frame']
            if not isinstance(frame, int) or frame <= last:
                raise ValueError('Frames must increase strictly')
            last = frame
            audit['source_frames'] += 1
            period = rec['period']
            if period is None:
                audit['null_period_frames'] += 1
                continue
            if period not in (1, 2):
                raise ValueError('Unsupported period')
            periods.setdefault(period, [frame, frame, 0])
            periods[period][1] = frame
            periods[period][2] += 1
            seen = set()
            valid = []
            for p in rec['player_data']:
                pid = p['player_id']
                if pid in seen:
                    raise ValueError('Duplicate player in frame')
                seen.add(pid)
                if pid not in known:
                    audit['unknown_player_rows'] += 1
                    continue
                xy = [p.get('x'), p.get('y')]
                if any(v is None for v in xy) or not np.isfinite(xy).all() or abs(xy[0]) > meta['pitch_length']/2+5 or abs(xy[1]) > meta['pitch_width']/2+5:
                    audit['invalid_coordinate_rows'] += 1
                    continue
                valid.append(p)
                audit['player_rows'] += 1
                audit['detected_player_rows'] += p.get('is_detected') is True
            if len(valid) != 22:
                audit['frames_without_22_players'] += 1
            ball = rec.get('ball_data') or {}
            audit['ball_detected_frames'] += ball.get('is_detected') is True
            audit['unknown_carrier_frames'] += (rec.get('possession') or {}).get('player_id') is None
            if frame in wanted:
                rec['player_data'] = valid
                keep[frame] = rec
        except (TypeError, KeyError, ValueError) as exc:
            raise ValueError(f'Tracking line {number}: {exc}') from exc
    audit['periods'] = periods
    return keep, dict(audit)


@dataclass
class State:
    frame: int
    period: int
    carrier: int
    team: int
    sign: int
    ball: np.ndarray
    ids: np.ndarray
    teams: np.ndarray
    xy: np.ndarray
    velocity: np.ndarray
    detected: np.ndarray
    ball_detected: bool
    target_indices: np.ndarray
    defender_indices: np.ndarray


def phase_at(phases, frame, period):
    rows = phases[(phases.period == period) & (phases.frame_start <= frame) & (frame < phases.frame_end)]
    if len(rows) > 1:
        raise ValueError('Many-to-many phase join')
    return None if rows.empty else rows.iloc[0]


def snapshot(records, meta, phases, frame, carrier, team, config):
    """Returns (state, exclusion reason); no provider ease/outcome fields accepted."""
    rec = records.get(int(frame))
    if rec is None:
        return None, 'missing_tracking'
    period = rec['period']
    phase = phase_at(phases, frame, period)
    if phase is None or phase.team_in_possession_id != team:
        return None, 'no_matching_in_play_phase'
    owner = rec.get('possession') or {}
    group = 'home team' if team == meta['home_team']['id'] else 'away team'
    if owner.get('player_id') != carrier or owner.get('group') != group:
        return None, 'carrier_not_confirmed'
    players = sorted(rec['player_data'], key=lambda p: p['player_id'])
    lookup = {p['id']: p for p in meta['players']}
    if len(players) != 22:
        return None, 'incomplete_22_player_context'
    ids = np.array([p['player_id'] for p in players])
    teams = np.array([lookup[i]['team_id'] for i in ids])
    if carrier not in ids or lookup[carrier]['team_id'] != team or sum(teams == team) != 11:
        return None, 'invalid_team_context'
    xy = np.array([[p['x'], p['y']] for p in players], dtype=float)
    ball_data = rec.get('ball_data') or {}
    b = [ball_data.get('x'), ball_data.get('y')]
    if any(v is None for v in b) or not np.isfinite(b).all():
        return None, 'missing_ball'
    ball = np.array(b, dtype=float)
    ci = int(np.flatnonzero(ids == carrier)[0])
    if np.linalg.norm(ball - xy[ci]) > config['max_ball_carrier_distance_m']:
        return None, 'ball_far_from_carrier'
    if ball_data.get('z') is None or not np.isfinite(ball_data['z']) or ball_data['z'] > 1.0:
        return None, 'ball_not_low'
    if abs(ball[0]) > meta['pitch_length']/2 or abs(ball[1]) > meta['pitch_width']/2:
        return None, 'ball_off_pitch'
    defenders = np.flatnonzero(teams != team)
    window = config['velocity_window_frames']
    history = []
    for f in range(frame-window, frame+1):
        past = records.get(f)
        if past is None or past['period'] != period:
            return None, 'missing_past_velocity_window'
        ps = {p['player_id']: p for p in past['player_data']}
        if any(int(ids[i]) not in ps for i in defenders):
            return None, 'missing_defender_history'
        history.append([[ps[int(ids[i])]['x'], ps[int(ids[i])]['y']] for i in defenders])
    hist = np.array(history)
    if (np.linalg.norm(np.diff(hist, axis=0), axis=2)*config['fps'] > config['max_raw_speed_mps']).any():
        return None, 'implausible_defender_jump'
    velocity = np.zeros_like(xy)
    velocity[defenders] = (hist[-1]-hist[0])/(window/config['fps'])
    sign = 1 if meta['home_team_side'][period-1] == 'left_to_right' else -1
    if team != meta['home_team']['id']:
        sign *= -1
    expected = 'left_to_right' if sign == 1 else 'right_to_left'
    if phase.attacking_side != expected:
        raise ValueError('Phase/metadata attacking direction mismatch')
    signed_x = xy[:, 0]*sign
    offside_line = max(0.0, ball[0]*sign, np.sort(signed_x[defenders])[-2])
    distance = np.linalg.norm(xy-ball, axis=1)
    candidate = (teams == team) & (ids != carrier) & (distance >= config['min_pass_m']) & (distance <= config['max_pass_m'])
    candidate &= np.array([lookup[i]['player_role']['acronym'] != 'GK' for i in ids])
    candidate &= (abs(xy[:, 0]) <= meta['pitch_length']/2) & (abs(xy[:, 1]) <= meta['pitch_width']/2)
    candidate &= signed_x <= offside_line
    targets = np.flatnonzero(candidate)
    if len(targets) < config['minimum_targets']:
        return None, 'too_few_targets'
    return State(int(frame), period, int(carrier), int(team), sign, ball, ids, teams, xy, velocity,
                 np.array([p.get('is_detected') is True for p in players]),
                 ball_data.get('is_detected') is True, targets, defenders), None


def start_states(root, mid, config):
    receipts = verify_sources(root, mid)
    meta, events, phases = load_tables(root, mid)
    possessions = events[events.event_type == 'player_possession'].copy()
    wanted = {f for frame in possessions.frame_start for f in range(int(frame)-config['velocity_window_frames'], int(frame)+1)}
    records, audit = read_tracking(root / f'data/raw/{mid}_tracking_extrapolated.jsonl', meta, wanted)
    states, exclusions = [], Counter()
    for e in possessions.itertuples():
        s, why = snapshot(records, meta, phases, int(e.frame_start), int(e.player_id), int(e.team_id), config)
        if s is None:
            exclusions[why] += 1
        else:
            states.append((e, s))
    audit.update(match_id=mid, match=f'{meta["home_team"]["short_name"]} vs {meta["away_team"]["short_name"]}',
                 date=meta['date_time'], event_rows=len(events), event_columns=len(events.columns),
                 event_types=events.event_type.value_counts().to_dict(), possession_rows=len(possessions),
                 missing_ease=int(possessions.passing_option_ease_start.isna().sum()),
                 missing_pressure=int(possessions.overall_pressure_start.isna().sum()),
                 eligible_starts=len(states), exclusions=dict(exclusions),
                 all_detected_starts=int(sum(s.detected.all() and s.ball_detected for _, s in states)))
    return meta, states, audit, receipts
