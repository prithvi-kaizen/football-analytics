#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON_BIN="${PYTHON_BIN:-.venv/bin/python}"
export PYTHONPATH=.
"$PYTHON_BIN" scripts/prepare_data.py "$@"
"$PYTHON_BIN" scripts/inspect_data.py
"$PYTHON_BIN" -m unittest discover -s tests -v
"$PYTHON_BIN" scripts/run_baseline.py
"$PYTHON_BIN" scripts/run_experiment.py
"$PYTHON_BIN" scripts/build_viewer.py
"$PYTHON_BIN" scripts/render_demo.py
"$PYTHON_BIN" scripts/build_report.py
"$PYTHON_BIN" scripts/verify_exports.py
