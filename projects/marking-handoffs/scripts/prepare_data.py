"""Fetch pinned public files, or verify and copy an existing local cache."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
REVISION = "4340d274572876239c154c90bc507a9b3250a656"
MATCHES = [1925299, 1996435]


def digest(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", type=Path, help="Existing raw SkillCorner directory")
    args = parser.parse_args()
    tree = json.loads((ROOT / "docs/source/upstream-tree.json").read_text())
    blobs = {x["path"]: x["sha"] for x in tree["tree"]}
    receipts = []
    for mid in MATCHES:
        for suffix in ["match.json", "phases_of_play.csv", "tracking_extrapolated.jsonl"]:
            name = f"{mid}_{suffix}"
            path = ROOT / "data/raw" / name
            repo_path = f"data/matches/{mid}/{name}"
            host = "media.githubusercontent.com/media" if suffix.endswith("jsonl") else "raw.githubusercontent.com"
            url = f"https://{host}/SkillCorner/opendata/{REVISION}/{repo_path}"
            if not path.exists():
                part = path.with_suffix(path.suffix + ".part")
                try:
                    if args.cache:
                        shutil.copyfile(args.cache / name, part)
                    else:
                        with urlopen(url, timeout=120) as response, part.open("wb") as out:
                            shutil.copyfileobj(response, out)
                    part.replace(path)
                finally:
                    part.unlink(missing_ok=True)
            sha = digest(path)
            if suffix.endswith("jsonl"):
                pointer = (ROOT / f"docs/source/{mid}.lfs").read_text().splitlines()
                expected = pointer[1].split(":")[1]
                expected_size = int(pointer[2].split()[1])
                if sha != expected or path.stat().st_size != expected_size:
                    raise ValueError(f"LFS hash/size mismatch: {path}")
            else:
                data = path.read_bytes()
                git_hash = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
                if git_hash != blobs[repo_path]:
                    raise ValueError(f"Git blob mismatch: {path}")
            receipts.append(dict(file=str(path.relative_to(ROOT)), url=url,
                                 bytes=path.stat().st_size, sha256=sha, verified=True))
    (ROOT / "data/provenance.json").write_text(json.dumps(dict(revision=REVISION, files=receipts), indent=2) + "\n")
    print(json.dumps(dict(files_verified=len(receipts), revision=REVISION)))


if __name__ == "__main__":
    main()
