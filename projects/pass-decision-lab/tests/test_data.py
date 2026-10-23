import hashlib
from urllib.error import HTTPError

import pytest

from passlab.data import BASE_URL, REVISION, Cache, download_matches, write_json


def test_verified_offline_cache(tmp_path):
    resource = "data/events/1.json"
    path = tmp_path / REVISION / resource
    write_json(path, [{"id": "fixture"}])
    write_json(
        path.with_suffix(".receipt.json"),
        {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "revision": REVISION},
    )
    assert Cache(tmp_path, offline=True).get(resource) == [{"id": "fixture"}]
    path.write_text("[]")
    with pytest.raises(ValueError, match="integrity"):
        Cache(tmp_path, offline=True).get(resource)


def test_missing_unverified_and_unsafe_cache(tmp_path):
    cache = Cache(tmp_path, offline=True)
    with pytest.raises(FileNotFoundError):
        cache.get("data/events/1.json")
    write_json(cache.root / "data/events/1.json", [])
    with pytest.raises(ValueError, match="Unverified"):
        cache.get("data/events/1.json")
    for name in ["../secrets.json", "/tmp/a.json", "file.csv"]:
        with pytest.raises(ValueError):
            cache.get(name)
    assert REVISION in BASE_URL


def test_missing_360_only_swallows_404():
    class MissingFrameCache:
        def get(self, resource):
            if "/events/" in resource:
                return []
            raise HTTPError("fixture", 404, "Not found", None, None)

    assert download_matches(MissingFrameCache(), [{"match_id": 1}])[0]["frames"] == []
