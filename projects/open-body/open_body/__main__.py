from pathlib import Path
import argparse
import json

p = argparse.ArgumentParser()
p.add_argument("stage", choices=["baseline", "orientation", "viewer", "all"])
p.add_argument("--config", default="configs/pilot.json")
a = p.parse_args()
root = Path(__file__).resolve().parents[1]
cfg = json.loads((root / a.config).read_text())
if a.stage in ["baseline", "all"]:
    from .baseline import run

    run(root, cfg)
if a.stage in ["orientation", "all"]:
    from .experiment import run

    run(root, cfg)
if a.stage in ["viewer", "all"]:
    from .viewer import run

    run(root, cfg)
