#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
PYTHON_EXECUTABLE="${1:-python3}"
export PYTHONPATH=.
"$PYTHON_EXECUTABLE" scripts/prepare_data.py
"$PYTHON_EXECUTABLE" scripts/audit_data.py
"$PYTHON_EXECUTABLE" -m unittest discover -s tests -v
"$PYTHON_EXECUTABLE" scripts/run_analysis.py
"$PYTHON_EXECUTABLE" scripts/export_replays.py
"$PYTHON_EXECUTABLE" scripts/build_report.py
"$PYTHON_EXECUTABLE" scripts/render_demo.py
"$PYTHON_EXECUTABLE" scripts/verify_outputs.py
"$PYTHON_EXECUTABLE" scripts/build_website.py
