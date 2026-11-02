import numpy as np
import pytest

from possession_lab.tagging_interface import from_public_loader_records


def fictional_record(**extra):
    return {"start_s": 0.4, "end_s": 1.2, "code": "SET PIECES",
            "tags": {"Team": "Example Side", "Half": "1st Half", "Type": "Throw-in"}, **extra}


def test_future_context_preserves_uncertainty_and_intervals():
    record = fictional_record()
    intervals = from_public_loader_records([record], np.ones(50, int), 25, {"Example Side": "H"})
    item = intervals[0]
    assert (item.start, item.stop, item.team_hint) == (10, 30, "H")
    assert item.confidence is None
    assert item.code == "set pieces"
    assert not hasattr(item, "possession_label")


def test_na_team_and_conflicts_are_not_fabricated_truth():
    first = fictional_record(tags={"Team": "N/A"})
    second = fictional_record(tags={"Team": "Other Example"})
    result = from_public_loader_records([first, second], np.ones(50, int), 25, {"Other Example": "A"})
    assert len(result) == 2
    assert result[0].team_hint is None
    assert result[1].team_hint == "A"


@pytest.mark.parametrize("record", [fictional_record(end_s=10), fictional_record(start_s=np.nan),
    fictional_record(tags={"Team": "Unknown"}), fictional_record(tags={"Half": "2nd Half"}),
    fictional_record(confidence=1.2)])
def test_invalid_future_context_fails(record):
    with pytest.raises(ValueError):
        from_public_loader_records([record], np.ones(50, int), 25, {"Example Side": "H"})
