"""Package the validated offline viewer and demo as a small static site."""

from pathlib import Path
import argparse
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]


def build(output):
    output = Path(output).resolve()
    if output in [ROOT, ROOT / "outputs"]:
        raise ValueError("Use a separate website output directory")
    output.mkdir(parents=True, exist_ok=True)
    files = {
        "viewer.html": "index.html",
        "open-body-demo.mp4": "open-body-demo.mp4",
        "results.png": "results.png",
    }
    manifest = {}
    for source, target in files.items():
        path = ROOT / "outputs" / source
        shutil.copyfile(path, output / target)
        manifest[target] = hashlib.sha256(path.read_bytes()).hexdigest()
    shutil.copyfile(
        ROOT / "docs/source/data_LICENSE.txt", output / "SKILLCORNER-LICENSE.txt"
    )
    (output / "vercel.json").write_text(
        json.dumps(
            {
                "version": 2,
                "framework": None,
                "buildCommand": None,
                "outputDirectory": ".",
            },
            indent=2,
        )
        + "\n"
    )
    (output / "build-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Static website written to {output}")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "site")
    build(parser.parse_args().output)
