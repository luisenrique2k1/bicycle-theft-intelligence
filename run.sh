#!/usr/bin/env bash
# Usage: ./run.sh [setup|fetch|build|test|all]
#   setup  create .venv and install requirements
#   fetch  download raw data from data.police.uk into data/raw (needs internet; skips files already present)
#   build  rebuild warehouse.duckdb from data/raw, run quality checks, write reports/report.html
#   test   run the test-suite (uses synthetic fixtures, no internet needed)
#   all    setup + test + build  (works from a clean clone using the committed raw data)
set -euo pipefail
cd "$(dirname "$0")"
PY=".venv/bin/python"
setup() { [ -d .venv ] || python3 -m venv .venv; .venv/bin/pip install -q -r requirements.txt; }
case "${1:-all}" in
  setup) setup ;;
  fetch) setup; $PY -m pipeline.fetch --months "${@:2}" ;;
  build) setup; $PY -m pipeline.build ;;
  test)  setup; $PY -m pytest -q ;;
  all)   setup; $PY -m pytest -q; $PY -m pipeline.build ;;
  *) sed -n '2,8p' "$0"; exit 1 ;;
esac
