import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("corner_analysis", Path(__file__).resolve().parents[1] / "src/analyse.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

MATCH = {"match_id": 1, "match_date": "2024-01-01", "tournament": "test", "home_team": {"home_team_id": 1, "home_team_name": "Home"}, "away_team": {"away_team_id": 2, "away_team_name": "Away"}}


def event(idx, sec, typ, team=1, poss=1, **fields):
    return {"id": str(idx), "index": idx, "period": 1, "timestamp": f"00:00:{sec:06.3f}", "minute": 0,
            "type": {"name": typ}, "team": {"id": team, "name": "Home" if team == 1 else "Away"},
            "possession": poss, "possession_team": {"id": poss, "name": "Home" if poss == 1 else "Away"}, **fields}


def corner():
    return event(1, 0, "Pass", **{"pass": {"type": {"name": "Corner"}, "length": 20}})


def test_clearance_does_not_confirm_turnover():
    events = [corner(), event(2, 2, "Clearance", 2), event(3, 3, "Ball Recovery"),
              event(4, 4, "Carry", carry={"end_location": [110, 30]}, location=[90, 30]),
              event(5, 6, "Shot", shot={"statsbomb_xg": .12}), event(6, 18, "Half End")]
    r = mod.episode(events, 0, MATCH, 15)
    assert r["clearance"] and r["recovered"] and not r["confirmed_defense"]
    assert r["second_shots"] == 1 and r["second_box_entries"] == 1


def test_same_timestamp_shot_stays_unknown():
    events = [corner(), event(2, 2, "Duel", 2), event(3, 2, "Shot", shot={"statsbomb_xg": .2}),
              event(4, 20, "Half End")]
    r = mod.episode(events, 0, MATCH, 15)
    assert r["ambiguous_shots"] == 1 and r["second_shots"] == 0 and not r["recovered"]


def test_defender_control_then_counter_shot():
    events = [corner(), event(2, 2, "Clearance", 2), event(3, 4, "Carry", 2, 2),
              event(4, 7, "Shot", 2, 2, shot={"statsbomb_xg": .1}), event(5, 30, "Half End")]
    r = mod.episode(events, 0, MATCH, 15)
    assert r["confirmed_defense"] and r["counter_shots"] == 1 and r["counter_xg"] == .1


def test_duplicate_indexes_rejected():
    events = [corner(), event(1, 2, "Clearance", 2)]
    try:
        mod.validate(events)
    except ValueError:
        pass
    else:
        raise AssertionError("duplicate index accepted")
