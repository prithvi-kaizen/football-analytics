"""Fetch only the 82 pinned event files needed for this project; no 360 frames."""
import hashlib
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REVISION="4b73468fc5b0f1950f9f66fada70ad3a4f9327cb"
BASE=f"https://raw.githubusercontent.com/hudl/open-data/{REVISION}/data"
DEST=ROOT/"data/raw/data"


def get(relative):
    dest=DEST/relative
    receipt=dest.with_suffix(".receipt.json")
    if dest.exists() and receipt.exists():
        payload=dest.read_bytes(); info=json.loads(receipt.read_text())
        if info.get("revision")==REVISION and info.get("sha256")==hashlib.sha256(payload).hexdigest():
            return json.loads(payload)
        raise ValueError(f"Cache integrity failure: {dest}")
    url=f"{BASE}/{relative}"
    with urllib.request.urlopen(url,timeout=90) as response:
        payload=response.read()
    value=json.loads(payload)
    if not isinstance(value,list):
        raise ValueError(f"Expected JSON array: {url}")
    dest.parent.mkdir(parents=True,exist_ok=True)
    temp=dest.with_suffix(".tmp")
    temp.write_bytes(payload)
    temp.replace(dest)
    receipt.write_text(json.dumps({"url":url,"revision":REVISION,"sha256":hashlib.sha256(payload).hexdigest(),"bytes":len(payload),"retrieved_utc":datetime.now(timezone.utc).isoformat()},indent=2))
    return value


def main():
    competitions=get("competitions.json")
    selected=((55,282),(53,315))
    if not all(any(c["competition_id"]==cid and c["season_id"]==sid for c in competitions) for cid,sid in selected):
        raise ValueError("Pinned competition/season is missing")
    matches=[]
    for cid,sid in selected:
        matches.extend(get(f"matches/{cid}/{sid}.json"))
    ids=[m["match_id"] for m in matches]
    if len(ids)!=82 or len(ids)!=len(set(ids)):
        raise ValueError(f"Expected 82 distinct matches, found {len(ids)}")
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(lambda mid:get(f"events/{mid}.json"),ids))
    print(f"Verified {len(ids)} matches at revision {REVISION}")


if __name__=="__main__":
    main()
