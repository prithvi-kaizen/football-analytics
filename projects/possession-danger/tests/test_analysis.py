import numpy as np
import pandas as pd
import pytest

from possession_danger.analysis import classify, split_matches, team_matches, team_summary


def test_chronological_split_whole_matches_and_per_league():
    matches = [{"match_id": i, "match_date": f"2024-01-{i:02}", "competition": {"competition_id": 1 if i < 6 else 2}} for i in range(1, 11)]
    split = split_matches(list(reversed(matches)))
    assert sorted(mid for mid, label in split.items() if label == "test") == [5, 10]
    assert len(split) == 10


def test_interpretable_style_edges():
    frame = pd.DataFrame({"elapsed_seconds": [30, 15, 40, 20], "passes": [10, 4, 10, 12],
                          "positive_xt": [.009, .05, .001, .01], "shots": [0, 0, 1, 0]})
    assert classify(frame).tolist() == ["High volume / low threat", "Direct / high threat", "Other", "Other"]


def test_weighted_rate_and_zero_territorial_denominator():
    frame = pd.DataFrame([
        dict(match_id=1, team_id=1, team="A", competition="League", season="2024", date="2024-01-01", split="test", sequence_key="a", active_seconds=10, passes=1, completed_passes=1, final_third_passes=0, shots=0, xg=0, positive_xt=.2, net_xt=.1, turnover_xt=0),
        dict(match_id=1, team_id=2, team="B", competition="League", season="2024", date="2024-01-01", split="test", sequence_key="b", active_seconds=30, passes=1, completed_passes=1, final_third_passes=0, shots=0, xg=0, positive_xt=.1, net_xt=.05, turnover_xt=0)])
    totals = team_matches(frame)
    assert totals.possession_pct.tolist() == [25, 75]
    assert totals.field_tilt.isna().all()
    assert totals.threat_share.sum() == pytest.approx(100)
    second = pd.concat([totals.iloc[:1]] * 2, ignore_index=True)
    second["match_id"] = [1, 2]
    second["positive_xt"] = [.2, .3]
    second["possessions"] = [1, 3]
    assert team_summary(second).xt_per_100.iloc[0] == pytest.approx(12.5)
