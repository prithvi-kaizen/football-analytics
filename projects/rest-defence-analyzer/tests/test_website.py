import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil

import numpy as np
import pandas as pd
import pytest
from rest_defence.data import analysis_fingerprint

ROOT=Path(__file__).resolve().parents[1]


def load_builder():
    spec=importlib.util.spec_from_file_location('rest_static_build',ROOT/'scripts/build_website.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_static_release_matches_every_published_transition():
    bundle=json.loads((ROOT/'web/bundle.json').read_text())
    compressed=(ROOT/'web'/bundle['snapshot']['archive']).read_bytes()
    raw=gzip.decompress(compressed)
    assert hashlib.sha256(compressed).hexdigest()==bundle['snapshot']['archive_sha256']
    assert hashlib.sha256(raw).hexdigest()==bundle['snapshot']['sha256']
    payload=json.loads(raw)
    assert payload['audit']['analysis_code_sha256']==analysis_fingerprint()
    df=pd.read_csv(ROOT/'outputs/J03WPY/transitions.csv').set_index('transition_id')
    assert len(payload['transitions'])==len(df)==293
    for row in payload['transitions']:
        source=df.loc[row['transition_id']]
        assert row['behind_ball']==source.behind_ball
        assert row['open_lanes']==len(row['overlay']['lanes'])
        if pd.notna(source.vulnerability_score):
            assert row['vulnerability_score']==pytest.approx(source.vulnerability_score)
        else:
            assert row['vulnerability_score'] is None
        assert len(row['snapshot'])==22
        assert row['timeline'][0][0]==0
        assert max(p[1] for p in row['timeline'])==pytest.approx(source.progress_m,abs=.002)
        assert row['replay'][0]['time']<0
    assert sum(r['attacking_scope'] for r in payload['transitions'])==168


def test_static_build_without_analytics_or_network(tmp_path):
    builder=load_builder()
    builder.build(tmp_path/'dist')
    assert (tmp_path/'dist/index.html').exists()
    release=json.loads((tmp_path/'dist/release.json').read_text())
    assert (tmp_path/'dist'/release['snapshot']).exists()
    assert (tmp_path/'dist/DATA-NOTICE.md').exists()


def test_static_build_rejects_modified_asset(tmp_path,monkeypatch):
    builder=load_builder()
    shutil.copytree(ROOT/'web',tmp_path/'web')
    with (tmp_path/'web/app.js').open('a') as out:
        out.write('\n// invalidated release\n')
    monkeypatch.setattr(builder,'ROOT',tmp_path)
    with pytest.raises(ValueError,match='Integrity'):
        builder.build(tmp_path/'dist')
