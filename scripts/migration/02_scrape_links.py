#!/usr/bin/env python3
"""Scrub Codex-Batavi path couplings from a biologis-cogitator tree.

Does NOT rewrite scripts/migration/ (this toolkit).
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SKIP_DIR_NAMES = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
}

TEXT_SUFFIXES = {
    ".py",
    ".md",
    ".yaml",
    ".yml",
    ".json",
    ".txt",
    ".csv",
    ".sh",
    ".cmd",
    ".toml",
    ".gitignore",
}

# Longer / more specific first. Do not include identity no-ops.
REPLACEMENTS: list[tuple[str, str]] = [
    (
        "/home/paulom/Codex-Batavi/tools/castra-biogen/",
        "",
    ),
    (
        "/home/paulom/Codex-Batavi/tools/castra-biogen",
        ".",
    ),
    (
        "codex-batavi/biological-encyclopedia-bestiary",
        "external/lore/bestiary",
    ),
    (
        "codex-batavi/atlas-and-topography/cultures",
        "external/lore/cultures",
    ),
    ("codex-batavi/", "external/lore/"),
    ("codex-batavi", "external-lore"),
    ("tools/castra-biogen", "."),
    ("castra-biogen", "biologis-cogitator"),
    ("Propose-codex", "Propose-export"),
    ("propose-codex", "propose-export"),
    ("propose_codex", "propose_export"),
    ("CODEX_BESTIARY", "EXPORT_BESTIARY"),
]


def should_skip(rel: Path) -> bool:
    if rel.parts[:2] == ("scripts", "migration"):
        return True
    return any(part in SKIP_DIR_NAMES for part in rel.parts)


def is_text(path: Path) -> bool:
    if path.name in {".gitignore", "run", "install-cli.sh", "biologis-cogitator"}:
        return True
    return path.suffix.lower() in TEXT_SUFFIXES


def scrub_text(text: str) -> tuple[str, int]:
    n = 0
    out = text
    for old, new in REPLACEMENTS:
        if old in out:
            count = out.count(old)
            out = out.replace(old, new)
            n += count
    out2 = re.sub(r"(?<!:)/{2,}", "/", out)
    if out2 != out:
        n += 1
        out = out2
    return out, n


def scrub_file(path: Path) -> int:
    raw = path.read_text(encoding="utf-8")
    new, n = scrub_text(raw)
    if not n:
        return 0
    if path.suffix.lower() == ".json":
        try:
            data = json.loads(new)
            path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            return n
        except json.JSONDecodeError:
            pass
    path.write_text(new, encoding="utf-8")
    return n


def rename_propose_module(root: Path) -> None:
    src = root / "lib" / "propose_codex.py"
    dst = root / "lib" / "propose_export.py"
    if src.is_file():
        text, _ = scrub_text(src.read_text(encoding="utf-8"))
        dst.write_text(text, encoding="utf-8")
        src.unlink()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "root",
        nargs="?",
        default="/home/paulom/biologis-cogitator",
        type=Path,
    )
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    root: Path = args.root.resolve()
    if not (root / "run").is_file():
        raise SystemExit(f"not a biologis tree (missing run): {root}")

    touched = 0
    total_hits = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if should_skip(rel) or not is_text(path):
            continue
        raw = path.read_text(encoding="utf-8", errors="replace")
        _, n = scrub_text(raw)
        if not n:
            continue
        touched += 1
        total_hits += n
        print(f"{'DRY ' if args.dry_run else ''}{rel}: {n} replacement(s)")
        if not args.dry_run:
            scrub_file(path)

    if not args.dry_run:
        rename_propose_module(root)

    print(f"Done. files={touched} hits≈{total_hits} dry_run={args.dry_run}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
