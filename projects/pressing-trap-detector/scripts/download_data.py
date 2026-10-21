"""Download the public Euro 2024 event release, pinned to one source revision."""
import argparse
import concurrent.futures
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data' / 'raw'
REPO = 'https://raw.githubusercontent.com/hudl/open-data/'

def fetch(url):
    with urllib.request.urlopen(url, timeout=60) as response:
        return response.read()

def main():
    RAW.mkdir(parents=True, exist_ok=True)
    parser = argparse.ArgumentParser()
    parser.add_argument('--revision', help='Specific source commit; defaults to the existing manifest, or master on first download.')
    args = parser.parse_args()
    manifest_path = ROOT / 'data' / 'manifest.json'
    revision = args.revision or (json.loads(manifest_path.read_text())['revision'] if manifest_path.exists() else json.loads(fetch('https://api.github.com/repos/hudl/open-data/commits/master'))['sha'])
    base = REPO + revision + '/'
    matches_bytes = fetch(base + 'data/matches/55/282.json')
    matches = json.loads(matches_bytes)
    (RAW / 'matches.json').write_bytes(matches_bytes)
    def download(match):
        match_id = match['match_id']
        content = fetch(base + f'data/events/{match_id}.json')
        events = json.loads(content)
        assert events and len({event['id'] for event in events}) == len(events)
        (RAW / f'{match_id}.json').write_bytes(content)
        return {'match_id': match_id, 'events': len(events), 'sha256': hashlib.sha256(content).hexdigest()}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        checks = list(pool.map(download, matches))
    (RAW / 'LICENSE.pdf').write_bytes(fetch(base + 'LICENSE.pdf'))
    (RAW / 'README.md').write_bytes(fetch(base + 'README.md'))
    manifest = {'repository': 'https://github.com/hudl/open-data', 'revision': revision,
                'competition_id': 55, 'season_id': 282, 'matches': checks}
    (ROOT / 'data' / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    print(json.dumps({'revision': revision, 'matches': len(matches), 'events': sum(x['events'] for x in checks)}))

if __name__ == '__main__':
    main()
