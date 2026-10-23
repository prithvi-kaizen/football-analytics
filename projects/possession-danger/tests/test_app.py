from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).parents[1]


def box(app, label):
    return next(item for item in app.selectbox if item.label == label)


@pytest.mark.real_data
def test_dashboard_filters_and_thresholds():
    if not (ROOT / "outputs/sample/actions.csv").exists():
        pytest.skip("Generate sample outputs first")
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    assert not app.exception
    sample = next(value for value in box(app, "Dataset").options if value == "sample")
    # Streamlit selectbox values here are Path objects, displayed by folder name.
    box(app, "Dataset").set_value(ROOT / "outputs" / sample).run()
    assert not app.exception
    app.radio[0].set_value("Territorial control").run()
    assert not app.exception
    box(app, "Match split").set_value("Training matches").run()
    assert not app.exception
    box(app, "Match split").set_value("All matches (descriptive)").run()
    assert not app.exception
    names = box(app, "Focus team").options
    box(app, "Focus team").set_value(names[-1]).run()
    assert not app.exception
    # All match, sequence, and threshold controls must trigger a valid rerun.
    match_control = box(app, "Match")
    if len(match_control.options) > 1:
        match_control.select_index(len(match_control.options) - 1).run()
    sequence_control = box(app, "Possession")
    sequence_control.select_index(len(sequence_control.options) - 1).run()
    assert not app.exception
    next(s for s in app.slider if s.label == "Minimum elapsed duration (seconds)").set_value(90).run()
    next(s for s in app.slider if s.label == "Positive move xT ceiling").set_value(.001).run()
    assert not app.exception
    assert any("No possessions meet" in item.value for item in app.info)
    assert {tab.label for tab in app.tabs} == {"Team comparison", "Match lab", "Methods & validation"}


@pytest.mark.real_data
def test_dashboard_supports_every_sample_league():
    if not (ROOT / "outputs/all-leagues-sample/actions.csv").exists():
        pytest.skip("Generate all-leagues-sample first")
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    box(app, "Dataset").set_value(ROOT / "outputs/all-leagues-sample").run()
    leagues = box(app, "Competition").options.copy()
    assert len(leagues) == 5
    for league in leagues:
        box(app, "Competition").set_value(league).run()
        assert not app.exception, league
