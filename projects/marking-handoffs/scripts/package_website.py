"""Package only the validated public viewer and its attribution for static hosting."""
from pathlib import Path
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
destination = ROOT / "web"
destination.mkdir(exist_ok=True)
for source, name in [
    ("outputs/marking-handoffs.html", "index.html"),
    ("outputs/marking-handoffs-demo.mp4", "marking-handoffs-demo.mp4"),
    ("docs/source/LICENSE.skillcorner", "LICENSE.skillcorner"),
]:
    shutil.copyfile(ROOT / source, destination / name)
(destination / "vercel.json").write_text(json.dumps({
    "version": 2,
    "framework": None,
    "installCommand": "",
    "buildCommand": "",
    "outputDirectory": ".",
}, indent=2) + "\n")
print(destination)
