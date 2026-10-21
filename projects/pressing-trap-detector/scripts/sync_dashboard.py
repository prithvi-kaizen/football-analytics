"""Update reviewed evidence while preserving dashboard identity and presentation setup."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'dashboard/src/data.json'
current=json.loads(p.read_text())
reviewed=json.loads((ROOT/'outputs/reviewed.json').read_text())
for key in ['queries','generatedAt']:
    current[key]=reviewed[key]
current['buildStatus']='updating'
for f in current.get('filters',[]):
    if f['id']=='wide_candidate':
        f['field']='wide_entry'
p.write_text(json.dumps(current,separators=(',',':')))
print('Synced reviewed evidence, preserving dashboard ID and filter definitions.')
