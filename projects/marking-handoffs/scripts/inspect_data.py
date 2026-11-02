from pathlib import Path
import json
from marking_handoffs.data import load_match

ROOT = Path(__file__).resolve().parents[1]
for mid in [1925299, 1996435]:
    d = load_match(ROOT / "data/raw", mid)
    (ROOT / f"outputs/audit-{mid}.json").write_text(json.dumps(d["audit"], indent=2) + "\n")
    print(json.dumps({k: v for k, v in d["audit"].items() if k not in ["sample_record", "schema_keys"]}))
