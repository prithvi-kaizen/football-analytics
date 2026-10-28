"""Fetch immutable public inputs; save hashes and verify the publisher's pose manifest."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib
import json
import shutil
import urllib.request
import time

ROOT = Path(__file__).resolve().parents[1]
GIT_REV = "4340d274572876239c154c90bc507a9b3250a656"
HF_REV = "a62e1ec1e3b82952042a7f7fa9dafd77c0e0822a"
BASE = f"https://raw.githubusercontent.com/SkillCorner/opendata/{GIT_REV}"
JOBS = []
for m in [1925299, 1996435]:
    for suffix in [
        "match.json",
        "dynamic_events.csv",
        "tracking_extrapolated.jsonl",
        "phases_of_play.csv",
    ]:
        name = f"{m}_{suffix}"
        JOBS.append((f"{BASE}/data/matches/{m}/{name}", ROOT / "data/raw" / name))
    JOBS.append(
        (
            f"https://huggingface.co/datasets/SkillCorner/opendata-bodypose/resolve/{HF_REV}/raw/{m}.jsonl.zip",
            ROOT / f"data/raw/{m}.jsonl.zip",
        )
    )
for name, rel in [
    (
        "pose_tutorial.ipynb",
        "notebooks/tutorials/05_Body_Pose/Part1_Getting_Started_with_Body_Pose.ipynb",
    ),
    ("MANIFEST.json", "data/bodypose/MANIFEST.json"),
    ("data_LICENSE.txt", "LICENSE"),
    ("sample.jsonl.gz", "data/bodypose/sample_1925299_phase406.jsonl.gz"),
]:
    JOBS.append((f"{BASE}/{rel}", ROOT / "docs/source" / name))


def fetch(job):
    url, path = job
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        for attempt in range(3):
            try:
                with (
                    urllib.request.urlopen(url, timeout=90) as src,
                    path.with_suffix(path.suffix + ".part").open("wb") as out,
                ):
                    shutil.copyfileobj(src, out)
                path.with_suffix(path.suffix + ".part").replace(path)
                break
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(2)
    if path.stat().st_size < 200 and path.read_bytes().startswith(
        b"version https://git-lfs"
    ):
        pointer = path.read_text()
        expected = pointer.split("oid sha256:")[1].split()[0]
        media = url.replace(
            "https://raw.githubusercontent.com/",
            "https://media.githubusercontent.com/media/",
        )
        temporary = path.with_suffix(path.suffix + ".media.part")
        with (
            urllib.request.urlopen(media, timeout=120) as src,
            temporary.open("wb") as out,
        ):
            shutil.copyfileobj(src, out)
        assert (
            hashlib.file_digest(temporary.open("rb"), "sha256").hexdigest() == expected
        )
        temporary.replace(path)
    h = hashlib.file_digest(path.open("rb"), "sha256").hexdigest()
    lock_path = ROOT / "data/source-lock.json"
    if lock_path.exists():
        lock = json.loads(lock_path.read_text())
        expected = lock.get(str(path.relative_to(ROOT)))
        if expected and (
            h != expected["sha256"] or path.stat().st_size != expected["bytes"]
        ):
            raise ValueError(f"Corrupt input {path}; remove it and rerun downloader")
    print(path.name, path.stat().st_size, h, flush=True)
    return {
        "file": str(path.relative_to(ROOT)),
        "url": url,
        "bytes": path.stat().st_size,
        "sha256": h,
    }


if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(fetch, JOBS))
    manifest = json.loads((ROOT / "docs/source/MANIFEST.json").read_text())
    for rec in records:
        if rec["file"].endswith(".zip"):
            spec = manifest["files"]["raw/" + Path(rec["file"]).name]
            assert (
                rec["sha256"] == spec["sha256"] and rec["bytes"] == spec["size_bytes"]
            ), rec
    (ROOT / "data/provenance.json").write_text(
        json.dumps(
            {
                "github_revision": GIT_REV,
                "huggingface_revision": HF_REV,
                "files": records,
            },
            indent=2,
        )
        + "\n"
    )
