from dataclasses import replace

import numpy as np
import pytest

from possession_lab.event_fusion import FusionConfig, event_evidence, fuse_events, infer_events
from possession_lab.event_worlds import generate_twins
from possession_lab.features import extract
from possession_lab.hierarchical import hierarchical
from possession_lab.synthetic_tags import uninformative_tags
from possession_lab.tagging_interface import PhaseInterval


def tag(start=70, stop=100, code="stoppage signal", team=None):
    return PhaseInterval(start, stop, code, team, 1, (), None)


def test_tagless_and_disabled_operation_is_exact(controlled_batch):
    f = extract(controlled_batch)
    baseline = hierarchical(f)
    for result in (fuse_events(f), fuse_events(f, (tag(),), enabled=False),
                   fuse_events(f, (tag(),), cfg=FusionConfig(power=0))):
        np.testing.assert_array_equal(result.labels, baseline.labels)
        np.testing.assert_array_equal(result.posterior, baseline.posterior)


def test_completely_uninformative_semantic_weights_are_neutral(controlled_batch):
    f = extract(controlled_batch)
    result = fuse_events(f, (tag(),), cfg=FusionConfig(stop_probability=0.5, restart_probability=0.5, team_probability=0.5))
    np.testing.assert_array_equal(result.labels, hierarchical(f).labels)
    np.testing.assert_allclose(result.tag_live_log_odds, 0)
    assert not result.event_support.any()


def test_exact_duplicates_do_not_multiply_evidence(controlled_batch):
    f = extract(controlled_batch)
    a, b = fuse_events(f, (tag(),)), fuse_events(f, (tag(),) * 20)
    np.testing.assert_array_equal(a.posterior, b.posterior)


def test_conflicts_are_bounded_and_team_is_conditional(controlled_batch):
    f = extract(controlled_batch)
    tags = (tag(code="set pieces", team="H"), tag(code="set pieces", team="A"), tag())
    live, home, _ = event_evidence(f, tags)
    assert np.max(np.abs(live)) <= FusionConfig().max_log_odds
    np.testing.assert_allclose(home, 0)
    unknown = event_evidence(f, (tag(code="set pieces"),))[1]
    np.testing.assert_allclose(unknown, 0)


def test_conservative_requires_corroboration_and_preserves_uncertain_timing(controlled_batch):
    f = extract(controlled_batch)
    single = event_evidence(f, (tag(),), "conservative")[0]
    np.testing.assert_allclose(single, 0)
    pair = event_evidence(f, (tag(), tag(180, 220, "set pieces")), "conservative")[0]
    assert pair[130] < 0 and pair[20] == 0 and pair[250] == 0
    assert 0 > pair[85] > pair[130]


def test_no_evidence_or_support_crosses_periods(controlled_batch):
    p = np.r_[np.ones(130, int), np.zeros(40, int), np.full(130, 2)]
    f = extract(replace(controlled_batch, period=p))
    evidence = event_evidence(f, (tag(),))[0]
    np.testing.assert_allclose(evidence[130:], 0)
    with pytest.raises(ValueError):
        fuse_events(f, (tag(100, 180),))


def test_null_twin_tags_cannot_exceed_chance_and_fusion_does_not_read_truth():
    live, dead = generate_twins("invisible", 51)
    tags = uninformative_tags(live.tracking.period, 53)
    a = infer_events(live.tracking, tags)
    b = infer_events(dead.tracking, tags)
    np.testing.assert_array_equal(a.labels, b.labels)
    balanced = ((a.labels[live.target] == live.truth[live.target]).mean()
                 + (b.labels[dead.target] == dead.truth[dead.target]).mean()) / 2
    assert balanced <= 0.5


def test_event_fusion_no_file_access(controlled_batch, monkeypatch):
    import builtins
    from pathlib import Path
    def refuse(*args, **kwargs):
        raise AssertionError("event inference attempted file access")
    monkeypatch.setattr(builtins, "open", refuse)
    monkeypatch.setattr(Path, "open", refuse)
    infer_events(controlled_batch, (tag(),))
