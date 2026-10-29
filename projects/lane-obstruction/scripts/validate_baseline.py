"""Run this real-data gate before adding/scoring arrival-time models."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
from lane_obstruction.data import start_states, sha256
from lane_obstruction.baseline import corridor_obstruction, marginal_obstruction

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--config', type=Path, default=root/'configs/pilot.json')
config_path = parser.parse_args().config.resolve()
cfg = json.loads(config_path.read_text())
meta, states, audit, receipts = start_states(root, cfg['development_matches'][0], cfg)
rows = []
for e, s in states:
    m = corridor_obstruction(s.ball, s.xy[s.target_indices], s.xy[s.defender_indices], cfg['corridor_halfwidth_m'], cfg['endpoint_buffer_m'])
    team, marginal = marginal_obstruction(m)
    assert np.all((team >= 0) & (team <= 1)) and (marginal >= 0).all()
    rows.append(float(team.mean()))
assert len(rows) > 50 and np.std(rows) > 0, 'Insufficient real baseline variation/coverage'
result = dict(status='passed', scope='development match only', n=len(rows), min=min(rows), max=max(rows), mean=float(np.mean(rows)), audit=audit,
              config_sha256=sha256(config_path), sources=receipts)
(root/'outputs/baseline_validation.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
