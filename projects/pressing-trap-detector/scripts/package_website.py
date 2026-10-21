"""Package a verified dashboard without copying local chat metadata or raw-data caches."""
import gzip
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

def sha(data):
    return hashlib.sha256(data).hexdigest()

def main():
    source = ROOT / 'dashboard' / 'dist'
    manifest = json.loads((source / 'data-app-build.json').read_text())
    html = (source / manifest['html']['path']).read_bytes()
    snapshot = (source / manifest['snapshot']['path']).read_bytes()
    if sha(html) != manifest['html']['sha256'] or sha(snapshot) != manifest['snapshot']['sha256']:
        raise SystemExit('The source build does not match its verified manifest.')
    text = html.decode('utf-8')
    # This transient tag routes local Codex chats. It is unrelated to the public app.
    text, removed = re.subn(r'<meta\b(?=[^>]*\bname=["\']data-app-local-thread["\'])[^>]*>\s*', '', text)
    html = text.encode('utf-8')
    if '/Users/' in text or 'data-app-local-thread' in text:
        raise SystemExit('Local metadata remains in the website HTML.')
    compressed = gzip.compress(snapshot, compresslevel=9, mtime=0)
    web = ROOT / 'web'
    web.mkdir(exist_ok=True)
    (web / 'index.html').write_bytes(html)
    (web / 'snapshot.json.gz').write_bytes(compressed)
    publication = {
        'format': 1,
        'html': {'path': 'index.html', 'sha256': sha(html)},
        'snapshot': {'path': manifest['snapshot']['path'], 'archive': 'snapshot.json.gz',
                     'sha256': sha(snapshot), 'archive_sha256': sha(compressed), 'bytes': len(snapshot)},
        'upstream_html_sha256': manifest['html']['sha256'],
        'runtime_sha256': manifest['runtimeSha256'],
        'removed_local_thread_tags': removed,
    }
    (web / 'bundle.json').write_text(json.dumps(publication, indent=2) + '\n')
    print(json.dumps({'html_bytes': len(html), 'snapshot_bytes': len(snapshot),
                      'compressed_snapshot_bytes': len(compressed), 'removed_local_thread_tags': removed}))

if __name__ == '__main__':
    main()
