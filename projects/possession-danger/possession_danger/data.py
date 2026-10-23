from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time

import requests

REVISION = "4b73468fc5b0f1950f9f66fada70ad3a4f9327cb"
BASE = f"https://raw.githubusercontent.com/hudl/open-data/{REVISION}"
LEAGUES = {"liga-f": (182, 281), "wsl": (37, 281), "bundesliga": (135, 281),
           "serie-a": (131, 281), "nwsl": (49, 107)}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    temp.replace(path)


class Cache:
    """Immutable revision cache; corrupt cached files fail instead of silently changing."""

    def __init__(self, root: Path, offline: bool = False):
        self.root = Path(root) / REVISION
        self.offline = offline

    def get(self, relative: str):
        path = self.root / relative
        receipt = path.with_suffix(path.suffix + ".receipt.json")
        if path.exists():
            if not receipt.exists() or json.loads(receipt.read_text())["sha256"] != digest(path):
                raise ValueError(f"Cache integrity failure: {path}. Remove this file and receipt to redownload.")
            return json.loads(path.read_text())
        if self.offline:
            raise FileNotFoundError(f"Not cached: {path}; run download without --offline first.")
        url = f"{BASE}/{relative}"
        for attempt in range(4):
            try:
                response = requests.get(url, timeout=(15, 90), headers={"User-Agent": "possession-danger-research/0.1"})
                response.raise_for_status()
                value = response.json()
                break
            except (requests.RequestException, ValueError):
                if attempt == 3:
                    raise
                time.sleep(2 ** attempt)
        write_json(path, value)
        write_json(receipt, {"url": url, "sha256": digest(path), "bytes": path.stat().st_size,
                             "retrieved_at": datetime.now(timezone.utc).isoformat()})
        return value

    def provenance(self, relative: str) -> dict:
        return json.loads((self.root / relative).with_suffix(".json.receipt.json").read_text())


def catalog(cache: Cache, league: str) -> list[dict]:
    available = cache.get("data/competitions.json")
    comp, season = LEAGUES[league]
    if not any((x["competition_id"], x["season_id"]) == (comp, season) for x in available):
        raise ValueError(f"Competition absent from pinned source: {league}")
    matches = cache.get(f"data/matches/{comp}/{season}.json")
    if len({m["match_id"] for m in matches}) != len(matches):
        raise ValueError("Duplicate match IDs")
    return sorted(matches, key=lambda m: (m["match_date"], m["match_id"]))


def is_barcelona(match: dict) -> bool:
    return "Barcelona" in match["home_team"]["home_team_name"] or "Barcelona" in match["away_team"]["away_team_name"]


def select_matches(matches: list[dict], sample: int | None) -> list[dict]:
    if sample is None:
        return matches
    if sample < 3:
        raise ValueError("Use at least 3 matches for a match-separated smoke test")
    # Include Barcelona in the Liga F smoke test, with unrelated fixtures as a comparison.
    barca = [m for m in matches if is_barcelona(m)]
    other = [m for m in matches if not is_barcelona(m)]
    chosen = barca[:sample // 2] + other[:sample - min(len(barca), sample // 2)]
    return sorted(chosen, key=lambda m: (m["match_date"], m["match_id"]))


def download(cache: Cache, leagues: list[str], sample: int | None, workers: int = 4) -> list[dict]:
    selected = []
    for league in leagues:
        selected.extend(select_matches(catalog(cache, league), sample))
    def fetch(match):
        cache.get(f"data/events/{match['match_id']}.json")
        return match["match_id"]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for i, mid in enumerate(pool.map(fetch, selected), 1):
            if i % 10 == 0 or i == len(selected):
                print(f"Cached {i}/{len(selected)} matches (latest {mid})", flush=True)
    return selected
