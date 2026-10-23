"""Restore the reviewed static companion using only Python's standard library."""

import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build(output):
    web = ROOT / "web"
    bundle = json.loads((web / "bundle.json").read_text())
    checked = []
    for name, expected in bundle["assets"].items():
        rel = Path(name)
        if rel.is_absolute() or ".." in rel.parts:
            raise ValueError("Unsafe release path")
        source = web / rel
        if hashlib.sha256(source.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Release integrity failure: {name}")
        checked.append((source, output / rel))
    for source, target in checked:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    print(f"Pass Decision Lab: {bundle['caseCount']} analytical cases; all asset hashes verified.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    build(parser.parse_args().output)
