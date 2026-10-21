from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

PROJECT = Path(__file__).resolve().parents[1]


@pytest.mark.real_data
def test_app_filters_replay_and_thresholds():
    if not list((PROJECT / "outputs").glob("*/manifest.json")):
        pytest.skip("Reproduce a sample before testing the real app")
    app = AppTest.from_file(str(PROJECT / "app.py"), default_timeout=60).run()
    assert not app.exception
    app.selectbox[0].select(PROJECT / "outputs/1886347-sample-300s").run()
    assert not app.exception
    assert len(app.get("plotly_chart")) >= 2
    app.selectbox[3].select("Runner + context endpoints detected").run()
    assert not app.exception
    assert any("No runs meet" in item.value for item in app.info)
    app.selectbox[3].select("All estimates").run()
    app.selectbox[1].select(4177).run()
    assert not app.exception
    app.selectbox[1].select("All").run()
    app.selectbox[2].select("Behind line").run()
    assert not app.exception
    app.selectbox[2].select("All").run()
    app.slider(key="frame_index").set_value(1).run()
    assert not app.exception
    app.button[3].click().run()
    assert not app.exception
    app.slider[0].set_value(8.0)
    app.slider[1].set_value(20.0)
    app.button[0].click().run()
    assert not app.exception
