from pathlib import Path
from streamlit.testing.v1 import AppTest

APP=Path(__file__).resolve().parents[1]/"app.py"


def start():
    app=AppTest.from_file(str(APP),default_timeout=60).run()
    assert not app.exception
    return app


def test_app_real_data_controls_and_replay():
    app=start()
    assert app.metric[0].value=="168"
    next(w for w in app.checkbox if w.label=="Show central space and clear corridors").uncheck().run()
    assert not next(w for w in app.checkbox if w.label=="Show central space and clear corridors").value
    next(w for w in app.checkbox if w.label=="Show central space and clear corridors").check().run()
    next(w for w in app.selectbox if w.label=="Losing team").select("Fortuna Düsseldorf").run()
    assert not app.exception and app.metric[0].value=="81"
    next(w for w in app.radio if w.label=="Half").set_value("First half").run()
    assert not app.exception
    next(w for w in app.checkbox if w.label=="Attacking losses only").uncheck().run()
    assert not app.exception
    next(w for w in app.checkbox if w.label=="Require event corroboration").check().run()
    assert not app.exception
    next(w for w in app.radio if w.label=="Pitch view").set_value("Recorded transition frames").run()
    assert not app.exception and len(app.select_slider)==1
    initial_frame=app.select_slider[0].value
    app.select_slider[0].set_value(initial_frame+5).run()
    assert not app.exception and app.select_slider[0].value==initial_frame+5
    picker=next(w for w in app.selectbox if w.label=="Turnover to inspect")
    picker.select(picker.value).run()
    assert not app.exception


def test_app_empty_state_and_sample_switch():
    app=start()
    app.slider[0].set_range(99,100).run()
    assert not app.exception and "No turnovers" in app.info[0].value
    app.slider[0].set_range(0,100).run()
    next(w for w in app.selectbox if w.label=="Analysis").select(APP.parent/"outputs/sample").run()
    assert not app.exception
    assert app.warning


def test_app_source_error_state(monkeypatch):
    import streamlit as st
    st.cache_data.clear()
    monkeypatch.setattr("rest_defence.pipeline.load_result",lambda path: (_ for _ in ()).throw(ValueError("fixture integrity failure")))
    app=AppTest.from_file(str(APP),default_timeout=60).run()
    assert not app.exception
    assert "integrity failure" in app.error[0].value
    st.cache_data.clear()
