"""Build the published static website using Python's standard library only."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def verify(data, digest, label):
    if hashlib.sha256(data).hexdigest() != digest:
        raise SystemExit(f'{label} failed its SHA-256 integrity check.')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'dist')
    args = parser.parse_args()
    web = ROOT / 'web'
    bundle = json.loads((web / 'bundle.json').read_text())
    html = (web / 'index.html').read_bytes()
    compressed = (web / bundle['snapshot']['archive']).read_bytes()
    verify(html, bundle['html']['sha256'], 'HTML')
    verify(compressed, bundle['snapshot']['archive_sha256'], 'Snapshot archive')
    snapshot = gzip.decompress(compressed)
    verify(snapshot, bundle['snapshot']['sha256'], 'Reviewed snapshot')
    filename = bundle['snapshot']['path']
    if Path(filename).name != filename:
        raise SystemExit('Snapshot filename must not contain a directory.')
    reviewed = json.loads(snapshot)
    if reviewed.get('buildStatus') != 'complete':
        raise SystemExit('The reviewed dashboard is not marked complete.')
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'index.html').write_bytes(html)
    (args.output / filename).write_bytes(snapshot)
    print(f"Website built: {len(reviewed['queries']['pressures']['rows']):,} pressure records; {len(snapshot):,} snapshot bytes; all integrity checks passed.")

if __name__ == '__main__':
    main()
