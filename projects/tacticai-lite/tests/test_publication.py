import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]


def load_builder():
    spec=importlib.util.spec_from_file_location('website_builder',ROOT/'scripts/build_website.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def test_public_release_contains_only_aggregates():
    data=json.loads((ROOT/'web/data.json').read_text())
    assert sum(r['corners'] for r in data['inventory'])==817
    assert sum(r['corners'] for r in data['delivery'])==813
    assert sum(r['shots_created'] for r in data['delivery'])==293
    assert data['audit']['mismatches']==0
    forbidden={'corner_id','match_id','event_uuid','freeze_frame','visible_area','location','team_id','player','taker','sequence'}
    def check(value):
        if isinstance(value,dict):
            assert not forbidden.intersection(value)
            for item in value.values():check(item)
        elif isinstance(value,list):
            for item in value:check(item)
    check(data)


def test_website_build_is_offline_and_complete(tmp_path):
    subprocess.run([sys.executable,str(ROOT/'scripts/build_website.py'),'--output',str(tmp_path)],check=True)
    for path in ['index.html','app.js','style.css','data.json','release.json','reports/findings.md','reports/corner-shot-creation.png']:
        assert (tmp_path/path).is_file()
    assert not (tmp_path/'data/raw').exists()
    assert not (tmp_path/'outputs').exists()


def test_website_refuses_modified_release(tmp_path):
    release=json.loads((ROOT/'web/release.json').read_text())
    for name in [*release['files'],'web/release.json']:
        destination=tmp_path/name;destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/name,destination)
    with (tmp_path/'web/data.json').open('a') as handle: handle.write(' ')
    builder=load_builder();builder.ROOT=tmp_path
    with pytest.raises(ValueError,match='integrity'):
        builder.build(tmp_path/'result')
