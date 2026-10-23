"""Build the published portfolio projects without analytics dependencies or network access."""

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "dist"

for project, target in [("pressing-trap-detector", OUTPUT), ("invisible-runner", OUTPUT / "invisible-runner"), ("rest-defence-analyzer", OUTPUT / "rest-defence"),
                        ("pass-decision-lab", OUTPUT / "pass-decision-lab"),
                        ("possession-danger", OUTPUT / "possession-danger"),
                        ("tacticai-lite", OUTPUT / "tacticai-lite")]:
    subprocess.run([sys.executable, str(ROOT / "projects" / project / "scripts/build_website.py"),
                    "--output", str(target)], check=True)
