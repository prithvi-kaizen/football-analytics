import json
from pathlib import Path
import pytest

from possession_danger.data import Cache, REVISION, select_matches


def test_cache_is_pinned_integrity_checked_and_offline(tmp_path, monkeypatch):
    calls = []
    class Response:
        def raise_for_status(self):
            pass
        def json(self):
            return [{"id": 3}]
    def get(url, **kwargs):
        calls.append(url)
        return Response()
    monkeypatch.setattr("requests.get", get)
    cache = Cache(tmp_path)
    assert cache.get("data/example.json") == [{"id": 3}]
    assert REVISION in calls[0]
    assert Cache(tmp_path, offline=True).get("data/example.json") == [{"id": 3}]
    assert len(calls) == 1
    (cache.root / "data/example.json").write_text("[]")
    with pytest.raises(ValueError, match="integrity"):
        cache.get("data/example.json")
    with pytest.raises(FileNotFoundError):
        Cache(tmp_path, offline=True).get("data/missing.json")


def test_sample_is_deterministic_and_includes_barcelona():
    matches = [{"match_id": i, "match_date": f"2024-01-{i:02}", "home_team": {"home_team_name": "Barcelona" if i > 5 else "Other"}, "away_team": {"away_team_name": "Rival"}} for i in range(1, 11)]
    sample = select_matches(matches, 6)
    assert [m["match_id"] for m in sample] == [1, 2, 3, 6, 7, 8]
    assert select_matches(matches, None) == matches
    with pytest.raises(ValueError):
        select_matches(matches, 1)
