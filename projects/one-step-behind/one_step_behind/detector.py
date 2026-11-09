"""Role-backed line geometry and conservative, gap-aware temporal retrieval."""
from __future__ import annotations
from collections import Counter
import numpy as np
from .data import attack_sign


def runs(mask):
    edges = np.diff(np.r_[False, np.asarray(mask, dtype=bool), False].astype(int))
    return [(int(a), int(b)) for a, b in zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1))]


def gaps(x):
    x = np.asarray(x)
    return np.stack([np.median(np.delete(x, i, axis=-1), axis=-1) - x[..., i]
                     for i in range(x.shape[-1])], axis=-1)


def line_geometry(depth, lateral, roles, cfg):
    """Indices of a metadata-backed last line; reject midfield cover/advanced backs."""
    line = np.flatnonzero(np.isin(roles, ['Central Defender', 'Full Back']))
    if not 3 <= len(line) <= 5 or sum(roles[line] == 'Central Defender') < 2:
        return None
    if set(np.argsort(depth, kind='stable')[:len(line)]) != set(line):
        return None
    if np.ptp(depth[line]) > cfg['max_spread_m'] or np.ptp(lateral[line]) < cfg['min_width_m']:
        return None
    return line


def eligible_segments(d, cfg, observed_only=False):
    meta, ids = d['metadata'], d['ids']
    players = {p['id']: p for p in meta['players']}
    roles = np.array([players[int(pid)]['player_role']['position_group'] for pid in ids])
    n = len(d['period'])
    active = np.zeros((n, len(ids)), dtype=bool)
    for j, pid in enumerate(ids):
        for interval in players[int(pid)]['playing_time']['by_period']:
            # Metadata end_frame is the last playing frame (substitution examples confirm).
            active[interval['start_frame']:interval['end_frame']+1, j] = True
    reasons = Counter()
    segments = []
    for tid in [meta['home_team']['id'], meta['away_team']['id']]:
        previous_key = None
        segment = None
        for fr in range(n):
            per, ph = int(d['period'][fr]), int(d['phase'][fr])
            reason = None
            if per not in [1, 2] or ph < 0:
                reason = 'no_consistent_phase'
            elif d['phase_team'][fr] != d['possession'][fr] or d['possession'][fr] < 0:
                reason = 'unknown_or_conflicting_possession'
            elif d['possession'][fr] == tid:
                reason = 'in_possession'
            elif d['phase_rows'][ph]['team_in_possession_phase_type'] not in cfg['allowed_phases']:
                reason = 'excluded_phase'
            elif not np.isfinite(d['ball'][fr]).all():
                reason = 'missing_ball'
            outfield = np.flatnonzero((d['teams'] == tid) & ~d['gk'] & active[fr])
            if reason is None and (len(outfield) != 10 or not d['clean'][fr, outfield].all()):
                reason = 'incomplete_outfield'
            if reason is None and observed_only and not d['detected'][fr, outfield].all():
                reason = 'extrapolated_outfield'
            if reason is None:
                sign = attack_sign(meta, tid, per)
                xy = d['xy'][fr, outfield] * sign
                chosen = line_geometry(xy[:, 0], xy[:, 1], roles[outfield], cfg)
                if chosen is None:
                    reason = 'ambiguous_line'
            if reason:
                reasons[reason] += 1
                previous_key, segment = None, None
                continue
            members = tuple(int(i) for i in outfield[chosen])
            key = (tid, per, ph, members)
            reasons['eligible'] += 1
            if key != previous_key:
                segment = dict(team=tid, period=per, phase=ph, members=members, start=fr, stop=fr+1, sign=sign)
                segments.append(segment)
            else:
                segment['stop'] = fr+1
            previous_key = key
    for s in segments:
        s['x'] = d['xy'][s['start']:s['stop'], s['members'], 0] * s['sign']
        s['detected'] = d['detected'][s['start']:s['stop'], s['members']]
    return segments, dict(reasons)


def step_windows(x, cfg):
    hz = cfg['hz']
    w = round(cfg['step_window_s'] * hz)
    if len(x) <= w:
        return []
    half = w // 2
    advance = x[w:] - x[:-w]
    a = x[half:len(x)-(w-half)] - x[:-w]
    b = x[w:] - x[half:len(x)-(w-half)]
    moving = (advance >= cfg['step_advance_m']) & (a >= cfg['sustained_half_advance_m']) & (b >= cfg['sustained_half_advance_m'])
    valid = (moving.sum(axis=1) >= x.shape[1]-1) & (np.ptp(x[:-w], axis=1) <= cfg['initial_spread_m'])
    windows = []
    for a, b in runs(np.r_[np.zeros(w, bool), valid]):
        start = a-w
        if windows and start < windows[-1][1]:
            windows[-1] = (windows[-1][0], b)
        else:
            windows.append((start, b))
    return windows


def detect_segment(s, cfg):
    x, hz = s['x'], cfg['hz']
    g = gaps(x)
    episodes = []
    for a, b in step_windows(x, cfg):
        stop = min(len(x), b+hz)
        candidate_options = []
        baseline = bool((g[a:stop] >= cfg['gap_m']).any())
        for j in range(x.shape[1]):
            peers = np.delete(x, j, axis=1)
            peer_move = np.median(peers - peers[a], axis=1)
            mask = ((g[:, j] >= cfg['gap_m']) & (np.ptp(peers, axis=1) <= cfg['peer_spread_m'])
                    & (g[:, j]-g[a, j] >= cfg['gap_growth_m'])
                    & (x[:, j]-x[a, j] <= cfg['lag_motion_ratio']*peer_move))
            for c, e in runs(mask[a:stop]):
                if e-c >= round(cfg['persistence_s']*hz):
                    candidate_options.append((a+c, -float(g[a+c, j]), j, a+e))
                    break
        event = dict(start_frame=s['start']+a, end_frame=s['start']+b-1,
                     duration_s=round((b-a)/hz, 3), team_id=s['team'], period=s['period'], phase_id=s['phase'],
                     members=list(s['members']), baseline=baseline, candidate=False)
        if candidate_options:
            c, _, j, confirmed_end = min(candidate_options)
            cap = min(len(x), c+round(cfg['followup_s']*hz)+1)
            recovery = None
            for r, e in runs(np.ptp(x[c:cap], axis=1) <= cfg['gap_m']):
                if e-r >= round(cfg['recovery_confirmation_s']*hz):
                    recovery = c+r
                    break
            gap_end = c
            while gap_end < cap and g[gap_end, j] >= cfg['gap_m']:
                gap_end += 1
            follow_end = recovery + round(cfg['recovery_confirmation_s']*hz) if recovery is not None else cap
            event.update(candidate=True, defender_index=s['members'][j], onset_frame=s['start']+c,
                         confirmation_frame=s['start']+c+round(cfg['persistence_s']*hz)-1,
                         follow_end_frame=s['start']+follow_end-1,
                         peak_gap_m=float(g[c:follow_end, j].max()),
                         gap_duration_s=round((gap_end-c)/hz, 3), gap_censored=gap_end == cap,
                         recovery_s=round((recovery-c)/hz, 3) if recovery is not None else None,
                         recovery_censored=recovery is None,
                         censor_reason=None if recovery is not None else ('10s_cap' if cap < len(x) else 'eligibility_end'),
                         followup_s=round((follow_end-c)/hz, 3),
                         line_observed_fraction=float(s['detected'][c:follow_end].mean()),
                         candidate_window_all_line_detected=bool(s['detected'][c:c+round(cfg['persistence_s']*hz)].all()))
        episodes.append(event)
    return episodes


def quantiles(values):
    return {str(q): float(np.quantile(values, q)) for q in [0, .25, .5, .75, .9, 1]} if len(values) else None


def analyze(segments, reasons, cfg):
    episodes = [e for s in segments for e in detect_segment(s, cfg)]
    candidates = [e for e in episodes if e['candidate']]
    frame_gap = np.concatenate([gaps(s['x']).max(axis=1) for s in segments]) if segments else np.array([])
    spread = np.concatenate([np.ptp(s['x'], axis=1) for s in segments]) if segments else np.array([])
    return dict(eligibility=reasons, eligible_team_seconds=sum(len(s['x']) for s in segments)/cfg['hz'],
                line_size_frames=dict(Counter({str(k): sum(len(s['x']) for s in segments if len(s['members']) == k) for k in [3,4,5]})),
                stepping_episodes=len(episodes), stepping_seconds=sum(e['duration_s'] for e in episodes),
                step_duration_quantiles_s=quantiles([e['duration_s'] for e in episodes]),
                baseline_steps=sum(e['baseline'] for e in episodes), candidate_steps=len(candidates),
                candidate_fraction=len(candidates)/len(episodes) if episodes else None,
                gap_quantiles_m=quantiles(frame_gap), spread_quantiles_m=quantiles(spread),
                candidate_gap_duration_quantiles_s=quantiles([e['gap_duration_s'] for e in candidates]),
                gap_censored=sum(e['gap_censored'] for e in candidates),
                recovered=sum(not e['recovery_censored'] for e in candidates),
                recovery_censored=sum(e['recovery_censored'] for e in candidates),
                observed_recovery_quantiles_s=quantiles([e['recovery_s'] for e in candidates if e['recovery_s'] is not None]),
                all_line_detected_candidates=sum(e['candidate_window_all_line_detected'] for e in candidates)), episodes
