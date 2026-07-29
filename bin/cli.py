#!/usr/bin/env python3
"""CLI for biologis-cogitator."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lib import packs, pipeline, propose_export, state  # noqa: E402
from lib.util import apply_config, set_active_pack  # noqa: E402

apply_config()


def cmd_layers(_: argparse.Namespace) -> int:
    print("biologis-cogitator pipeline layers\n")
    for lid, name, desc in pipeline.LAYER_CONTRACTS:
        print(f"  {lid:4}  {name:28}  {desc}")
    print()
    return 0


def cmd_packs(_: argparse.Namespace) -> int:
    rows = packs.list_packs()
    if not rows:
        print("(no packs under data/packs/)")
        return 0
    for meta in rows:
        print(f"  {meta.get('id'):20}  {meta.get('title') or ''}")
    return 0


def cmd_generate_system(args: argparse.Namespace) -> int:
    if args.pack:
        set_active_pack(args.pack)
    system = pipeline.generate_system(
        args.slug,
        seed=args.seed,
        spark=args.spark,
        mode=args.mode,
        existing=args.existing,
        pack=args.pack,
    )
    print(f"Wrote system pack: cogitator-results/systems/{args.slug}/")
    print(f"  star: {system['layers'].get('star')}")
    print(f"  body_slots: {len(system['layers'].get('body_slots') or [])}")
    if system.get("warnings"):
        print("  warnings:")
        for w in system["warnings"]:
            print(f"    - {w}")
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    from_lock = Path(args.from_lock) if args.from_lock else None
    if args.pack:
        set_active_pack(args.pack)
    try:
        world = pipeline.generate_body(
            args.slug,
            seed=args.seed,
            spark=args.spark,
            from_lock=from_lock,
            system_slug=args.system,
            existing_system=args.existing_system,
            pack=args.pack,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote body pack: cogitator-results/{args.slug}/")
    print(f"  magos: {world['render']['magos_path']}")
    print(f"  literary: {world['render']['literary_path']}")
    pt = world["layers"]["planet_type"]
    chem = world["layers"]["chemistry_climate"]
    print(f"  planet_type: {pt.get('planet_type')} ({pt.get('body_kind')})")
    print(f"  immaterium_stress: {chem.get('immaterium_stress')}")
    print(f"  biomes: {len(world['layers'].get('biomes') or [])}")
    if world.get("warnings"):
        print("  warnings:")
        for w in world["warnings"]:
            print(f"    - {w}")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    slug = args.slug
    sys_path = state.system_out_dir(slug) / "system.json"
    body_path = state.body_out_dir(slug) / "state.json"
    if args.as_system or (sys_path.is_file() and not body_path.is_file()):
        try:
            data = state.load_system(slug)
        except FileNotFoundError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return 0
    try:
        data = state.load_world(slug)
    except FileNotFoundError:
        try:
            data = state.load_system(slug)
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return 0
        except FileNotFoundError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return 0
    meta = data["meta"]
    layers = data["layers"]
    print(f"Body: {meta['slug']}  system={meta.get('system_slug')}")
    print(f"  planet_type: {layers['planet_type']}")
    print(f"  geology.gravity_g: {layers['geology'].get('gravity_g')}")
    print(f"  immaterium_stress: {layers['chemistry_climate'].get('immaterium_stress')}")
    print(f"  biomes: {[b['id'] for b in layers.get('biomes') or []]}")
    print(f"  warnings: {len(data.get('warnings') or [])}")
    return 0


def cmd_propose_export(args: argparse.Namespace) -> int:
    try:
        world = state.load_world(args.slug)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(propose_export.format_report(world))
    return 0


def cmd_wizard(args: argparse.Namespace) -> int:
    from lib.tui.app import run_wizard

    run_wizard(seed=args.seed, pack=args.pack, splash=not args.no_splash)
    return 0


def cmd_setup(_: argparse.Namespace) -> int:
    from lib.setup_wizard import run_setup

    return run_setup()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="biologis-cogitator", description="40k system/biosphere generator")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("generate-system", help="L-1 stellar/system (default first step)")
    s.add_argument("slug")
    s.add_argument("--seed", type=int, default=None)
    s.add_argument("--spark", action="store_true")
    s.add_argument("--mode", choices=["natural", "engineered_mesh"], default="natural")
    s.add_argument("--existing", action="store_true", help="Pin/load from pack/system lock")
    s.add_argument("--pack", default=None, help="Scenario pack id (e.g. castra-vetera)")
    s.set_defaults(func=cmd_generate_system)

    g = sub.add_parser("generate", help="L0–L7 body biosphere (requires system)")
    g.add_argument("slug")
    g.add_argument("--seed", type=int, default=None)
    g.add_argument("--spark", action="store_true")
    g.add_argument("--from-lock", default=None)
    g.add_argument("--system", default=None)
    g.add_argument("--existing-system", default=None)
    g.add_argument("--pack", default=None, help="Scenario pack id (e.g. castra-vetera)")
    g.set_defaults(func=cmd_generate)

    sh = sub.add_parser("show", help="Show body or system pack summary")
    sh.add_argument("slug")
    sh.add_argument("--json", action="store_true")
    sh.add_argument("--as-system", action="store_true")
    sh.set_defaults(func=cmd_show)

    pc = sub.add_parser("propose-export", help="Dry-run suggested external lore paths")
    pc.add_argument("slug")
    pc.set_defaults(func=cmd_propose_export)

    ly = sub.add_parser("layers", help="List pipeline layer contracts")
    ly.set_defaults(func=cmd_layers)

    pk = sub.add_parser("packs", help="List scenario packs under data/packs/")
    pk.set_defaults(func=cmd_packs)

    w = sub.add_parser("wizard", help="Cogitator TUI guided flow")
    w.add_argument("--seed", type=int, default=None)
    w.add_argument("--pack", default=None, help="Preselect pack id")
    w.add_argument(
        "--no-splash",
        action="store_true",
        help="Skip cogitator boot animation",
    )
    w.set_defaults(func=cmd_wizard)

    su = sub.add_parser("setup", help="Choose results/out folders (first-run / reconfigure)")
    su.set_defaults(func=cmd_setup)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    apply_config()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
