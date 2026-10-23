"""Deterministic corner definitions, temporal attribution and partial-frame geometry."""
from __future__ import annotations

import math
import re
from statistics import mean

import numpy as np
import pandas as pd

from .data import DataError, unique_records


def name(obj):
    return obj.get('name', '') if isinstance(obj, dict) else ''


def timestamp_seconds(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{2}:\d{2}:\d{2}(?:\.\d+)?', value):
        raise DataError(f"Invalid period timestamp: {value!r}")
    h, m, s = map(float, value.split(':'))
    if m >= 60 or s >= 60:
        raise DataError(f"Invalid period timestamp: {value!r}")
    return h * 3600 + m * 60 + s


def xy(value):
    if not isinstance(value, (list, tuple)) or len(value) < 2:
        return None
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in value[:2]):
        return None
    x, y = map(float, value[:2])
    return (x, y) if 0 <= x <= 120 and 0 <= y <= 80 else None


def canonical(point, origin):
    """Reflect only across pitch width; actors already attack toward x=120."""
    return (point[0], 80 - point[1]) if origin[1] > 40 else tuple(point)


def is_corner(event):
    return event.get('period', 0) in (1, 2, 3, 4) and (
        name(event.get('type')) == 'Pass' and name(event.get('pass', {}).get('type')) == 'Corner'
        or name(event.get('type')) == 'Shot' and name(event.get('shot', {}).get('type')) == 'Corner')


def delivery(event, short_threshold=15):
    p = event.get('pass', {})
    if name(event.get('type')) == 'Shot':
        return 'Direct shot'
    length = p.get('length')
    if length is None:
        a, b = xy(event.get('location')), xy(p.get('end_location'))
        if a and b:
            length = math.dist(a, b)
    # Explicitly a geometric heuristic, not an inferred tactical intent.
    if isinstance(length, (int, float)) and math.isfinite(length) and 0 <= length <= short_threshold:
        return 'Short'
    technique = name(p.get('technique'))
    if technique in ('Inswinging', 'Outswinging', 'Straight'):
        return technique
    return 'Other / unknown'


def restart(event):
    typ = name(event.get('type'))
    return typ == 'Pass' and name(event.get('pass', {}).get('type')) in (
        'Corner', 'Free Kick', 'Throw-in', 'Throw In', 'Goal Kick', 'Kick Off') or (
        typ == 'Shot' and name(event.get('shot', {}).get('type')) in ('Corner', 'Free Kick', 'Penalty', 'Kick Off'))


def terminal(event):
    typ = name(event.get('type'))
    if typ in ('Half End', 'Offside', 'Injury Stoppage', 'Referee Ball-Drop') or event.get('out'):
        return True
    if typ in ('Foul Committed', 'Foul Won'):
        key = 'foul_committed' if typ == 'Foul Committed' else 'foul_won'
        return not event.get(key, {}).get('advantage', False)
    if typ == 'Shot' and name(event.get('shot', {}).get('outcome')) == 'Goal':
        return True
    return False


def corner_sequence(events, start, horizon=15):
    if horizon <= 0:
        raise ValueError('horizon must be positive')
    corner = events[start]
    t0 = timestamp_seconds(corner['timestamp'])
    team = corner['team']['id']
    sequence, shots = [], []
    observed = False
    reason = 'recording ended'
    for offset, event in enumerate(events[start:]):
        if event['period'] != corner['period']:
            observed, reason = True, 'period ended'
            break
        dt = timestamp_seconds(event['timestamp']) - t0
        # Overlapping annotated actions can be indexed after a later-starting event.
        # Keep provider order, but never attribute a negative-time action.
        if dt < -1e-6:
            continue
        if offset and dt > horizon:
            observed, reason = True, 'time window ended'
            break
        if offset and restart(event):
            observed, reason = True, 'next restart'
            break
        if offset and (event.get('possession') != corner.get('possession') or
                       event.get('possession_team', {}).get('id', team) != team):
            observed, reason = True, 'possession ended'
            break
        sequence.append({'event_id': event['id'], 'index': event['index'], 'elapsed': round(dt, 3),
                         'event': name(event.get('type')), 'team': name(event.get('team')),
                         'player': name(event.get('player')),
                         'detail': name(event.get('shot', {}).get('outcome')) or name(event.get('pass', {}).get('outcome'))})
        if name(event.get('type')) == 'Shot' and event.get('team', {}).get('id') == team:
            shots.append((event, dt))
        if terminal(event):
            observed, reason = True, 'stoppage or ball out'
            break
    # Positive outcomes remain observed even if later recording is incomplete.
    label = True if shots else False if observed else None
    xgs = [s.get('shot', {}).get('statsbomb_xg') for s, _ in shots]
    return {'shot_created': label, 'shots': len(shots), 'first_shot_seconds': shots[0][1] if shots else None,
            'first_shot_id': shots[0][0]['id'] if shots else None,
            'xg_sum': sum(xgs) if all(isinstance(v, (int, float)) and math.isfinite(v) for v in xgs) else None,
            'goal': any(name(s.get('shot', {}).get('outcome')) == 'Goal' for s, _ in shots),
            'stop_reason': reason, 'sequence': sequence}


def polygon_area(poly):
    return abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(poly, poly[1:] + poly[:1]))) / 2 if len(poly) >= 3 else 0.0


def clip_box(poly, bounds=(102, 18, 120, 62)):
    """Sutherland-Hodgman intersection with the standardized penalty area."""
    for axis, edge, greater in [(0, bounds[0], True), (0, bounds[2], False), (1, bounds[1], True), (1, bounds[3], False)]:
        result = []
        if not poly:
            return []
        for a, b in zip(poly, poly[1:] + poly[:1]):
            a_in = a[axis] >= edge if greater else a[axis] <= edge
            b_in = b[axis] >= edge if greater else b[axis] <= edge
            if a_in:
                result.append(a)
            if a_in != b_in:
                t = (edge - a[axis]) / (b[axis] - a[axis])
                result.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))
        poly = result
    return poly


def inside_polygon(point, poly):
    if len(poly) < 3:
        return False
    x, y = point
    inside = False
    for a, b in zip(poly, poly[1:] + poly[:1]):
        cross = (x-a[0])*(b[1]-a[1]) - (y-a[1])*(b[0]-a[0])
        if abs(cross) < 1e-7 and min(a[0],b[0])-1e-7 <= x <= max(a[0],b[0])+1e-7 and min(a[1],b[1])-1e-7 <= y <= max(a[1],b[1])+1e-7:
            return True
        if (a[1] > y) != (b[1] > y) and x < (b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:
            inside = not inside
    return inside


SPATIAL = ['attackers_box', 'defenders_box', 'attackers_near', 'attackers_far',
           'attacker_mean_x', 'attacker_mean_y', 'attacker_spread_y',
           'defender_mean_x', 'nearest_defender_mean', 'box_visible_fraction', 'defenders_per_100_visible_units']


def spatial_features(frame, origin):
    result = {key: None for key in SPATIAL}
    result.update(has_360=frame is not None, visible_players=None, invalid_players=0)
    if frame is None or origin is None:
        return result
    players = []
    for p in frame.get('freeze_frame', []):
        loc = xy(p.get('location'))
        if loc is None or not isinstance(p.get('teammate'), bool):
            result['invalid_players'] += 1
            continue
        players.append({**p, 'location': canonical(loc, origin)})
    result['visible_players'] = len(players)
    atk = [p['location'] for p in players if p['teammate'] and not p.get('actor') and not p.get('keeper')]
    defence = [p['location'] for p in players if not p['teammate']]  # keeper included, documented flag caveat
    box = lambda p: 102 <= p[0] <= 120 and 18 <= p[1] <= 62
    result.update(attackers_box=sum(map(box, atk)), defenders_box=sum(map(box, defence)),
                  attackers_near=sum(box(p) and p[1] < 36 for p in atk),
                  attackers_far=sum(box(p) and p[1] > 44 for p in atk))
    if atk:
        result.update(attacker_mean_x=mean(p[0] for p in atk), attacker_mean_y=mean(p[1] for p in atk),
                      attacker_spread_y=float(np.std([p[1] for p in atk])))
    if defence:
        result['defender_mean_x'] = mean(p[0] for p in defence)
    if atk and defence:
        result['nearest_defender_mean'] = mean(min(math.dist(a, d) for d in defence) for a in atk)
    raw = frame.get('visible_area', [])
    if len(raw) >= 6 and len(raw) % 2 == 0 and all(isinstance(v, (float, int)) and math.isfinite(v) for v in raw):
        poly = [canonical((raw[i], raw[i+1]), origin) for i in range(0, len(raw), 2)]
        area = polygon_area(clip_box(poly))
        if area > 0:
            result['box_visible_fraction'] = min(1.0, area / 792)
            result['defenders_per_100_visible_units'] = 100 * sum(box(p) and inside_polygon(p, poly) for p in defence) / area
    return result


def extract_match(match, events, frames, horizon=15, short_threshold=15):
    unique_records(events, 'id')
    unique_records(events, 'index')
    unique_records(frames, 'event_uuid')
    events = sorted(events, key=lambda e: e['index'])
    for event in events:
        timestamp_seconds(event['timestamp'])
    by_frame = {f['event_uuid']: f for f in frames}
    rows, details = [], {}
    for i, event in enumerate(events):
        if not is_corner(event):
            continue
        outcome = corner_sequence(events, i, horizon)
        origin = xy(event.get('location'))
        frame = by_frame.get(event['id'])
        rows.append({'corner_id': event['id'], 'match_id': match['match_id'], 'tournament': match['tournament'],
            'match_date': match['match_date'], 'match': f"{match['home_team']['home_team_name']} vs {match['away_team']['away_team_name']}",
            'team': name(event['team']), 'team_id': event['team']['id'], 'taker': name(event.get('player')),
            'period': event['period'], 'timestamp': event['timestamp'], 'minute': event.get('minute'),
            'corner_side': ('Top' if origin[1] <= 40 else 'Bottom') if origin else 'Unknown',
            'delivery': delivery(event, short_threshold), 'recorded_technique': name(event.get('pass', {}).get('technique')) or None,
            **{k: v for k, v in outcome.items() if k != 'sequence'}, **spatial_features(frame, origin)})
        details[event['id']] = {'event': event, 'frame': frame, 'sequence': outcome['sequence']}
    return pd.DataFrame(rows), details


def summary(frame, by=('tournament', 'delivery')):
    valid = frame[frame.shot_created.notna()]
    if valid.empty:
        return pd.DataFrame(columns=[*by, 'corners', 'shots_created', 'rate', 'low', 'high'])
    out = valid.groupby(list(by), dropna=False, observed=True).shot_created.agg(corners='size', shots_created='sum').reset_index()
    n, successes, z = out.corners, out.shots_created.astype(int), 1.959963984540054
    out['shots_created'] = successes
    out['rate'] = successes / n
    center = (out.rate + z*z/(2*n)) / (1+z*z/n)
    margin = z * np.sqrt(out.rate*(1-out.rate)/n + z*z/(4*n*n)) / (1+z*z/n)
    out['low'], out['high'] = center-margin, center+margin
    return out
