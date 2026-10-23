"""Restore the reviewed aggregate-only website. Standard library, no downloads."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]


def build(output):
    release=json.loads((ROOT/'web/release.json').read_text())
    for name,digest in release['files'].items():
        relative=Path(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Unsafe release path')
        source=ROOT/relative
        if hashlib.sha256(source.read_bytes()).hexdigest()!=digest:
            raise ValueError(f'Release integrity failure: {name}. Repackage the reviewed artifacts.')
        destination=output/(Path(*relative.parts[1:]) if relative.parts[0]=='web' else relative)
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,destination)
    shutil.copyfile(ROOT/'web/release.json',output/'release.json')
    print('TacticAI Lite website built; aggregate release hashes verified.')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=ROOT/'dist')
    build(parser.parse_args().output)
