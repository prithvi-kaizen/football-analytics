"""Pinned provider downloads, atomic cache and content-addressed provenance."""
from __future__ import annotations

import hashlib
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import requests

REVISION = "4b73468fc5b0f1950f9f66fada70ad3a4f9327cb"
BASE = f"https://raw.githubusercontent.com/statsbomb/open-data/{REVISION}"
TOURNAMENTS = {"euro2024": (55, 282, "Men's Euro 2024"), "weuro2025": (53, 315, "Women's Euro 2025")}


class DataError(ValueError):
    """Input cannot safely be interpreted as provider data."""


class Store:
    def __init__(self, root: Path | str, offline: bool = False):
        self.root = Path(root)
        self.offline = offline

    def get(self, relative: str, optional: bool = False):
        path = self.root / relative
        receipt = path.with_suffix('.receipt.json')
        if path.exists():
            payload = path.read_bytes()
            if receipt.exists():
                saved = json.loads(receipt.read_text())
                if saved['revision'] != REVISION or saved['sha256'] != hashlib.sha256(payload).hexdigest():
                    raise DataError(f"Cache integrity failure: {path}. Remove this file and its receipt, then download again.")
            else:
                # A cache entry without provenance must not masquerade as pinned data.
                raise DataError(f"Unverified cache entry: {path}; remove it and download through the pipeline.")
            return json.loads(payload)
        if self.offline:
            if optional and receipt.exists():
                saved = json.loads(receipt.read_text())
                if saved.get('revision') == REVISION and saved.get('status') == 404:
                    return None
            raise FileNotFoundError(f"Not cached: {path}; rerun without --offline.")
        url = f"{BASE}/{relative}"
        for attempt in range(3):
            try:
                response = requests.get(url, timeout=(15, 120))
                if optional and response.status_code == 404:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    receipt.write_text(json.dumps({'url': url, 'revision': REVISION, 'status': 404,
                        'retrieved_utc': datetime.now(timezone.utc).isoformat()}, indent=2))
                    return None
                response.raise_for_status()
                payload = response.content
                parsed = json.loads(payload)
                if not isinstance(parsed, list):
                    raise DataError(f"Expected a JSON array at {url}")
                break
            except (requests.RequestException, ValueError):
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix('.tmp')
        temp.write_bytes(payload)
        os.replace(temp, path)
        receipt.write_text(json.dumps({"url": url, "revision": REVISION,
            "sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload),
            "retrieved_utc": datetime.now(timezone.utc).isoformat()}, indent=2))
        return parsed


def unique_records(records, key):
    seen = set()
    for row in records:
        if key not in row or row[key] in seen:
            raise DataError(f"Missing or duplicate {key}")
        seen.add(row[key])
    return records


def select_matches(store: Store, tournaments, sample: int | None = 1):
    if sample is not None and sample < 1:
        raise ValueError("sample must be positive")
    competitions = store.get('data/competitions.json')
    selected = []
    for tournament in tournaments:
        comp, season, label = TOURNAMENTS[tournament]
        if not any(c['competition_id'] == comp and c['season_id'] == season for c in competitions):
            raise DataError(f"Competition/season absent: {tournament}")
        matches = unique_records(store.get(f'data/matches/{comp}/{season}.json'), 'match_id')
        matches = sorted(matches, key=lambda m: (m['match_date'], m['match_id']))
        for match in matches[:sample] if sample else matches:
            selected.append({**match, 'tournament': label})
    return selected


def download_matches(store, matches, workers=4):
    def download(match):
        match_id = match['match_id']
        events = unique_records(store.get(f'data/events/{match_id}.json'), 'id')
        frames = store.get(f'data/three-sixty/{match_id}.json', optional=True)
        if frames is not None:
            unique_records(frames, 'event_uuid')
            if not {f['event_uuid'] for f in frames}.issubset({e['id'] for e in events}):
                raise DataError(f"360 frames without matching events: {match_id}")
        return match, events, frames or []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(download, matches))


def manifest(store):
    return [json.loads(p.read_text()) for p in sorted(store.root.rglob('*.receipt.json'))]
