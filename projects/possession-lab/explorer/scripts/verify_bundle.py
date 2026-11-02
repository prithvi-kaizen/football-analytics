"""Validate the public artifact, including its no-label public-sample contract."""
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

DIST = Path(__file__).resolve().parents[1] / 'dist'

def main():
    cases = list((DIST / 'data').glob('*.json'))
    assert len(cases) == 25, len(cases)
    for path in cases:
        data = json.loads(path.read_text())
        worlds = data.get('worlds', [data])
        if 'worlds' in data:
            assert data['identical_tracking']
            assert worlds[0]['tracking'] == worlds[1]['tracking']
            assert worlds[0]['truth'] != worlds[1]['truth']
            if data['evidence'] != 'independent':
                assert all(s['balanced_target_accuracy'] <= .5 for s in data['summary'])
        for world in worlds:
            n = world['frames']
            assert len(world['tracking']['ball']) == n
            assert all(len(m['labels']) == n and set(m['labels']) <= set('HADX') for m in world['models'])
            if path.stem.startswith('public'):
                assert world['truth'] is None
                assert all(m['metrics'] is None for m in world['models'])
    with ZipFile(DIST / 'possession-lab-source.zip') as archive:
        names = archive.namelist()
        assert not any(any(p.startswith(('.git', '.env', '.venv', 'restricted', 'private')) for p in Path(n).parts) for n in names)
        assert 'possession-lab/LICENSE' in names
        assert 'possession-lab/scripts/reproduce_explorer.sh' in names
        assert 'possession-lab/explorer/web/index.html' in names
        assert not any(n.endswith(('.csv', '.xml', '.atd', '.mp4')) and '/outputs/' not in n for n in names)
    with ZipFile(DIST / 'research-python.zip') as archive:
        manifest = json.loads((DIST / 'provenance.json').read_text())
        for name, digest in manifest['research_source_sha256'].items():
            assert hashlib.sha256(archive.read(name)).hexdigest() == digest
    print(f'PASS: {len(cases)} public/synthetic cases; null public accuracy; exact twins; source allowlist; Python archive hashes')

if __name__ == '__main__':
    main()
