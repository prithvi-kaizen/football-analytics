from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).resolve().parents[1]


def test_app_empty_state(tmp_path,monkeypatch):
    monkeypatch.setenv('TACTICAI_OUTPUT',str(tmp_path))
    app=AppTest.from_file(str(ROOT/'app.py')).run(timeout=30)
    assert not app.exception
    assert 'No processed dataset' in app.info[0].value


def test_app_error_state(tmp_path,monkeypatch):
    for name in ['corners.csv','details.json','manifest.json','model.json']:
        (tmp_path/name).write_text('invalid')
    monkeypatch.setenv('TACTICAI_OUTPUT',str(tmp_path))
    app=AppTest.from_file(str(ROOT/'app.py')).run(timeout=30)
    assert not app.exception
    assert 'Could not load' in app.error[0].value


@pytest.mark.real_data
def test_app_filters_and_pitch(monkeypatch):
    if not (ROOT/'outputs/corners.csv').exists(): pytest.skip('Build real outputs first')
    monkeypatch.setenv('TACTICAI_OUTPUT',str(ROOT/'outputs'))
    app=AppTest.from_file(str(ROOT/'app.py')).run(timeout=45)
    assert not app.exception
    assert len(app.tabs)==3
    app.text_input[0].set_value('no-such-team-xyz').run()
    assert not app.exception and 'No corners match' in app.info[0].value
    app.text_input[0].set_value('Germany').run()
    assert not app.exception
    assert all('Germany' in label for label in app.selectbox[2].options)
    app.text_input[0].set_value('').run()
    app.selectbox[1].select('No shot').run()
    assert not app.exception
    assert any(h.value=='No shot created' for h in app.subheader)
    app.selectbox[1].select('All').run()
    app.checkbox[0].check().run()
    assert not app.exception
    app.checkbox[1].uncheck().run()
    assert not app.exception
    app.selectbox[0].select('C1').run()
    assert not app.exception
    app.multiselect[1].set_value(['Short']).run()
    assert not app.exception
    app.multiselect[0].set_value([]).run()
    assert 'No corners match' in app.info[0].value


@pytest.mark.real_data
def test_export_payload_and_comparison_denominator(monkeypatch):
    import io
    import pandas as pd
    import streamlit as st
    if not (ROOT/'outputs/corners.csv').exists(): pytest.skip('Build real outputs first')
    monkeypatch.setenv('TACTICAI_OUTPUT',str(ROOT/'outputs'))
    captured=[]
    original=st.download_button
    def record_download(label,data,*args,**kwargs):
        captured.append(data)
        return original(label,data,*args,**kwargs)
    monkeypatch.setattr(st,'download_button',record_download)
    app=AppTest.from_file(str(ROOT/'app.py')).run(timeout=45)
    assert not app.exception
    baseline=pd.read_csv(io.StringIO(captured[-1]))
    source=pd.read_csv(ROOT/'outputs/corners.csv')
    pass_corners=source[source.delivery.ne('Direct shot') & source.shot_created.notna()]
    assert baseline.corners.sum()==len(pass_corners)
    assert baseline.shots_created.sum()==pass_corners.shot_created.sum()
    app.selectbox[1].select('Shot created').run()
    assert not app.exception
    pd.testing.assert_frame_equal(pd.read_csv(io.StringIO(captured[-1])),baseline)
