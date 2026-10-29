"""Render the checked-in viewer template with executed model outputs; no CDN."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
payload = {name: json.loads((ROOT/f'outputs/{name}.json').read_text()) for name in ['replays', 'results']}
encoded = json.dumps(payload, separators=(',', ':'), allow_nan=False).replace('</', '<\\/')
template = (ROOT/'viewer.html').read_text()
if template.count('__PAYLOAD__') != 1:
    raise ValueError('Expected exactly one data template binding')
(ROOT/'outputs/viewer.html').write_text(template.replace('__PAYLOAD__', encoded))
print('Built outputs/viewer.html')
