from pathlib import Path
import json
import pytest
import numpy as np
import pandas as pd
from open_body.models import fit_predict

ROOT = Path(__file__).resolve().parents[1]


def test_test_labels_cannot_change_predictions():
    train = pd.DataFrame({"x": [-2, -1, 1, 2], "target": [0, 0, 1, 1]})
    test = pd.DataFrame({"x": [0, 1], "target": [0, 1]})
    cfg = {"ridge_lambda": 1}
    p, _ = fit_predict(train, test, ["x"], cfg)
    test.target = 1 - test.target
    q, _ = fit_predict(train, test, ["x"], cfg)
    assert np.array_equal(p, q)


@pytest.mark.real_data
def test_exported_clips_are_real_deterministic_and_synchronized():
    path = ROOT / "outputs/viewer_data.json"
    if not path.exists():
        pytest.skip("run viewer stage")
    d = json.loads(path.read_text())
    rows = pd.read_csv(ROOT / "outputs/receptions_orientation.csv")
    assert len(d["clips"]) == 2
    for c in d["clips"]:
        eligible = (
            rows[rows.match_id.eq(c["match_id"]) & rows.position_group.eq("Midfield")]
            .sort_values("frame")
            .iloc[0]
        )
        assert c["event_id"] == eligible.event_id
        assert len(c["frames"]) >= 99
        for f in c["frames"]:
            assert 0 <= f["pose_frame"] / 25 - f["tracking_frame"] / 10 < 0.100001
            assert len({p["id"] for p in f["players"]}) == len(f["players"]) <= 22
            if f["joints"]:
                assert np.allclose(f["joints"]["midHip"], [0, 0, 0])
    html = (ROOT / "outputs/viewer.html").read_text()
    assert (
        "/* VIEWER_SCRIPT */" not in html
        and "/* VIEWER_STYLE */" not in html
        and "<!-- DATA_PAYLOAD -->" not in html
    )
    assert "<script src=" not in html and "fetch(" not in html
