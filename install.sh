#!/usr/bin/env bash
# Install Biologis Cogitator on Linux: deps check, PATH, tab completion, desktop entry, setup.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAUNCHER="$ROOT/bin/biologis-cogitator"
BIN="${XDG_BIN_HOME:-$HOME/.local/bin}"
YES=0
SKIP_SETUP=0

for arg in "$@"; do
  case "$arg" in
    -y|--yes) YES=1 ;;
    --skip-setup) SKIP_SETUP=1 ;;
    -h|--help)
      cat <<EOF
Usage: ./install.sh [--yes] [--skip-setup]

  --yes          Auto-install missing pip packages without prompting
  --skip-setup   Do not open the folder-picker setup at the end
EOF
      exit 0
      ;;
  esac
done

echo "==> Biologis Cogitator installer (Linux)"
echo

# ---------------------------------------------------------------------------
# 0. Dependencies check (always first)
# ---------------------------------------------------------------------------
check_deps() {
  local failed=0
  local missing_pip=()
  local warn_tk=0

  echo "==> Checking dependencies…"

  if ! command -v python3 >/dev/null 2>&1; then
    echo "  FAIL  python3 not found on PATH"
    echo "        Install: sudo dnf install python3"
    failed=1
  else
    echo "  OK    python3 ($(python3 --version 2>&1))"
  fi

  if ! python3 -m pip --version >/dev/null 2>&1; then
    echo "  FAIL  python3 -m pip not available"
    echo "        Install: sudo dnf install python3-pip"
    failed=1
  else
    echo "  OK    pip ($(python3 -m pip --version 2>&1 | awk '{print $1,$2}'))"
  fi

  if [[ "$failed" -ne 0 ]]; then
    echo
    echo "Fix the system packages above, then re-run ./install.sh"
    exit 1
  fi

  if ! python3 -c "import yaml" >/dev/null 2>&1; then
    echo "  MISS  PyYAML"
    missing_pip+=(PyYAML)
  else
    echo "  OK    PyYAML"
  fi

  if ! python3 -c "import textual" >/dev/null 2>&1; then
    echo "  MISS  textual"
    missing_pip+=(textual)
  else
    echo "  OK    textual"
  fi

  if ! python3 -c "import tkinter" >/dev/null 2>&1; then
    echo "  WARN  tkinter missing (GUI folder picker needs it)"
    echo "        Install: sudo dnf install python3-tkinter"
    echo "        Setup will fall back to terminal prompts until then."
    warn_tk=1
  else
    echo "  OK    tkinter"
  fi

  if [[ ${#missing_pip[@]} -gt 0 ]]; then
    echo
    echo "Missing Python packages: ${missing_pip[*]}"
    if [[ "$YES" -eq 1 ]]; then
      echo "Installing from requirements.txt…"
      python3 -m pip install -r "$ROOT/requirements.txt"
    else
      read -r -p "Install now with: python3 -m pip install -r requirements.txt ? [Y/n] " ans
      ans=${ans:-Y}
      if [[ "$ans" =~ ^[Yy]$ ]]; then
        python3 -m pip install -r "$ROOT/requirements.txt"
      else
        echo "Aborted. Install deps and re-run ./install.sh"
        exit 1
      fi
    fi
    # Re-check
    if ! python3 -c "import yaml, textual" >/dev/null 2>&1; then
      echo "FAIL: PyYAML/textual still missing after pip install"
      exit 1
    fi
    echo "  OK    PyYAML + textual (installed)"
  fi

  echo
  if [[ "$warn_tk" -eq 1 ]]; then
    echo "Dependencies OK for CLI (tkinter optional for GUI setup)."
  else
    echo "Dependencies OK."
  fi
  echo
}

check_deps

# ---------------------------------------------------------------------------
# 1. Launchers + PATH symlinks
# ---------------------------------------------------------------------------
echo "==> Installing commands into $BIN"
chmod +x "$LAUNCHER" "$ROOT/run" "$ROOT/bin/cli.py" "$ROOT/install.sh" 2>/dev/null || true
mkdir -p "$BIN"

for name in biologis-cogitator cogitator init-cogitator; do
  ln -sfn "$LAUNCHER" "$BIN/$name"
  echo "  linked $BIN/$name → $LAUNCHER"
done

if ! command -v biologis-cogitator >/dev/null 2>&1; then
  echo
  echo "Note: $BIN is not on your PATH in this shell."
  echo "Add to ~/.bashrc (or ~/.zshrc):"
  echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

# ---------------------------------------------------------------------------
# 2. Bash completion
# ---------------------------------------------------------------------------
BASH_COMP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions"
mkdir -p "$BASH_COMP_DIR"
install -m 644 "$ROOT/packaging/completions/biologis-cogitator.bash" \
  "$BASH_COMP_DIR/biologis-cogitator"
# Same function file under alias names so bash finds them
ln -sfn "$BASH_COMP_DIR/biologis-cogitator" "$BASH_COMP_DIR/cogitator"
ln -sfn "$BASH_COMP_DIR/biologis-cogitator" "$BASH_COMP_DIR/init-cogitator"
echo "==> Bash completion → $BASH_COMP_DIR/biologis-cogitator"

# ---------------------------------------------------------------------------
# 3. Zsh completion
# ---------------------------------------------------------------------------
ZSH_COMP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions"
mkdir -p "$ZSH_COMP_DIR"
install -m 644 "$ROOT/packaging/completions/_biologis-cogitator" \
  "$ZSH_COMP_DIR/_biologis-cogitator"
echo "==> Zsh completion → $ZSH_COMP_DIR/_biologis-cogitator"
echo "    If completions do not load, add to ~/.zshrc:"
echo "      fpath=(\$HOME/.local/share/zsh/site-functions \$fpath)"
echo "      autoload -Uz compinit && compinit"

# ---------------------------------------------------------------------------
# 4. Desktop entry + app icon
# ---------------------------------------------------------------------------
APP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
ICON_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor"
mkdir -p "$APP_DIR"
ICON_SRC="$ROOT/assets/app-icon.png"
if [[ -f "$ICON_SRC" ]]; then
  for sz in 32 48 64 128 256 512; do
    sized="$ROOT/assets/app-icon-${sz}.png"
    dest="$ICON_DIR/${sz}x${sz}/apps"
    mkdir -p "$dest"
    if [[ -f "$sized" ]]; then
      install -m 644 "$sized" "$dest/biologis-cogitator.png"
    else
      install -m 644 "$ICON_SRC" "$dest/biologis-cogitator.png"
    fi
  done
  if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t "$ICON_DIR" >/dev/null 2>&1 || true
  fi
  echo "==> App icon → $ICON_DIR (biologis-cogitator)"
fi
# Rewrite Exec + Icon to absolute paths so menus work even with a thin PATH
{
  sed -e "s|^Exec=.*|Exec=$BIN/biologis-cogitator|" \
      -e "s|^Icon=.*|Icon=$ROOT/assets/app-icon.png|" \
    "$ROOT/packaging/biologis-cogitator.desktop"
} >"$APP_DIR/biologis-cogitator.desktop"
chmod 644 "$APP_DIR/biologis-cogitator.desktop"
echo "==> Desktop entry → $APP_DIR/biologis-cogitator.desktop"
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$APP_DIR" >/dev/null 2>&1 || true
fi

# ---------------------------------------------------------------------------
# 5. Setup (folder picker)
# ---------------------------------------------------------------------------
if [[ "$SKIP_SETUP" -eq 1 ]]; then
  echo
  echo "Skipping setup (--skip-setup). Run later: biologis-cogitator setup"
else
  echo
  echo "==> Opening setup (choose results + scratch folders)…"
  if ! bash "$ROOT/run" setup; then
    echo "Setup was cancelled or failed. You can re-run: biologis-cogitator setup"
  fi
fi

echo
echo "Ready."
echo "  Terminal:  biologis-cogitator"
echo "  Desktop:   Biologis Cogitator (app menu; opens a terminal)"
echo "  Reconfigure folders: biologis-cogitator setup"
echo "  Reload this shell (or source completions) for tab completion."
