#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export MPLCONFIGDIR="$PWD/.mpl-cache"
mkdir -p outputs/explorer
.venv/bin/python -m pip check
.venv/bin/python -m pytest -q | tee outputs/explorer/pytest.txt
.venv/bin/python explorer/scripts/vendor_runtime.py
.venv/bin/python explorer/scripts/build.py
.venv/bin/python explorer/scripts/verify_bundle.py
node --check explorer/web/app.js
node --check explorer/web/worker.js

node --test explorer/tests/requests.test.cjs
