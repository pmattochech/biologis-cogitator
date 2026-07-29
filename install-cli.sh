#!/usr/bin/env bash
# Install biologis-cogitator / cogitator / init-cogitator into ~/.local/bin
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAUNCHER="$ROOT/bin/biologis-cogitator"
BIN="${XDG_BIN_HOME:-$HOME/.local/bin}"

chmod +x "$LAUNCHER" "$ROOT/run" "$ROOT/bin/cli.py" 2>/dev/null || true
mkdir -p "$BIN"

for name in biologis-cogitator cogitator init-cogitator; do
  ln -sfn "$LAUNCHER" "$BIN/$name"
  echo "linked $BIN/$name → $LAUNCHER"
done

if ! command -v biologis-cogitator >/dev/null 2>&1; then
  echo
  echo "Note: $BIN is not on your PATH in this shell."
  echo "Add to ~/.bashrc if needed:"
  echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
else
  echo
  echo "Ready. From any terminal:"
  echo "  biologis-cogitator"
  echo "  cogitator"
  echo "  init-cogitator"
fi
