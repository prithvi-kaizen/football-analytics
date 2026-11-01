from pathlib import Path
import hashlib
import json
import runpy
import shutil

SITE = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    if not (SITE / "web/runtime/SHA256.json").exists():
        raise SystemExit("Run explorer/scripts/vendor_runtime.py before building")
    for name, digest in json.loads((SITE / "web/runtime/SHA256.json").read_text())["files"].items():
        if hashlib.sha256((SITE / "web/runtime" / name).read_bytes()).hexdigest() != digest:
            raise SystemExit("Runtime hash mismatch: " + name)
    (SITE / "dist").mkdir(exist_ok=True)
    for path in (SITE / "web").rglob("*"):
        if path.is_file():
            dest = SITE / "dist" / path.relative_to(SITE / "web")
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, dest)
    runpy.run_path(str(SITE / "scripts/export.py"), run_name="__main__")
