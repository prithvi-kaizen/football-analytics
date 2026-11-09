"""Build a standalone, network-free explorer from verified precomputed results."""
import argparse
import hashlib
import html
import json
import re
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]

def build(output):
    receipt = json.loads((ROOT / 'outputs/verification.json').read_text())
    if not receipt['passed']:
        raise ValueError('Output verification did not pass')
    for name in ['outputs/replays.json', 'outputs/results-1925299.json',
                 'outputs/results-1996435.json', 'outputs/demo.mp4', 'configs/pilot.json']:
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != receipt['files'][name]:
            raise ValueError(f'Verified release file changed: {name}')
    payload = (ROOT / 'outputs/replays.json').read_text()
    data = json.loads(payload)
    if len(data['examples']) != 3:
        raise ValueError('The reviewed pilot must contain three real comparison examples')
    for row in data['summaries']:
        current = hashlib.sha256((ROOT / 'configs/pilot.json').read_bytes()).hexdigest()
        if row['config_sha256'] != current:
            raise ValueError('Results do not match the frozen configuration')
    output.mkdir(parents=True, exist_ok=True)
    page = (ROOT / 'viewer/index.html').read_text().replace('__PAYLOAD__', payload.replace('</', '<\\/'))
    (output / 'index.html').write_text(page)
    for name in ['replays.json', 'results-1925299.json', 'results-1996435.json', 'independent-checks.json', 'verification.json']:
        shutil.copyfile(ROOT / 'outputs' / name, output / name)
    for source, target in [('docs/source/LICENSE.skillcorner', 'LICENSE.skillcorner'),
                           ('docs/protocol.md', 'protocol.md'), ('data/provenance.json', 'provenance.json')]:
        shutil.copyfile(ROOT / source, output / target)
    article = ROOT / 'docs/article.md'
    if article.exists():
        paragraphs = article.read_text().split('\n\n')
        def markdown_text(value):
            return re.sub(r'\[([^\]]+)\]\((https://[^\s)]+)\)', r'<a href="\2">\1</a>', html.escape(value))
        body = ''.join('<h1>'+markdown_text(p[2:])+'</h1>' if p.startswith('# ') else '<p>'+markdown_text(p)+'</p>' for p in paragraphs)
        (output / 'article.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>One Step Behind | Investigation</title><style>body{background:#f5f3ed;color:#273c45;max-width:750px;margin:45px auto;padding:0 22px;font:18px/1.7 system-ui}h1{font:44px/1.15 Georgia}a{color:#245a79}</style><a href="./">Back to the pitch replay</a>'+body+'</html>')
    video = ROOT / 'outputs/demo.mp4'
    if video.exists():
        shutil.copyfile(video, output / 'demo.mp4')
    manifest = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir() if p.is_file() and p.name != 'manifest.json'}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(f'One Step Behind: three real sequences, {len(payload):,} replay bytes -> {output}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT/'web')
    build(parser.parse_args().output)
