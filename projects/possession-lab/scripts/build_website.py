"""Restore the reviewed public/synthetic website using only the standard library."""
import argparse
import json
from pathlib import Path
from _release_io import restore, sha256

ROOT = Path(__file__).resolve().parents[1]


def build(output):
    manifest = json.loads((ROOT / 'web/release.json').read_text())
    for name, digest in manifest['source_files_sha256'].items():
        if sha256(ROOT / name) != digest:
            raise ValueError('Website source changed; regenerate and review the release: ' + name)
    # A fresh build directory avoids overwriting unrelated files or prior releases.
    output = Path(output)
    if output.exists():
        for name in manifest['files']:
            path = output / name
            if path.is_file() and sha256(path) != manifest['files'][name]:
                path.unlink()
    count = restore(ROOT / 'web/release.tar.gz', manifest, output)
    print(f'Possession Lab website built; {count} reviewed public/synthetic assets verified.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'dist')
    build(parser.parse_args().output)
