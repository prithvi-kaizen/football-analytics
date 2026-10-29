"""Fetch pinned MIT-licensed source files or verify/reuse sibling project caches."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def fetch(reuse=False):
    lock = json.loads((ROOT / 'data/source-lock.json').read_text())
    for item in lock['files']:
        dst = ROOT / 'data/raw' / item['file']
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists() and sha256(dst) == item['sha256']:
            continue
        if dst.exists():
            raise ValueError(f'Corrupt cache: {dst}; remove explicitly before refetching')
        sources = []
        if reuse:
            sources = [ROOT.parent / 'open-body/data/raw' / item['file'],
                       ROOT.parent / f'invisible-runner/data/raw/{lock["revision"]}/1886347' / item['file']]
        src = next((p for p in sources if p.exists() and sha256(p) == item['sha256']), None)
        temp = dst.with_suffix(dst.suffix + '.part')
        try:
            if src:
                shutil.copyfile(src, temp)
            else:
                with urlopen(Request(item['url'], headers={'User-Agent': 'lane-obstruction-research/0.1'}), timeout=120) as response, temp.open('wb') as out:
                    shutil.copyfileobj(response, out)
            if sha256(temp) != item['sha256']:
                raise ValueError(f'Source hash mismatch: {item["file"]}')
            temp.replace(dst)
        finally:
            temp.unlink(missing_ok=True)
        print(item['file'], 'verified', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reuse-workspace', action='store_true')
    fetch(parser.parse_args().reuse_workspace)
