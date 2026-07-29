"""Auto-update helpers — git fetch / apply for installed checkouts."""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .util import ROOT

DEFAULT_REF = "master"
DEFAULT_POLL_SECONDS = 300
BANNER_TEXT = (
    "UPDATE AVAILABLE — a newer cogitator build was detected on the remote. "
    "Save all unsaved work, then Terminate this session and open the cogitator again "
    "to load the update."
)
CURRENT_BANNER_TEXT = (
    "COGITATOR CURRENT — this session is running the latest build from origin. "
    "Veil link synchronized."
)


@dataclass
class UpdateStatus:
    enabled: bool
    root: Path
    ref: str
    local: str | None = None
    remote: str | None = None
    available: bool = False
    applied: bool = False
    dirty: bool = False
    message: str = ""
    error: str = ""

    @property
    def short_local(self) -> str:
        return (self.local or "?")[:7]

    @property
    def short_remote(self) -> str:
        return (self.remote or "?")[:7]


def auto_update_enabled() -> bool:
    if os.environ.get("BIOLOGIS_NO_AUTOUPDATE", "").strip() in {"1", "true", "yes"}:
        return False
    if os.environ.get("BIOLOGIS_AUTOUPDATE", "1").strip() in {"0", "false", "no"}:
        return False
    return True


def update_ref() -> str:
    return (os.environ.get("BIOLOGIS_REF") or DEFAULT_REF).strip() or DEFAULT_REF


def poll_interval_seconds() -> float:
    raw = os.environ.get("BIOLOGIS_UPDATE_CHECK_SECONDS", str(DEFAULT_POLL_SECONDS))
    try:
        val = float(raw)
    except ValueError:
        return float(DEFAULT_POLL_SECONDS)
    return max(60.0, val)


def is_git_checkout(root: Path | None = None) -> bool:
    base = root or ROOT
    return (base / ".git").exists()


def _git(
    *args: str,
    cwd: Path,
    timeout: float = 90.0,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def local_head(root: Path | None = None) -> str | None:
    base = root or ROOT
    if not is_git_checkout(base):
        return None
    r = _git("rev-parse", "HEAD", cwd=base)
    if r.returncode != 0:
        return None
    return (r.stdout or "").strip() or None


def working_tree_dirty(root: Path | None = None) -> bool:
    base = root or ROOT
    if not is_git_checkout(base):
        return False
    r = _git("status", "--porcelain", cwd=base)
    if r.returncode != 0:
        return True
    return bool((r.stdout or "").strip())


def fetch_remote_head(root: Path | None = None, *, ref: str | None = None) -> str | None:
    """Fetch origin/<ref> (depth 1) and return FETCH_HEAD sha, or None on failure."""
    base = root or ROOT
    branch = ref or update_ref()
    if not is_git_checkout(base):
        return None
    # Ensure origin exists
    remotes = _git("remote", cwd=base)
    if "origin" not in (remotes.stdout or ""):
        return None
    fr = _git("fetch", "--depth", "1", "origin", branch, cwd=base, timeout=120.0)
    if fr.returncode != 0:
        # Non-shallow fetch fallback
        fr = _git("fetch", "origin", branch, cwd=base, timeout=120.0)
        if fr.returncode != 0:
            return None
    head = _git("rev-parse", "FETCH_HEAD", cwd=base)
    if head.returncode != 0:
        return None
    return (head.stdout or "").strip() or None


def check_for_update(
    root: Path | None = None,
    *,
    ref: str | None = None,
    fetch: bool = True,
) -> UpdateStatus:
    """Compare local HEAD to remote. Does not modify the working tree."""
    base = (root or ROOT).resolve()
    branch = ref or update_ref()
    status = UpdateStatus(
        enabled=auto_update_enabled(),
        root=base,
        ref=branch,
        local=local_head(base),
        dirty=working_tree_dirty(base),
    )
    if not status.enabled:
        status.message = "auto-update disabled"
        return status
    if not is_git_checkout(base):
        status.message = "not a git checkout — auto-update skipped"
        return status
    try:
        remote = fetch_remote_head(base, ref=branch) if fetch else None
        if not fetch:
            # Use origin/ref if already fetched
            r = _git("rev-parse", f"origin/{branch}", cwd=base)
            remote = (r.stdout or "").strip() or None if r.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired) as exc:
        status.error = str(exc)
        status.message = f"update check failed: {exc}"
        return status
    status.remote = remote
    if not remote:
        status.message = "could not reach origin (offline or no remote)"
        return status
    if not status.local:
        status.message = "could not read local HEAD"
        return status
    status.available = status.local != remote
    if status.available:
        status.message = (
            f"update available: {status.short_local} → {status.short_remote} ({branch})"
        )
    else:
        status.message = f"up to date ({status.short_local})"
    return status


def apply_startup_update(
    root: Path | None = None,
    *,
    ref: str | None = None,
    verbose: bool = False,
) -> UpdateStatus:
    """On process start: fetch and fast-forward / force-checkout to remote tip.

    Skips when disabled, not a git repo, or the working tree has local changes
    (so a developer checkout is not wiped). Installed clones are usually clean.
    """
    status = check_for_update(root, ref=ref, fetch=True)
    if verbose and status.message:
        print(f"[biologis-cogitator] {status.message}", flush=True)
    if not status.enabled or not status.available or not status.remote:
        return status
    if status.dirty:
        status.message = (
            f"update available ({status.short_local} → {status.short_remote}) "
            "but working tree has local changes — not applying automatically. "
            "Commit/stash or set BIOLOGIS_NO_AUTOUPDATE=1 for this checkout."
        )
        if verbose:
            print(f"[biologis-cogitator] {status.message}", flush=True)
        return status
    base = status.root
    branch = status.ref
    # Detach-proof branch for installers; matches remote-install naming.
    co = _git(
        "checkout",
        "-f",
        "-B",
        f"install-{branch}",
        "FETCH_HEAD",
        cwd=base,
    )
    if co.returncode != 0:
        status.error = (co.stderr or co.stdout or "checkout failed").strip()
        status.message = f"update apply failed: {status.error}"
        if verbose:
            print(f"[biologis-cogitator] {status.message}", flush=True)
        return status
    status.applied = True
    status.local = local_head(base) or status.remote
    status.available = False
    status.message = (
        f"updated to {status.short_local} ({branch}) — launching refreshed cogitator"
    )
    if verbose:
        print(f"[biologis-cogitator] {status.message}", flush=True)
    return status


def banner_text(status: UpdateStatus | None = None) -> str:
    if status and status.short_remote and status.short_local:
        return (
            f"UPDATE AVAILABLE ({status.short_local} → {status.short_remote}). "
            "Save all unsaved work, then Terminate and open the cogitator again "
            "to load the update."
        )
    return BANNER_TEXT


def current_banner_text(status: UpdateStatus | None = None) -> str:
    if status and status.short_local:
        return (
            f"COGITATOR CURRENT — latest {status.ref} ({status.short_local}). "
            "Veil link synchronized with origin."
        )
    return CURRENT_BANNER_TEXT
