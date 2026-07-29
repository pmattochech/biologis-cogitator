#!/usr/bin/env bash
# One-shot public install — clone (or update) Biologis Cogitator, then run install.sh.
#
# Usage (no prior clone needed):
#   curl -fsSL https://raw.githubusercontent.com/pmattochech/biologis-cogitator/master/scripts/remote-install.sh | bash
#
# Optional env:
#   BIOLOGIS_HOME   Install directory (default: ~/.local/share/biologis-cogitator)
#   BIOLOGIS_REF    Git branch/tag (default: master)
#   BIOLOGIS_NO_SETUP=1  Passed through as install.sh --skip-setup
set -euo pipefail

REPO_HTTPS="${BIOLOGIS_REPO:-https://github.com/pmattochech/biologis-cogitator.git}"
REF="${BIOLOGIS_REF:-master}"
DEST="${BIOLOGIS_HOME:-${XDG_DATA_HOME:-$HOME/.local/share}/biologis-cogitator}"

echo "==> Biologis Cogitator — remote install"
echo "    repo: $REPO_HTTPS"
echo "    ref:  $REF"
echo "    dest: $DEST"
echo

if ! command -v git >/dev/null 2>&1; then
  echo "error: git is required (e.g. sudo dnf install git / sudo apt install git)" >&2
  exit 1
fi
if ! command -v curl >/dev/null 2>&1 && ! command -v wget >/dev/null 2>&1; then
  echo "error: curl or wget is required to fetch the installer itself" >&2
  exit 1
fi

mkdir -p "$(dirname "$DEST")"

if [[ -d "$DEST/.git" ]]; then
  echo "==> Updating existing checkout…"
  git -C "$DEST" remote set-url origin "$REPO_HTTPS" 2>/dev/null || true
  git -C "$DEST" fetch --depth 1 origin "$REF"
  git -C "$DEST" checkout -f -B "install-$REF" "FETCH_HEAD"
elif [[ -e "$DEST" ]]; then
  echo "error: $DEST exists but is not a git checkout. Move it aside or set BIOLOGIS_HOME." >&2
  exit 1
else
  echo "==> Cloning…"
  git clone --depth 1 --branch "$REF" "$REPO_HTTPS" "$DEST"
fi

INSTALL_ARGS=(--yes)
if [[ "${BIOLOGIS_NO_SETUP:-}" == "1" ]]; then
  INSTALL_ARGS+=(--skip-setup)
fi
# Forward any extra args from: bash remote-install.sh --skip-setup
for arg in "$@"; do
  case "$arg" in
    --yes|-y|--skip-setup) INSTALL_ARGS+=("$arg") ;;
  esac
done

chmod +x "$DEST/install.sh" "$DEST/run" "$DEST/bin/biologis-cogitator" 2>/dev/null || true
exec bash "$DEST/install.sh" "${INSTALL_ARGS[@]}"
