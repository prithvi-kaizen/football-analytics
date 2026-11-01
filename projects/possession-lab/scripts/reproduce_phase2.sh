#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export MPLCONFIGDIR="$PWD/.mpl-cache"
mkdir -p outputs/phase2
.venv/bin/python -m pip check
.venv/bin/python -m pytest -q | tee outputs/phase2/pytest.txt
.venv/bin/python -m possession_lab.phase2_experiments --history-only
.venv/bin/python -m possession_lab.phase2_experiments
