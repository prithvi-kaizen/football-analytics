"""Fetch the pinned public Pyodide runtime; verify wheels against its package lock."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import subprocess

BASE = 'https://cdn.jsdelivr.net/pyodide/v0.29.2/full/'
DEST = Path(__file__).resolve().parents[1] / 'web' / 'runtime'

def fetch(name):
    path = DEST / name
    if not path.exists():
        subprocess.run(['curl', '--fail', '--retry', '2', '--max-time', '120', '--silent', '--show-error', BASE + name, '-o', str(path)], check=True)
    return path

def main():
    DEST.mkdir(parents=True, exist_ok=True)
    expected = json.loads((DEST / 'SHA256.json').read_text())['files'] if (DEST / 'SHA256.json').exists() else {}
    lock = json.loads(fetch('pyodide-lock.json').read_text())
    packages = set()
    def visit(name):
        if name in packages:
            return
        packages.add(name)
        for dep in lock['packages'][name].get('depends', []):
            visit(dep)
    visit('numpy')
    visit('pandas')
    names = ['pyodide.js', 'pyodide.asm.js', 'pyodide.asm.wasm', 'python_stdlib.zip']
    names += [lock['packages'][name]['file_name'] for name in sorted(packages)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(fetch, names))
    licence = DEST / 'PYODIDE-LICENSE.txt'
    if not licence.exists():
        subprocess.run(['curl', '--fail', '--max-time', '60', '--silent', '--show-error',
                        'https://raw.githubusercontent.com/pyodide/pyodide/0.29.2/LICENSE', '-o', str(licence)], check=True)
    for name, digest in expected.items():
        if hashlib.sha256((DEST / name).read_bytes()).hexdigest() != digest:
            raise ValueError('Pinned runtime hash mismatch: ' + name)
    for name in packages:
        package = lock['packages'][name]
        digest = hashlib.sha256((DEST / package['file_name']).read_bytes()).hexdigest()
        if digest != package['sha256']:
            raise ValueError('Runtime wheel hash mismatch: ' + name)
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(DEST.iterdir()) if p.is_file() and p.name != 'SHA256.json'}
    (DEST / 'SHA256.json').write_text(json.dumps({'source': BASE, 'files': hashes}, indent=2) + '\n')
    print(json.dumps({p.name: p.stat().st_size for p in sorted(DEST.iterdir())}))

if __name__ == '__main__':
    main()
