from dataclasses import asdict, replace
from itertools import product

import numpy as np
import pytest

from possession_lab.features import extract
from possession_lab.hierarchical import (HierarchicalConfig, decode_chain, hierarchical,
                                         observation_heads, transition_matrix)
from possession_lab.phase1_experiments import methods, verify_legacy
from possession_lab.pipeline import infer


def test_original_sources_are_intact():
    assert verify_legacy()["unchanged_source_files"] == 4


@pytest.mark.parametrize("kwargs", [{"live_mean_s": 0}, {"stationarity_weight": -1},
                                     {"evidence_power": np.nan}, {"missing_masks": "false"}])
def test_bad_hierarchy_config(kwargs):
    with pytest.raises(ValueError):
        HierarchicalConfig(**kwargs)


def test_joint_decoder_matches_exhaustive_probabilities():
    rng = np.random.default_rng(7)
    e = rng.normal(size=(4, 4))
    t = transition_matrix(25)
    states = np.array(list(product(range(4), repeat=4)))
    log_weight = np.array([-np.log(4) + sum(e[i, x] for i, x in enumerate(path))
        + sum(np.log(t[path[i - 1], path[i]]) for i in range(1, len(path))) for path in states])
    probabilities = np.exp(log_weight - log_weight.max())
    probabilities /= probabilities.sum()
    expected = np.array([[probabilities[states[:, i] == j].sum() for j in range(4)] for i in range(4)])
    path, posterior = decode_chain(e, t)
    np.testing.assert_array_equal(path, states[np.argmax(log_weight)])
    np.testing.assert_allclose(posterior, expected, atol=1e-12)


def test_neutral_missing_observations_are_not_dead_evidence(controlled_batch):
    b = controlled_batch
    missing = replace(b, ball=np.full_like(b.ball, np.nan), home=np.full_like(b.home, np.nan),
                       away=np.full_like(b.away, np.nan))
    f = extract(missing)
    live, owner, e = observation_heads(f)
    np.testing.assert_allclose(live, 0.5)
    np.testing.assert_allclose(owner, 0.5)
    np.testing.assert_allclose(e, 0)
    assert set(hierarchical(f).labels) == {"X"}
    assert np.isfinite(hierarchical(f).posterior).all()


def test_missing_negative_control_changes_only_evidence(controlled_batch):
    ball = controlled_batch.ball.copy()
    ball[30:60] = np.nan
    f = extract(replace(controlled_batch, ball=ball))
    good = observation_heads(f)[0]
    bad = observation_heads(f, HierarchicalConfig(missing_masks=False))[0]
    assert np.all(bad[30:60] < good[30:60])
    np.testing.assert_allclose(good[:30], bad[:30])


def test_transition_factors_are_independently_ablatable():
    full = transition_matrix(25)
    no_owner = transition_matrix(25, HierarchicalConfig(possession_continuity=False))
    no_duration = transition_matrix(25, HierarchicalConfig(duration_priors=False))
    for t in (full, no_owner, no_duration):
        np.testing.assert_allclose(t.sum(axis=1), 1)
        assert (t > 0).all()
    # Marginal live/dead transition probabilities stay fixed when owner continuity is removed.
    np.testing.assert_allclose(full.reshape(2, 2, 2, 2).sum(axis=3), no_owner.reshape(2, 2, 2, 2).sum(axis=3))
    np.testing.assert_allclose(no_duration.reshape(2, 2, 2, 2).sum(axis=3), 0.5)
    assert not np.allclose(full, no_duration)


def test_ablation_definitions_and_determinism(controlled_batch):
    runners = methods(asdict(HierarchicalConfig()))
    assert len(runners) == 10
    f = extract(controlled_batch)
    for runner in runners.values():
        a, b = runner(f), runner(f)
        np.testing.assert_array_equal(a.labels if hasattr(a, "labels") else a,
                                      b.labels if hasattr(b, "labels") else b)


def test_new_pipeline_interface_and_period_reset(controlled_batch):
    p = np.r_[np.ones(100, int), np.zeros(100, int), np.full(100, 2)]
    ball = controlled_batch.ball.copy()
    ball[200:] = np.nan
    result = infer(replace(controlled_batch, period=p, ball=ball), "hierarchical")
    assert set(result.labels[100:]) == {"X"}
    np.testing.assert_allclose(result.probabilities.posterior[:100].sum(axis=1), 1)
    assert np.isnan(result.probabilities.posterior[100:200]).all()


def test_hierarchy_no_file_access(controlled_batch, monkeypatch):
    import builtins
    from pathlib import Path
    def refuse(*args, **kwargs):
        raise AssertionError("hierarchy attempted to access files")
    monkeypatch.setattr(builtins, "open", refuse)
    monkeypatch.setattr(Path, "open", refuse)
    infer(controlled_batch, "hierarchical")
