"""Bind frozen results to a self-contained viewer; no browser-side model fitting."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
payload = dict(clips=json.loads((ROOT / "outputs/replays.json").read_text()),
               results=json.loads((ROOT / "outputs/results.json").read_text()))
data = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
template = (ROOT / "viewer/template.html").read_text()
assert template.count("__DATA_JSON__") == 1
(ROOT / "outputs/marking-handoffs.html").write_text(template.replace("__DATA_JSON__", data))
print("Built outputs/marking-handoffs.html", len(payload["clips"]), "candidate replays")
