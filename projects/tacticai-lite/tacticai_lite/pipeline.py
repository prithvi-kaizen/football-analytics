"""Build local research artifacts without redistributing provider records."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .analysis import extract_match, summary
from .data import REVISION, Store, download_matches, manifest, select_matches
from .models import cluster_corners, evaluate, usable_frames


def build(root: Path, sample=1, tournaments=('euro2024', 'weuro2025'), horizon=15, short_threshold=15, offline=False, output='outputs'):
    store = Store(root / 'data' / 'raw', offline=offline)
    matches = select_matches(store, tournaments, sample)
    datasets = download_matches(store, matches)
    tables, details = [], {}
    for match, events, frames in datasets:
        table, record_details = extract_match(match, events, frames, horizon, short_threshold)
        if not table.empty:
            tables.append(table)
        details.update(record_details)
    if not tables:
        raise ValueError('No corners found in selected matches')
    corners = pd.concat(tables, ignore_index=True)
    if corners.corner_id.duplicated().any():
        raise ValueError('Corner IDs are not unique across matches')
    corners, clusters, _, _ = cluster_corners(corners)
    model, predictions = evaluate(corners)
    dest = root / output
    dest.mkdir(parents=True, exist_ok=True)
    corners.to_csv(dest / 'corners.csv', index=False)
    summary(corners).to_csv(dest / 'delivery_summary.csv', index=False)
    summary(corners, ('tournament', 'cluster')).to_csv(dest / 'cluster_summary.csv', index=False)
    (dest / 'details.json').write_text(json.dumps(details, ensure_ascii=False))
    (dest / 'model.json').write_text(json.dumps(model, indent=2, allow_nan=False))
    if not predictions.empty:
        predictions.to_csv(dest / 'holdout_predictions.csv', index=False)
    elif (dest / 'holdout_predictions.csv').exists():
        (dest / 'holdout_predictions.csv').unlink()
    match_coverage = [{'match_id': m['match_id'], 'tournament': m['tournament'], 'events': len(e), 'frames': len(f)} for m,e,f in datasets]
    provenance = {'revision': REVISION, 'horizon_seconds': horizon, 'short_threshold_units': short_threshold,
        'sample_per_tournament': sample, 'matches': match_coverage, 'corners': len(corners),
        'corners_with_360': int(corners.has_360.sum()), 'usable_frames': int(usable_frames(corners).sum()),
        'censored': int(corners.shot_created.isna().sum()),
        'invalid_players': int(corners.invalid_players.sum()), 'clusters': clusters,
        'source_files': [r for r in manifest(store) if any(str(m['match_id']) in r['url'] for m in matches) or '/matches/' in r['url'] or 'competitions.json' in r['url']]}
    (dest / 'manifest.json').write_text(json.dumps(provenance, indent=2, allow_nan=False))
    return corners, provenance
