"""Verify executed deliverables and retain portable checksums and test evidence."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''):
            h.update(chunk)
    return h.hexdigest()


def luminance(s):
    values=[int(s[i:i+2],16)/255 for i in (1,3,5)]
    linear=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in values]
    return sum(a*b for a,b in zip(linear,[.2126,.7152,.0722]))


test=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=ROOT,capture_output=True,text=True)
if test.returncode:
    raise RuntimeError(test.stdout+test.stderr)
browser=json.loads((ROOT/'outputs/browser-validation.json').read_text())
assert browser['status']=='passed'
assert not browser['console_errors']
media=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration,size','-show_entries','stream=codec_name,width,height','-of','json',str(ROOT/'outputs/demo.mp4')]))
assert 20<=float(media['format']['duration'])<=40
text=(ROOT/'outputs/viewer.html').read_text()
assert '__PAYLOAD__' not in text and '—' not in text
assert 'SkillCorner' in text and 'PySport' in text
assert 'https://cdn' not in text and '<script src=' not in text
for value in ['/Users/','api_key','birth_date','birthday']:
    assert value not in text
pairs=[]
for fg,bg in [('#192724','#f7f4ec'),('#4c5955','#f7f4ec'),('#00665c','#f7f4ec'),('#973c20','#f7f4ec'),('#192724','#e5ede4'),('#00665c','#e5ede4'),('#973c20','#e5ede4'),('#727d75','#f7f4ec'),('#727d75','#e5ede4')]:
    a,b=sorted([luminance(fg),luminance(bg)])
    ratio=(b+.05)/(a+.05)
    minimum=3 if fg=='#727d75' else 4.5
    assert ratio>=minimum,(fg,bg,ratio)
    pairs.append(dict(foreground=fg,background=bg,ratio=round(ratio,3),minimum=minimum))
files={}
for directory in ['lane_obstruction','scripts','tests','configs','docs']:
    for p in sorted((ROOT/directory).rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts:
            files[str(p.relative_to(ROOT))]=sha(p)
for p in [ROOT/'README.md',ROOT/'LICENSE',ROOT/'pyproject.toml',ROOT/'requirements-lock.txt',ROOT/'viewer.html',ROOT/'data/source-lock.json']:
    files[str(p.relative_to(ROOT))]=sha(p)
outputs={str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'outputs').iterdir()) if p.is_file() and p.name not in ['verification.json']}
result=dict(status='passed',python=platform.python_version(),
            dependencies={p:importlib.metadata.version(p) for p in ['numpy','pandas','Pillow']},
            analytical_test_log=test.stderr.strip(),browser=browser,media=media,
            contrast_pairs=pairs,source_and_code_sha256=files,output_sha256=outputs,
            limitations='Engineering and rendering checks only; no physical-device, screen-reader, independent football-label or causal validation.')
(ROOT/'outputs/verification.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS: analytical tests, recorded browser controls/layouts, contrast, 30-second media and portable checksums')
