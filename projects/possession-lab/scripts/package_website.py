"""Package an explicitly reviewed explorer build for the offline portfolio builder."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import tarfile
from _release_io import sha256

ROOT = Path(__file__).resolve().parents[1]


def package(source):
    source = Path(source)
    allowed = {'index.html', 'app.js', 'style.css', 'worker.js', 'provenance.json', 'research-python.zip'}
    entries = {name: source / name for name in allowed}
    for directory in ('data', 'research', 'runtime'):
        for path in (source / directory).rglob('*'):
            if path.is_file():
                entries[str(path.relative_to(source))] = path
    for name in ('index.html', 'app.js', 'style.css', 'worker.js'):
        entries[name] = ROOT / 'explorer/web' / name
    for name in ('public1', 'public2'):
        data = json.loads(entries[f'data/{name}.json'].read_text())
        if data['truth'] is not None or any(m['metrics'] is not None for m in data['models']):
            raise ValueError('Public sample must not include possession truth or accuracy')
    provenance = json.loads(entries['provenance.json'].read_text())
    for name, digest in provenance['research_source_sha256'].items():
        path = ROOT / 'src' / name
        if path.exists() and sha256(path) != digest:
            raise ValueError('Research source differs from the reviewed build: ' + name)
    destination = ROOT / 'web'
    destination.mkdir(exist_ok=True)
    archive_path = destination / 'release.tar.gz'
    with archive_path.open('wb') as raw:
        with gzip.GzipFile(filename='', fileobj=raw, mode='wb', mtime=0) as stream:
            with tarfile.open(fileobj=stream, mode='w') as archive:
                for name, path in sorted(entries.items()):
                    info = archive.gettarinfo(str(path), arcname=name)
                    info.uid = info.gid = info.mtime = 0
                    info.uname = info.gname = ''
                    info.mode = 0o644
                    with path.open('rb') as content:
                        archive.addfile(info, content)
    tracked = [*list((ROOT / 'src').rglob('*.py')),
               *[ROOT / 'explorer/web' / name for name in ('index.html', 'app.js', 'style.css', 'worker.js')]]
    manifest = {'schema_version': 1,
                'classification': 'Synthetic experiments and attributed public Metrica excerpts; no restricted assets or public competition labels',
                'archive_sha256': sha256(archive_path),
                'source_files_sha256': {str(p.relative_to(ROOT)): sha256(p) for p in sorted(tracked)},
                'files': {name: sha256(path) for name, path in sorted(entries.items())}}
    (destination / 'release.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'assets': len(entries), 'archive_bytes': archive_path.stat().st_size}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    package(parser.parse_args().input)
