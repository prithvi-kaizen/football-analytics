import pytest


@pytest.fixture
def match():
    return {"match_id": 1, "home_team": {"home_team_id": 10, "home_team_name": "Home"},
            "away_team": {"away_team_id": 20, "away_team_name": "Away"}, "home_score": 0, "away_score": 0}


def event(i, kind="Pass", t="00:00:01.000", team=10, owner=10, possession=1, period=1, **extra):
    result = {"id": f"test-{i}", "index": i, "type": {"name": kind}, "timestamp": t, "team": {"id": team, "name": "Home" if team == 10 else "Away"},
              "possession_team": {"id": owner, "name": "Home" if owner == 10 else "Away"}, "possession": possession, "period": period,
              "location": [60, 40], "duration": 1}
    if kind == "Pass":
        result["pass"] = {"end_location": [90, 40]}
    result.update(extra)
    return result
