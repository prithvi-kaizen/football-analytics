#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON="${OPEN_BODY_PYTHON:-python3}"
"$PYTHON" -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python scripts/download_data.py
.venv/bin/python -m pytest -q tests/test_baseline.py
.venv/bin/python -m open_body baseline
.venv/bin/python -m open_body orientation
.venv/bin/python -m pytest -q
.venv/bin/python -m open_body viewer
.venv/bin/python scripts/render_demo.py
