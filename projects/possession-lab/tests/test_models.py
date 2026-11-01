from dataclasses import replace

import numpy as np
import pytest

from possession_lab.adapters.official_future import OfficialAdapter
from possession_lab.features import extract
from possession_lab.models import ModelConfig, hmm, state_machine
from possession_lab.pipeline import infer, run


@pytest.mark.parametrize("method", ["state_machine", "hmm"])
def test_controlled_h_a_d(controlled_batch, method):
    labels = infer(controlled_batch, method).labels
    assert labels[30] == "H"
    assert labels[140] == "A"
    assert labels[-1] == "D"
    assert set(labels) <= set("HADX")


@pytest.mark.parametrize("model", [state_machine, hmm])
def test_short_missing_ball_does_not_mean_dead(controlled_batch, model):
    ball = controlled_batch.ball.copy()
    ball[40:70] = np.nan
    out = model(extract(replace(controlled_batch, ball=ball)))
    assert set(out[40:70]) == {"H"}


@pytest.mark.parametrize("model", [state_machine, hmm])
def test_long_missing_abstains(controlled_batch, model):
    ball = controlled_batch.ball.copy()
    ball[20:180] = np.nan
    out = model(extract(replace(controlled_batch, ball=ball)))
    assert out[120] == "X"
    assert "D" not in out[20:180]


@pytest.mark.parametrize("model", [state_machine, hmm])
def test_wholly_unobserved_half_abstains(controlled_batch, model):
    b = replace(controlled_batch, ball=np.full((300, 2), np.nan))
    assert set(model(extract(b))) == {"X"}


def test_five_frame_touch_does_not_switch(controlled_batch):
    b = controlled_batch
    away = b.away.copy()
    home = b.home.copy()
    away[50:55, 0] = b.ball[50:55] + [0.1, 0]
    home[50:55, 0] = b.ball[50:55] + [6.0, 0]
    f = extract(replace(b, away=away, home=home))
    assert set(state_machine(f)[40:90]) == {"H"}


def test_state_machine_control_boundary_confirmation(controlled_batch):
    labels = infer(controlled_batch).labels
    assert set(labels[100:107]) == {"H"}
    assert labels[107] == "A"  # Eight consecutive control observations, including frame 100.


def test_viterbi_control_boundary_is_offline(controlled_batch):
    labels = infer(controlled_batch, "hmm").labels
    assert labels[99] == "H"
    assert labels[100] == "A"


@pytest.mark.parametrize("model", [state_machine, hmm])
def test_no_state_carry_across_adjacent_halves(controlled_batch, model):
    p = np.r_[np.ones(100, int), np.full(200, 2)]
    ball = controlled_batch.ball.copy()
    ball[100:] = np.nan
    out = model(extract(replace(controlled_batch, period=p, ball=ball)))
    assert set(out[100:]) == {"X"}


@pytest.mark.parametrize("method", ["nearest", "state_machine", "hmm"])
def test_stable_outputs_and_outside_play(controlled_batch, method):
    p = controlled_batch.period.copy()
    p[:15] = 0
    b = replace(controlled_batch, period=p)
    first = infer(b, method).labels
    np.testing.assert_array_equal(first, infer(b, method).labels)
    assert set(first[:15]) == {"X"}


def test_adapter_protocol(controlled_batch):
    class Adapter:
        def load(self):
            return controlled_batch
    np.testing.assert_array_equal(run(Adapter()).labels, infer(controlled_batch).labels)


def test_official_ingestion_disabled():
    with pytest.raises(RuntimeError, match="disabled"):
        OfficialAdapter().load()


@pytest.mark.parametrize("kwargs", [{"hold_seconds": -1}, {"min_reliability": 2},
                                     {"hmm_stay_probability": 1}, {"confirm_seconds": np.nan}])
def test_invalid_model_config(kwargs):
    with pytest.raises(ValueError):
        ModelConfig(**kwargs)


def test_pipeline_has_no_file_access(controlled_batch, monkeypatch):
    import builtins
    from pathlib import Path
    def refuse(*args, **kwargs):
        raise AssertionError("inference tried file access")
    monkeypatch.setattr(builtins, "open", refuse)
    monkeypatch.setattr(Path, "open", refuse)
    infer(controlled_batch, "hmm")
    infer(controlled_batch, "state_machine")


def test_unknown_method(controlled_batch):
    with pytest.raises(ValueError):
        infer(controlled_batch, "neural_net")
