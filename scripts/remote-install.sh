#!/usr/bin/env bash
# One-shot public install — clone (or update) Biologis Cogitator, then run install.sh.
#
# Usage (no prior clone needed):
#   curl -fsSL https://raw.githubusercontent.com/pmattochech/biologis-cogitator/master/scripts/remote-install.sh | bash
#
# Optional env:
#   BIOLOGIS_HOME        Install directory (default: ~/.local/share/biologis-cogitator)
#   BIOLOGIS_REF         Git branch/tag (default: master)
#   BIOLOGIS_REPO        Git remote URL
#   BIOLOGIS_NO_SETUP=1  Passed through as install.sh --skip-setup
#   BIOLOGIS_ASSUME_YES=1  Skip update confirmation + auto pip (--yes)
set -euo pipefail

REPO_HTTPS="${BIOLOGIS_REPO:-https://github.com/pmattochech/biologis-cogitator.git}"
REF="${BIOLOGIS_REF:-master}"
DEST="${BIOLOGIS_HOME:-${XDG_DATA_HOME:-$HOME/.local/share}/biologis-cogitator}"
ASSUME_YES="${BIOLOGIS_ASSUME_YES:-0}"

echo "==> Biologis Cogitator — remote install"
echo "    repo: $REPO_HTTPS"
echo "    ref:  $REF"
echo "    dest: $DEST"
echo
echo "WARNING: This installer downloads and executes code from the network,"
echo "         then may run pip install. Prefer a verified clone when you can:"
echo "           git clone $REPO_HTTPS && cd biologis-cogitator && ./install.sh"
echo "         Pin a release tag with BIOLOGIS_REF=<tag> when available."
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

IS_UPDATE=0
if [[ -d "$DEST/.git" ]]; then
  IS_UPDATE=1
  echo "==> Updating existing checkout…"
  OLD_HEAD="$(git -C "$DEST" rev-parse --short HEAD 2>/dev/null || echo unknown)"
  git -C "$DEST" remote set-url origin "$REPO_HTTPS" 2>/dev/null || true
  git -C "$DEST" fetch --depth 1 origin "$REF"
  NEW_HEAD="$(git -C "$DEST" rev-parse --short FETCH_HEAD 2>/dev/null || echo unknown)"
  echo "    current: $OLD_HEAD"
  echo "    fetch:   $NEW_HEAD ($REF)"
  if [[ "$ASSUME_YES" != "1" ]]; then
    read -r -p "Continue update and re-run installer? [y/N] " ans
    case "${ans:-}" in
      y|Y|yes|YES) ;;
      *)
        echo "Aborted."
        exit 1
        ;;
    esac
  fi
  git -C "$DEST" checkout -f -B "install-$REF" "FETCH_HEAD"
elif [[ -e "$DEST" ]]; then
  echo "error: $DEST exists but is not a git checkout. Move it aside or set BIOLOGIS_HOME." >&2
  exit 1
else
  echo "==> Cloning…"
  git clone --depth 1 --branch "$REF" "$REPO_HTTPS" "$DEST"
  NEW_HEAD="$(git -C "$DEST" rev-parse --short HEAD 2>/dev/null || echo unknown)"
  echo "    HEAD: $NEW_HEAD"
fi

INSTALL_ARGS=()
# Fresh clone: auto-yes pip is convenient (user already opted into curl|bash).
# Updates: prompt unless BIOLOGIS_ASSUME_YES=1.
if [[ "$IS_UPDATE" -eq 0 || "$ASSUME_YES" == "1" ]]; then
  INSTALL_ARGS+=(--yes)
fi
if [[ "${BIOLOGIS_NO_SETUP:-}" == "1" ]]; then
  INSTALL_ARGS+=(--skip-setup)
fi
for arg in "$@"; do
  case "$arg" in
    --yes|-y|--skip-setup) INSTALL_ARGS+=("$arg") ;;
  esac
done

chmod +x "$DEST/install.sh" "$DEST/run" "$DEST/bin/biologis-cogitator" 2>/dev/null || true
echo "==> Running install.sh ${INSTALL_ARGS[*]:-}"
exec bash "$DEST/install.sh" "${INSTALL_ARGS[@]}"
