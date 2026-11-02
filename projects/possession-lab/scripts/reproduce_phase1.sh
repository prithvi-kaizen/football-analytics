#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export MPLCONFIGDIR="$PWD/.mpl-cache"
mkdir -p outputs/phase1
.venv/bin/python -m pip check
.venv/bin/python -m pytest -q | tee outputs/phase1/pytest.txt
.venv/bin/python - <<'PY'
import json
from pathlib import Path
from possession_lab.phase1_experiments import verify_legacy
receipt = verify_legacy(recompute=True)
Path('outputs/phase1/legacy_regression.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(receipt)
PY
.venv/bin/python -m possession_lab.cli phase1
