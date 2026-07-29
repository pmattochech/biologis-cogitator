#!/usr/bin/env bash
# Copy Codex tools/castra-biogen → biologis-cogitator (Codex tree untouched).
set -euo pipefail

SRC="${1:-/home/paulom/Codex-Batavi/tools/castra-biogen}"
DST="${2:-/home/paulom/biologis-cogitator}"

if [[ ! -d "$SRC" ]]; then
  echo "source missing: $SRC" >&2
  exit 1
fi
if [[ ! -d "$DST" ]]; then
  echo "destination missing (create_project first): $DST" >&2
  exit 1
fi
if [[ ! -f "$SRC/run" ]]; then
  echo "source does not look like castra-biogen (no ./run): $SRC" >&2
  exit 1
fi

echo "Copying $SRC → $DST"
rsync -a \
  --exclude '.git/' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  --exclude '.venv/' \
  --exclude 'venv/' \
  --exclude 'out/' \
  --exclude '.mypy_cache/' \
  --exclude '.ruff_cache/' \
  --exclude '.pytest_cache/' \
  --exclude 'scripts/migration/' \
  "$SRC"/ "$DST"/

mkdir -p "$DST/out"
touch "$DST/out/.gitkeep"
mkdir -p "$DST/scripts/migration"

echo "Copy complete."
find "$DST" -maxdepth 1 -mindepth 1 | sort
