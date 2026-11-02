#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export MPLCONFIGDIR="$PWD/.mpl-cache"
mkdir -p outputs/validation
.venv/bin/python -m pip check
.venv/bin/python -m pytest -q | tee outputs/validation/pytest.txt
.venv/bin/python -m possession_lab.cli sanity
.venv/bin/python -m possession_lab.cli benchmark
for game in 1 2; do
  base="../public-sample-data/data/Sample_Game_${game}/Sample_Game_${game}_RawTrackingData"
  if [[ -f "${base}_Home_Team.csv" && -f "${base}_Away_Team.csv" ]]; then
    .venv/bin/python -m possession_lab.cli sample --home "${base}_Home_Team.csv" --away "${base}_Away_Team.csv" --out "outputs/sample_game_${game}"
  fi
done
