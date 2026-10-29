"""Package the executed viewer for static hosting; no analytics dependencies."""
import argparse
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def build(output):
    output.mkdir(parents=True, exist_ok=True)
    (output/'outputs').mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT/'outputs/viewer.html', output/'outputs/viewer.html')
    (output/'index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="0;url=outputs/viewer.html"><title>Lane obstruction research replay</title><a href="outputs/viewer.html">Open the passing-lane replay</a></html>')
    for name in ['results.md', 'results.json', 'demo.mp4', 'demo-poster.png', 'results.png']:
        shutil.copyfile(ROOT/'outputs'/name, output/'outputs'/name)
    for name in ['methodology.md', 'limitations.md', 'feasibility.md']:
        destination=output/'docs'/name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT/'docs'/name, destination)
    destination=output/'docs/source/SkillCorner-LICENSE'
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT/'docs/source/SkillCorner-LICENSE', destination)
    shutil.copyfile(ROOT/'LICENSE', output/'LICENSE')
    print(f'Packaged verified static viewer at {output}')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'dist')
    build(parser.parse_args().output.resolve())
