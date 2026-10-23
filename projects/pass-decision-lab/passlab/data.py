"""Pinned public downloads with verified local caching; no account or API key."""

from __future__ import annotations

import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path, PurePosixPath
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

REVISION = "4b73468fc5b0f1950f9f66fada70ad3a4f9327cb"
BASE_URL = f"https://raw.githubusercontent.com/hudl/open-data/{REVISION}/"
TOURNAMENTS = {"Euro 2024": (55, 282), "Women's Euro 2025": (53, 315)}


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    tmp.replace(path)


class Cache:
    def __init__(self, root: Path, offline: bool = False):
        self.root = Path(root) / REVISION
        self.offline = offline

    def get(self, resource: str):
        pathpart = PurePosixPath(resource)
        if pathpart.is_absolute() or ".." in pathpart.parts or not resource.endswith(".json"):
            raise ValueError("Expected a repository-relative JSON resource")
        path = self.root / resource
        receipt = path.with_suffix(".receipt.json")
        if path.exists():
            if not receipt.exists():
                raise ValueError(f"Unverified cache file: {path}")
            raw = path.read_bytes()
            meta = json.loads(receipt.read_text())
            if meta["sha256"] != hashlib.sha256(raw).hexdigest() or meta["revision"] != REVISION:
                raise ValueError(f"Cache integrity failure: {path}")
            return json.loads(raw)
        if self.offline:
            raise FileNotFoundError(f"Not cached in offline mode: {resource}")
        req = Request(BASE_URL + resource, headers={"User-Agent": "pass-decision-lab/0.1 research"})
        for attempt in range(4):
            try:
                with urlopen(req, timeout=90) as response:
                    raw = response.read()
                obj = json.loads(raw)
                break
            except HTTPError as exc:
                if exc.code not in (429, 500, 502, 503, 504) or attempt == 3:
                    raise
                time.sleep(2**attempt)
            except (URLError, TimeoutError):
                if attempt == 3:
                    raise
                time.sleep(2**attempt)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".download")
        tmp.write_bytes(raw)
        tmp.replace(path)
        write_json(
            receipt,
            {
                "url": BASE_URL + resource,
                "revision": REVISION,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "bytes": len(raw),
            },
        )
        return obj

    def receipts(self):
        return [json.loads(p.read_text()) for p in sorted(self.root.rglob("*.receipt.json"))]


def select_matches(cache: Cache, sample: int | None = 2) -> list[dict]:
    if sample is not None and sample < 1:
        raise ValueError("sample must be positive")
    competitions = cache.get("data/competitions.json")
    selected = []
    for name, (competition_id, season_id) in TOURNAMENTS.items():
        entry = next(
            c for c in competitions if c["competition_id"] == competition_id and c["season_id"] == season_id
        )
        if not entry.get("match_available_360"):
            raise ValueError(f"No 360 advertised for {name}")
        matches = cache.get(f"data/matches/{competition_id}/{season_id}.json")
        matches = sorted(matches, key=lambda m: (m["match_date"], m.get("kick_off", ""), m["match_id"]))
        for m in matches[:sample] if sample else matches:
            selected.append(
                {
                    "match_id": m["match_id"],
                    "tournament": name,
                    "date": m["match_date"],
                    "label": m["home_team"]["home_team_name"] + " vs " + m["away_team"]["away_team_name"],
                }
            )
    return selected


def download_matches(cache: Cache, matches: list[dict]) -> list[dict]:
    def fetch(m):
        events = cache.get(f"data/events/{m['match_id']}.json")
        try:
            frames = cache.get(f"data/three-sixty/{m['match_id']}.json")
        except HTTPError as exc:
            if exc.code != 404:
                raise
            frames = []
        return {"match": m, "events": events, "frames": frames}

    with ThreadPoolExecutor(max_workers=4) as pool:
        return list(pool.map(fetch, matches))
