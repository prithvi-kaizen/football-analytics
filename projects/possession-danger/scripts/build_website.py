"""Restore the hash-checked static dashboard using only Python's standard library."""

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def checked(path, expected):
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError(f"Integrity check failed: {path}")
    return data


def safe(name):
    if Path(name).is_absolute() or ".." in Path(name).parts:
        raise ValueError("Invalid release path")
    return name


def build(output):
    web = ROOT / "web"
    bundle = json.loads((web / "bundle.json").read_text())
    snapshot = bundle["snapshot"]
    archive = checked(web / safe(snapshot["archive"]), snapshot["archive_sha256"])
    if hashlib.sha256(gzip.decompress(archive)).hexdigest() != snapshot["sha256"]:
        raise ValueError("Snapshot checksum mismatch")
    for name, expected in bundle["assets"].items():
        checked(web / safe(name), expected)
    for item in bundle["downloads"].values():
        checked(ROOT / safe(item["source"]), item["sha256"])
    output.mkdir(parents=True, exist_ok=True)
    for name in bundle["assets"]:
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(web / name, target)
    for name, item in bundle["downloads"].items():
        shutil.copyfile(ROOT / item["source"], output / safe(name))
    (output / safe(snapshot["path"])).write_bytes(archive)
    (output / "release.json").write_text(json.dumps({"snapshot": snapshot["path"], "sha256": snapshot["sha256"]}))
    print(f"Possession danger website built at {output}; integrity checks passed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    build(parser.parse_args().output)
