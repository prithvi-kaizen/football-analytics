"""Export aggregate analytical findings only, with a verified static release."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

from .analysis import summary

ROOT = Path(__file__).resolve().parents[1]


def records(frame):
    return json.loads(frame.to_json(orient='records', double_precision=15))


def package(root=ROOT):
    corners = pd.read_csv(root/'outputs/corners.csv')
    manifest = json.loads((root/'outputs/manifest.json').read_text())
    audit = json.loads((root/'reports/validation.json').read_text())
    model = json.loads((root/'outputs/model.json').read_text())
    if (audit['status'] != 'passed' or audit['source_revision'] != manifest['revision'] or
            audit['independently_reconstructed_corners'] != len(corners) or audit['mismatched_labels'] or audit['mismatched_shot_counts']):
        raise ValueError('Reconcile the current source labels before packaging a public release')
    if manifest['horizon_seconds'] != 15 or manifest['short_threshold_units'] != 15:
        raise ValueError('This reviewed public release requires the audited 15-second / 15-unit definitions')
    pass_corners = corners[corners.delivery.ne('Direct shot')]
    inventory = []
    for tournament, rows in corners.groupby('tournament'):
        inventory.append(dict(tournament=tournament, matches=int(rows.match_id.nunique()), corners=len(rows),
            frames=int(rows.has_360.sum()), usable_frames=int(rows.cluster.ne('No usable frame').sum()),
            shots_created=int(rows.shot_created.sum()), pass_corners=int(rows.delivery.ne('Direct shot').sum())))
    profiles = pass_corners[pass_corners.cluster.ne('No usable frame')].groupby(['tournament','cluster']).agg(
        corners=('corner_id','size'), attackers_box=('attackers_box','mean'), defenders_box=('defenders_box','mean'),
        box_visible_fraction=('box_visible_fraction','mean')).reset_index()
    payload = dict(schema_version=1, source_revision=manifest['revision'],
        definitions=dict(horizon_seconds=15, short_threshold_units=15, direct_shots_excluded=int(corners.delivery.eq('Direct shot').sum())),
        inventory=inventory, delivery=records(summary(pass_corners)),
        clusters=records(summary(pass_corners, ('tournament','cluster'))), cluster_profiles=records(profiles),
        sensitivity=records(pd.read_csv(root/'reports/window_sensitivity.csv')),
        model={key:model[key] for key in ['status','scope','features','train_corners','test_corners','metrics','seed']},
        split=dict(train_matches=len(model['train_matches']), test_matches=len(model['test_matches'])),
        audit=dict(corners_checked=audit['independently_reconstructed_corners'], mismatches=0))
    # The release contains no per-event IDs, match records, players, frames or locations.
    web = root/'web'
    web.mkdir(exist_ok=True)
    (web/'data.json').write_text(json.dumps(payload, indent=2, allow_nan=False)+'\n')
    sources = ['web/index.html','web/app.js','web/style.css','web/data.json',
        'assets/SB - Icon Lockup - Colour positive.png','reports/corner-shot-creation.png',
        'reports/delivery_summary.csv','reports/window_sensitivity.csv','reports/findings.md',
        'reports/validation.json']
    release = {'schema_version':1, 'source_revision':manifest['revision'],
        'classification':'Aggregate analytical findings; no provider event/player records',
        'files':{name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in sources}}
    (web/'release.json').write_text(json.dumps(release,indent=2)+'\n')
    return payload


if __name__=='__main__':
    payload=package()
    print(f"Packaged {sum(r['corners'] for r in payload['inventory'])} corners as aggregate findings only")
