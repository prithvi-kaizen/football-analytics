"""Audit the data before freezing the detector."""
import json
from pathlib import Path
from collections import Counter
from one_step_behind.data import load_match
ROOT = Path(__file__).resolve().parents[1]
for mid in [1925299, 1996435]:
    d = load_match(ROOT / 'data/raw', mid)
    a = d['audit']
    a.pop('sample_record', None)
    a['roles'] = dict(Counter(p['player_role']['position_group'] for p in d['metadata']['players']))
    a['all_22_detected_frames'] = int((d['detected'].sum(axis=1) == 22).sum())
    (ROOT / f'outputs/audit-{mid}.json').write_text(json.dumps(a, indent=2)+'\n')
    print(mid, a['detection_fraction'], a['player_count_distribution'], a['roles'])
