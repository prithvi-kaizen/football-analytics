"""Build the reviewed static release using only the Python standard library."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]


def checked(path,expected):
    data=path.read_bytes()
    if hashlib.sha256(data).hexdigest()!=expected:
        raise ValueError(f'Integrity check failed: {path.name}')
    return data


def build(output):
    web=ROOT/'web'
    bundle=json.loads((web/'bundle.json').read_text())
    snapshot=bundle['snapshot']
    for name in list(bundle['assets'])+[snapshot['archive'],snapshot['path']]:
        if Path(name).name!=name:
            raise ValueError('Unsafe release filename')
    compressed=checked(web/snapshot['archive'],snapshot['archive_sha256'])
    data=gzip.decompress(compressed)
    if hashlib.sha256(data).hexdigest()!=snapshot['sha256']:
        raise ValueError('Decompressed snapshot integrity failure')
    for name,digest in bundle['assets'].items():
        checked(web/name,digest)
    output.mkdir(parents=True,exist_ok=True)
    for name in bundle['assets']:
        shutil.copyfile(web/name,output/name)
    (output/snapshot['path']).write_bytes(compressed)
    (output/'release.json').write_text(json.dumps({'snapshot':snapshot['path'],'sha256':snapshot['sha256']}))
    for name in ['transitions.csv','findings.md','findings.json','score-validation.png','score-validation.svg','independent-validation.json']:
        shutil.copyfile(ROOT/'outputs/J03WPY'/name,output/name)
    shutil.copyfile(ROOT/'data/sample/NOTICE.md',output/'DATA-NOTICE.md')
    shutil.copyfile(ROOT/'docs/methodology.md',output/'methodology.md')
    print(f'Rest Defence website built: {bundle["transitions"]} verified transitions')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=ROOT/'dist')
    build(parser.parse_args().output)
