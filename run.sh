
#!/usr/bin/env bash
# Usage: ./run.sh [setup|fetch|build|test|all]
#   setup  install core Python dependencies
#   fetch  download UK Police bicycle theft data
#   build  prepare map and rebuild DuckDB + HTML dashboard
#   test   run tests without downloading geographical data
#   all    prepare map, run tests and build dashboard

set -euo pipefail

cd "$(dirname "$0")"

PY=".venv/bin/python"
PIP=".venv/bin/pip"

setup() {
  if [ ! -d .venv ]; then
    python3 -m venv .venv
  fi

  "$PIP" install -q -r requirements.txt
}

setup_geo() {
  "$PIP" install -q -r requirements-geo.txt
}

prepare_map() {
  setup_geo

  echo "Checking geographical data..."
  "$PY" scripts/setup_geography.py

  echo "Generating London map..."
  "$PY" scripts/generate_london_map.py
}

build_pipeline() {
  prepare_map

  echo "Building DuckDB warehouse and dashboard..."
  "$PY" -m pipeline.build
}

case "${1:-all}" in
  setup)
    setup
    ;;
  fetch)
    setup
    "$PY" -m pipeline.fetch --months "${@:2}"
    ;;
  build)
    setup
    build_pipeline
    ;;
  test)
    setup
    "$PY" -m pytest -q
    ;;
  all)
    setup
    build_pipeline
    "$PY" -m pytest -q
    ;;
  *)
    sed -n '2,8p' "$0"
    exit 1
    ;;
esac
