from dataclasses import asdict, replace

import numpy as np
import pytest

from possession_lab.event_worlds import ActionCue, PrivateAction, generate_world, generate_twins, rule_labels
from possession_lab.synthetic_tags import AnnotationConfig, observe_actions, relocate_tags, uninformative_tags


def test_private_rulings_change_truth_but_not_annotations():
    period = np.ones(200, int)
    cues = [ActionCue(50, "stop_gesture", "H", 1), ActionCue(140, "restart_attempt", "A", 1)]
    allowed = [PrivateAction(c, True) for c in cues]
    forbidden = [PrivateAction(c, False) for c in cues]
    assert not np.array_equal(rule_labels(period, allowed), rule_labels(period, forbidden))
    cfg = AnnotationConfig(missing_rate=0, false_events_per_s=0)
    a = observe_actions(tuple(x.cue for x in allowed), period, 4, cfg)
    b = observe_actions(tuple(x.cue for x in forbidden), period, 4, cfg)
    assert a == b  # The sensor cannot inspect the permission bit or truth boundaries.
    assert all(x.confidence is None for x in a)


def test_restart_attempt_is_not_itself_a_label():
    p = np.ones(200, int)
    actions = [PrivateAction(ActionCue(40, "stop_gesture", None, 1), True),
               PrivateAction(ActionCue(70, "restart_attempt", "A", 1), False),
               PrivateAction(ActionCue(120, "restart_attempt", "A", 1), True)]
    y = rule_labels(p, actions)
    assert y[39] == "H" and y[70] == "D" and y[120] == "A"


@pytest.mark.parametrize("family", ["episodes", "renewal"])
def test_world_and_annotation_reproduction(family):
    a, b = generate_world(family, 501), generate_world(family, 501)
    np.testing.assert_array_equal(a.truth, b.truth)
    np.testing.assert_array_equal(a.tracking.ball, b.tracking.ball)
    assert a.actions == b.actions
    assert observe_actions(a.visible_cues(), a.tracking.period, 61) == observe_actions(b.visible_cues(), b.tracking.period, 61)
    assert set(a.truth) <= set("HADX")


def test_independent_generators_and_rulings_are_not_tag_payload():
    a, b = generate_world("episodes", 501), generate_world("renewal", 501)
    assert a.actions != b.actions
    assert not np.array_equal(a.tracking.ball, b.tracking.ball, equal_nan=True)
    tags = observe_actions(a.visible_cues(), a.tracking.period, 71)
    for event in tags:
        assert not set(asdict(event)) & {"allowed", "truth", "dead_duration", "correct", "latent_id"}


def test_missing_detections_and_false_positives_are_separate():
    period = np.ones(1000, int)
    cues = (ActionCue(100, "stop_gesture", None, 1),)
    assert not observe_actions(cues, period, 3, AnnotationConfig(missing_rate=1, false_events_per_s=0))
    false = observe_actions((), period, 3, AnnotationConfig(false_events_per_s=1))
    assert len(false) > 0 and all(x.confidence is None for x in false)


def test_duplicate_conflict_and_temporal_noise_controls():
    p = np.ones(1000, int)
    cues = tuple(ActionCue(i, "restart_attempt", "H", 1) for i in range(100, 900, 100))
    cfg = AnnotationConfig(missing_rate=0, false_events_per_s=0, duplicate_rate=1, conflict_rate=1,
                            unknown_team=0, wrong_team=1, offset_s=0, delay_s=2)
    tags = observe_actions(cues, p, 18, cfg)
    assert len(tags) == 24
    assert len(set(tags)) < len(tags)
    assert {x.code for x in tags} >= {"set pieces", "stoppage signal"}
    assert all(0 <= x.start < x.stop <= len(p) for x in tags)
    assert min(x.start for x in tags) > 100


@pytest.mark.parametrize("mode", ["shuffle", "shift"])
def test_controls_preserve_observed_contents_and_widths(mode):
    p = np.ones(1000, int)
    tags = uninformative_tags(p, 4, events_per_s=1)
    control = relocate_tags(tags, p, 41, mode)
    signature = lambda t: sorted((e.stop-e.start, e.code, e.team_hint or "", e.tags) for e in t)
    assert signature(tags) == signature(control)
    assert tags != control


@pytest.mark.parametrize("kind", ["static", "invisible"])
def test_twins_have_equal_tracking_and_extra_actions(kind):
    live, dead = generate_twins(kind, 45)
    assert live.tracking is dead.tracking
    assert live.visible_cues() != dead.visible_cues()
    np.testing.assert_array_equal(rule_labels(dead.tracking.period, dead.actions), dead.truth)
    # Random tags share precisely the same payload, including when true worlds disagree.
    assert uninformative_tags(live.tracking.period, 88) == uninformative_tags(dead.tracking.period, 88)


@pytest.mark.parametrize("kwargs", [{"missing_rate": 2}, {"width_s": 0}, {"delay_s": np.nan}])
def test_invalid_sensor_config(kwargs):
    with pytest.raises(ValueError):
        AnnotationConfig(**kwargs)
