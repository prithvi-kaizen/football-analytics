import math
import json
from pathlib import Path
import pytest
import numpy as np
from open_body.orientation import shoulder_measurement, gate, causal_heading, wrap

CFG = json.loads(
    (Path(__file__).resolve().parents[1] / "configs/pilot.json").read_text()
)


def sample(frame, angle=0, error=6, width=0.4):
    return {
        "frame": frame,
        "period": 1,
        "heading": angle,
        "error": error,
        "width": width,
        "midpoint_residual": 0,
        "reason": "measured",
    }


def test_heading_geometry_and_error_gate():
    p = {
        "x": 0,
        "y": 0,
        "joints": {
            "lShoulder": {"xyz": [0, 0.2, 1.5], "p90_mae_cm": 6},
            "rShoulder": {"xyz": [0, -0.2, 1.5], "p90_mae_cm": 7},
        },
    }
    s = shoulder_measurement(p)
    assert (
        s["heading"] == 0
        and s["width"] == pytest.approx(0.4)
        and gate(s, CFG) == "valid"
    )
    p["joints"]["rShoulder"]["p90_mae_cm"] = 40
    assert gate(shoulder_measurement(p), CFG) == "error"
    assert gate(sample(5, width=0.01), CFG) == "width"
    assert gate({"reason": "no_pose"}, CFG) == "no_pose"


def test_circular_smoothing_wraps_without_fake_spin():
    values = [
        sample(100, math.radians(179)),
        sample(101, math.radians(-179)),
        sample(102, math.radians(180)),
    ]
    h, reason = causal_heading(values, 102 / 25, CFG)
    assert reason == "valid" and abs(abs(h["heading"]) - math.pi) < 0.02
    assert abs(wrap(math.radians(-179) - math.radians(179))) == pytest.approx(
        math.radians(2)
    )


def test_future_pose_cannot_change_heading():
    past = [sample(f, 0.3) for f in [98, 99, 100]]
    a, _ = causal_heading(past, 4, CFG)
    b, _ = causal_heading(past + [sample(101, -2.8), sample(102, 0)], 4, CFG)
    assert a == b and a["latest_frame"] == 100
    h, _ = causal_heading([sample(f, 0.2) for f in [98, 99, 100, 101, 102]], 4.02, CFG)
    assert h["latest_frame"] == 100


def test_missing_and_incoherent_windows_rejected():
    assert causal_heading([sample(100)], 4, CFG)[0] is None
    assert causal_heading([sample(f) for f in [95, 96, 97]], 4, CFG)[0] is None
    assert (
        causal_heading([sample(98, 0), sample(99, 2.1), sample(100, -2.1)], 4, CFG)[1]
        == "incoherent"
    )


@pytest.mark.real_data
def test_real_predictions_reconcile_when_available():
    import pandas as pd
    from open_body.models import losses

    out = Path(__file__).resolve().parents[1] / "outputs"
    if not (out / "heldout_predictions.csv").exists():
        pytest.skip("run orientation stage")
    pred = pd.read_csv(out / "heldout_predictions.csv")
    result = json.loads((out / "results.json").read_text())
    for r in [result["primary"], result["reverse_diagnostic"]]:
        p = pred[pred.match_id.eq(r["test_match"])]
        d = losses(p.target, p.p_orientation) - losses(p.target, p.p_baseline)
        assert d.mean() == pytest.approx(r["delta_log_loss"], abs=1e-12)
        assert np.allclose(p.loss_difference, d)
    rows = pd.read_csv(out / "receptions_orientation.csv")
    assert (rows.latest_pose_frame / 25 <= rows.feature_cutoff + 1e-8).all()
    assert rows[["match_id", "event_id"]].duplicated().sum() == 0


def test_no_smoothing_is_one_latest_frame():
    h, _ = causal_heading(
        [sample(99, -0.8), sample(100, 0.5)], 4, {**CFG, "smooth_seconds": 0}
    )
    assert h["heading"] == pytest.approx(0.5) and h["samples"] == 1


def test_native_tracking_misalignment_rejected():
    assert (
        gate({**sample(100), "tracking_residual": 7}, CFG)
        == "native_tracking_misalignment"
    )
    assert (
        gate({**sample(100), "tracking_residual": None}, CFG)
        == "native_tracking_missing"
    )


@pytest.mark.real_data
def test_full_match_audit_reconciles_published_counts_when_available():
    out = Path(__file__).resolve().parents[1] / "outputs/cache/1925299/pose_audit.json"
    if not out.exists():
        pytest.skip("run full pose extraction")
    a = json.loads(out.read_text())
    assert a["frames"] == 153252
    assert a["player_frames_with_pose"] == 1540715
    assert a["roster_player_frames"] == 4902560
    assert sum(a["shoulder_gates"].values()) == a["roster_player_frames"]
    assert a["maximum_exact_alignment_clock_error_s"] == 0
    assert (
        a["active_player_frames_with_pose"]
        <= a["active_player_frames"]
        < a["roster_player_frames"]
    )
    assert set(a["period_frames"]) == {"1", "2"}
