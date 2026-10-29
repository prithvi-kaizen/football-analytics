"""Run this before adding or evaluating any proposed assignment method."""
import json
from pathlib import Path
from marking_handoffs.data import load_match
from marking_handoffs.baseline import build_segments, nearest, independent_check, summary

ROOT = Path(__file__).resolve().parents[1]
cfg = json.loads((ROOT / "configs/pilot.json").read_text())
results = {}
for split in ["development", "heldout"]:
    mid = cfg[f"{split}_match"]
    data = load_match(ROOT / "data/raw", mid)
    segments = build_segments(data, cfg)
    labels = [nearest(s["distance"]) for s in segments]
    results[split] = dict(match_id=mid, metrics=summary(segments, labels),
                          validation=independent_check(data, segments, labels))
    print(split, results[split])
(ROOT / "outputs/baseline-validation.json").write_text(json.dumps(results, indent=2) + "\n")
