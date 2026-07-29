"""Auto-update helpers — git fetch / apply for installed checkouts."""
from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from . import config as app_config
from .util import ROOT

DEFAULT_REF = "master"
DEFAULT_POLL_SECONDS = 30
MIN_POLL_SECONDS = 10
# Safe subset of git ref names (branches/tags with optional /).
_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/\-]*$")
BANNER_TEXT = (
    "UPDATE AVAILABLE — a newer cogitator build was detected on the remote. "
    "Save all unsaved work, then Terminate this session and open the cogitator again "
    "to load the update."
)
CURRENT_BANNER_TEXT = (
    "COGITATOR CURRENT — this session is running the latest build from origin. "
    "Veil link synchronized."
)

RefSource = Literal["env", "config", "default"]


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


def validate_ref(ref: str) -> str:
    """Normalize and validate a branch/tag name. Raises ValueError if unsafe."""
    name = (ref or "").strip()
    if not name or name in {".", ".."} or name.startswith("-"):
        raise ValueError("empty or invalid git ref")
    if name.startswith("refs/"):
        raise ValueError("use the short branch/tag name, not refs/…")
    if ".." in name or "\\" in name or name.endswith("/"):
        raise ValueError(f"invalid git ref: {name}")
    if not _REF_RE.match(name):
        raise ValueError(f"invalid git ref: {name}")
    return name


def env_update_ref() -> str | None:
    raw = (os.environ.get("BIOLOGIS_REF") or "").strip()
    return raw or None


def ref_source() -> RefSource:
    """Where the active update ref comes from (env wins over config)."""
    if env_update_ref():
        return "env"
    if app_config.get_git_ref():
        return "config"
    return "default"


def update_ref() -> str:
    """Active origin branch/tag: BIOLOGIS_REF → config git_ref → master."""
    env = env_update_ref()
    if env:
        try:
            return validate_ref(env)
        except ValueError:
            return env.strip() or DEFAULT_REF
    cfg = app_config.get_git_ref()
    if cfg:
        try:
            return validate_ref(cfg)
        except ValueError:
            return cfg
    return DEFAULT_REF


def persist_update_ref(ref: str) -> str:
    """Save preferred channel to config.yaml. Returns normalized ref."""
    name = validate_ref(ref)
    app_config.set_git_ref(name)
    return name


def poll_interval_seconds() -> float:
    raw = os.environ.get("BIOLOGIS_UPDATE_CHECK_SECONDS", str(DEFAULT_POLL_SECONDS))
    try:
        val = float(raw)
    except ValueError:
        return float(DEFAULT_POLL_SECONDS)
    return max(float(MIN_POLL_SECONDS), val)


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


def _checkout_fetched_ref(base: Path, branch: str) -> subprocess.CompletedProcess[str]:
    """Force local install-* branch onto FETCH_HEAD (detach-proof)."""
    # Sanitize local branch name: slashes → dashes so git accepts -B name.
    local_name = "install-" + branch.replace("/", "-")
    return _git(
        "checkout",
        "-f",
        "-B",
        local_name,
        "FETCH_HEAD",
        cwd=base,
    )


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
    co = _checkout_fetched_ref(base, branch)
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


def list_remote_branches(root: Path | None = None) -> list[str]:
    """Remote branch names from origin (ls-remote). Empty on failure."""
    base = root or ROOT
    if not is_git_checkout(base):
        return []
    remotes = _git("remote", cwd=base)
    if "origin" not in (remotes.stdout or ""):
        return []
    r = _git("ls-remote", "--heads", "origin", cwd=base, timeout=120.0)
    if r.returncode != 0:
        return []
    names: list[str] = []
    for line in (r.stdout or "").splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        ref = parts[-1]
        prefix = "refs/heads/"
        if ref.startswith(prefix):
            name = ref[len(prefix) :]
            if name and name not in names:
                names.append(name)
    return sorted(names, key=lambda s: (s != DEFAULT_REF, s))


def switch_to_ref(
    ref: str,
    root: Path | None = None,
    *,
    persist: bool = True,
    apply_now: bool = True,
) -> UpdateStatus:
    """Select update channel: persist to config, optionally checkout remote tip.

    Python modules already loaded in this process stay stale — caller should
    tell the operator to Terminate and reopen after a successful apply.
    """
    base = (root or ROOT).resolve()
    branch = validate_ref(ref)
    if persist:
        persist_update_ref(branch)
    status = UpdateStatus(
        enabled=True,
        root=base,
        ref=branch,
        local=local_head(base),
        dirty=working_tree_dirty(base),
    )
    if env_update_ref() and env_update_ref() != branch:
        status.message = (
            f"saved channel {branch} in config, but BIOLOGIS_REF="
            f"{env_update_ref()!r} still overrides until you unset it"
        )
        return status
    if not apply_now:
        status.message = (
            f"channel set to {branch} — Terminate and reopen to load that build"
        )
        return status
    if not is_git_checkout(base):
        status.message = "not a git checkout — channel saved for next install/update"
        return status
    if status.dirty:
        status.message = (
            f"channel set to {branch}, but working tree is dirty — "
            "not checking out. Commit/stash, or reopen after a clean install tree."
        )
        return status
    remote = fetch_remote_head(base, ref=branch)
    status.remote = remote
    if not remote:
        status.message = (
            f"could not fetch origin/{branch} — channel saved; "
            "check the name or network, then Terminate and reopen"
        )
        return status
    co = _checkout_fetched_ref(base, branch)
    if co.returncode != 0:
        status.error = (co.stderr or co.stdout or "checkout failed").strip()
        status.message = f"checkout failed: {status.error}"
        return status
    status.applied = True
    status.local = local_head(base) or remote
    status.available = False
    status.message = (
        f"switched to {branch} ({status.short_local}). "
        "Terminate and reopen the cogitator to load this build."
    )
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
