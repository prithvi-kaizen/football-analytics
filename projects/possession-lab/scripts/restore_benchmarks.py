"""Restore exact historical synthetic outputs, without downloading match assets."""
import json
from pathlib import Path
from _release_io import restore

ROOT = Path(__file__).resolve().parents[1]

if __name__ == '__main__':
    manifest = json.loads((ROOT / 'benchmarks/manifest.json').read_text())
    count = restore(ROOT / 'benchmarks/history.tar.gz', manifest, ROOT)
    print(f'Restored and verified {count} historical synthetic files.')
