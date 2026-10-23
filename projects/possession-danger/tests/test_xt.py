import numpy as np
import pandas as pd
import pytest

from possession_danger.xt import XT, cells


def tiny_actions():
    return pd.DataFrame([
        {"match_id": 1, "x": 10, "y": 40, "end_x": 100, "end_y": 40, "type": "Pass", "complete": i < 3, "goal": False}
        for i in range(4)] + [
        {"match_id": 1, "x": 100, "y": 40, "end_x": np.nan, "end_y": np.nan, "type": "Shot", "complete": False, "goal": i == 0}
        for i in range(2)])


def test_substochastic_closed_form_and_failures():
    model = XT(2, 1).fit(tiny_actions())
    assert model.value == pytest.approx([.375, .5])
    assert model.transition[0].sum() == .75
    assert model.residual < 1e-10
    assert model.rate(tiny_actions()).positive_xt.sum() == pytest.approx(.375)


def test_closed_zero_reward_cycle_converges():
    actions = tiny_actions().iloc[:1].copy()
    actions["end_x"] = 10
    model = XT(2, 1).fit(actions)
    assert model.value.tolist() == [0, 0]


def test_grid_edges():
    assert cells([0, 120, 60], [0, 80, 40], 12, 8).tolist() == [0, 95, 54]
    with pytest.raises(ValueError):
        cells([121], [40], 12, 8)


def test_leakage_rejected_and_unseen_cells_reported():
    model = XT(2, 1).fit(tiny_actions())
    with pytest.raises(ValueError, match="leakage"):
        model.evaluate(tiny_actions())
    test = tiny_actions().assign(match_id=2)
    assert model.evaluate(test)["heldout_actions"] == 6


def test_signed_xt_preserves_backward_cost():
    model = XT(2, 1).fit(tiny_actions())
    actions = tiny_actions().iloc[:1].copy()
    actions[["x", "end_x"]] = [100, 10]
    rated = model.rate(actions)
    assert rated.xt_delta.iloc[0] == pytest.approx(-.125)
    assert rated.positive_xt.iloc[0] == 0
