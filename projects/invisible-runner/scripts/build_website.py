"""Restore a checked static release. Standard library only; no data downloads."""

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def checked(path, digest):
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != digest:
        raise ValueError(f"Integrity check failed: {path.name}")
    return data


def build(output):
    web = ROOT / "web"
    bundle = json.loads((web / "bundle.json").read_text())
    snapshot = bundle["snapshot"]
    if Path(snapshot["path"]).name != snapshot["path"]:
        raise ValueError("Invalid snapshot filename")
    compressed = checked(web / snapshot["archive"], snapshot["archive_sha256"])
    data = gzip.decompress(compressed)
    if hashlib.sha256(data).hexdigest() != snapshot["sha256"]:
        raise ValueError("Snapshot integrity check failed")
    for name, digest in bundle["assets"].items():
        if Path(name).is_absolute() or ".." in Path(name).parts:
            raise ValueError("Invalid asset path")
        checked(web / name, digest)
    output.mkdir(parents=True, exist_ok=True)
    for name in bundle["assets"]:
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(web / name, target)
    (output / snapshot["path"]).write_bytes(compressed)
    (output / "release.json").write_text(json.dumps({"snapshot": snapshot["path"], "encoding": "gzip", "sha256": snapshot["sha256"]}))
    for name in ["runs.csv", "sensitivity.csv", "provenance.json", "findings.md", "space-change.png", "space-change.svg"]:
        shutil.copyfile(ROOT / "outputs/1886347-full" / name, output / name)
    shutil.copyfile(ROOT / "docs/source/LICENSE", output / "LICENSE-skillcorner.txt")
    print(f"Invisible Runner website built: {bundle['profiles']}; integrity checks passed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    build(parser.parse_args().output)
