import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from open_body.data import (
    iter_frames,
    reception_events,
    build_receptions,
    clock_seconds,
)
from open_body.models import fit_predict, losses, metrics, block_interval

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "configs/pilot.json").read_text())


def test_loss_matches_independent_formula():
    y = np.array([0, 1, 1])
    p = np.array([0.2, 0.8, 0.3])
    assert np.mean(losses(y, p)) == pytest.approx(-np.log([0.8, 0.8, 0.3]).mean())
    assert metrics(y, p)["brier"] == pytest.approx(np.mean((y - p) ** 2))
    assert metrics(y, p)["auroc"] == 1


def test_scaler_uses_training_only():
    train = pd.DataFrame({"x": [-2, -1, 1, 2], "target": [0, 0, 1, 1]})
    test = pd.DataFrame({"x": [1000, 2000]})
    p, model = fit_predict(train, test, ["x"], CFG)
    assert model[0].mean_[0] == 0
    assert np.isfinite(p).all() and np.all((p >= 0) & (p <= 1))
    assert np.allclose(p, model.predict_proba(test[["x"]].to_numpy())[:, 1])


def test_bootstrap_is_paired_and_reproducible():
    cfg = {**CFG, "bootstrap_repetitions": 200}
    a = block_interval(np.ones(20) * 0.2, np.repeat(np.arange(4), 5), cfg)
    assert a == block_interval(np.ones(20) * 0.2, np.repeat(np.arange(4), 5), cfg)
    assert a["low"] == pytest.approx(0.2) and a["high"] == pytest.approx(0.2)


def test_streams_plain_and_gzip(tmp_path):
    import gzip

    data = b'{"frame":1}\n{"frame":2}\n'
    path = tmp_path / "a.jsonl"
    path.write_bytes(data)
    gz = tmp_path / "a.jsonl.gz"
    with gzip.open(gz, "wb") as f:
        f.write(data)
    assert (
        list(iter_frames(path)) == list(iter_frames(gz)) == [{"frame": 1}, {"frame": 2}]
    )
    assert clock_seconds("01:02:03.40") == pytest.approx(3723.4)


@pytest.mark.real_data
def test_real_event_labels_and_goalkeepers():
    if not (ROOT / "data/raw/1925299_dynamic_events.csv").exists():
        pytest.skip("run download_data.py")
    d, a = reception_events(ROOT / "data/raw", 1925299, CFG)
    meta = json.loads((ROOT / "data/raw/1925299_match.json").read_text())
    keepers = {p["id"] for p in meta["players"] if p["player_role"]["acronym"] == "GK"}
    assert not set(d.player_id) & keepers and a["goalkeeper"] > 0
    raw = pd.read_csv(
        ROOT / "data/raw/1925299_dynamic_events.csv", low_memory=False
    ).set_index("event_id")
    for r in d.to_dict("records"):
        e = raw.loc[r["event_id"]]
        expected = (
            e.end_type == "pass"
            and e.pass_outcome == "successful"
            and e.duration <= 2
            and e.player_targeted_x_reception - e.x_start >= 5
        )
        assert r["target"] == int(expected)


@pytest.mark.real_data
def test_real_coordinate_join():
    path = ROOT / "data/raw/1925299_tracking_extrapolated.jsonl"
    if not path.exists() or path.stat().st_size < 97091519:
        pytest.skip("full tracking unavailable")
    d, a, t = build_receptions(ROOT / "data/raw", 1925299, CFG)
    assert len(d) > 500 and d.tracking_event_residual_m.median() < 0.5
    assert set(t.period) == {0, 1, 2}
    assert a["tracking"]["outside_period_frames"] > 0
    assert (
        d.target.nunique() == 2
        and d[["x", "abs_y", "pre_speed_mps"]].notna().all().all()
    )


def test_zip_ignores_macos_resource_forks(tmp_path):
    import zipfile

    path = tmp_path / "poses.zip"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("7.jsonl", '{"frame":1}\n')
        z.writestr("__MACOSX/._7.jsonl", "resource fork, not JSON")
    assert list(iter_frames(path)) == [{"frame": 1}]
