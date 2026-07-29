# Biologis Cogitator

Reusable *Warhammer 40,000* **mesh workshop** — system + biosphere generator. Standalone fork of the former Codex-Batavi `castra-biogen` tool (Castra Vetera remains an optional example pack).

- **Interactive:** cogitator TUI — `biologis-cogitator` / `cogitator` / `init-cogitator` (or `./run wizard`)
- **Scriptable CLI:** `generate-system` / `generate` / `show` / …
- **Packs:** scenarios under `data/packs/` (Castra Vetera is an **optional example**, not the core)

Hardlocks / pack pins can be **overridden** in the wizard (warnings recorded). **Sealed** Magos + literary + `state.json` land under your configured **results** directory (default suggestion `~/BiologisCogitator/results`; until setup runs, the repo `cogitator-results/` path is used). Scratch/working copies use the configured **out** dir. Greenfield demo **templates** live under `templates/greenfield/`. `propose-export` is dry-run only (explicit apply is end-state, not yet).

**Term lexicon:** [`REFERENCE.md`](REFERENCE.md) — layers, enums, origins, biomes, provenance, paths.

**Now:** Archive reads sealed packs under the configured results dir. No dependency on a Codex-Batavi checkout.

## Install (Linux)

```bash
cd /path/to/biologis-cogitator
./install.sh
```

The installer **checks dependencies first** (`python3`, `pip`, PyYAML, textual, tkinter), then:

1. Links `biologis-cogitator` / `cogitator` / `init-cogitator` into `~/.local/bin`
2. Installs **bash** and **zsh** tab completion
3. Installs a **desktop entry** that opens the **GTK app window** (embedded terminal + background art)
4. Opens a **setup window** to pick Results + Scratch folders (Tk folder picker; needs `python3-tkinter`)

Graphical window needs system packages: `python3-gobject` + `vte291` (Fedora usually has these).  
Force plain terminal: `BIOLOGIS_NO_WINDOW=1 biologis-cogitator`

Flags: `--yes` (auto pip install), `--skip-setup` (PATH/desktop only).

Reconfigure folders anytime: `biologis-cogitator setup`  
Config file: `~/.config/biologis-cogitator/config.yaml`

Fedora tip if the GUI folder picker is missing:

```bash
sudo dnf install python3-tkinter
```

After install, open a new shell (or `source ~/.bashrc`) so **Tab** completes subcommands.

## Quick start

```bash
cd /path/to/biologis-cogitator
./install.sh
# then from any terminal or the app menu:
biologis-cogitator          # also: cogitator / init-cogitator
cogitator --pack castra-vetera --seed 42

# Local entry (no global install) — still uses XDG config if present
./run wizard
./run wizard --pack castra-vetera --seed 42

# CLI greenfield
./run generate-system demo-system --seed 42 --spark

# CLI with Castra Vetera pack
./run packs
./run generate-system system-ii-crucible --existing --pack castra-vetera
./run generate aethelgard-prime --existing-system system-ii-crucible --pack castra-vetera
./run propose-export aethelgard-prime
```

On Windows use `run.cmd` (forces WSL). Linux is the supported desktop release for now.

## Output layout

| Path | Role |
|------|------|
| Configured **results** dir (or repo `cogitator-results/`) | **Sealed finals** — Archive + L7 seal target |
| Configured **out** dir (or repo `out/`) | Scratch / working only |
| `templates/greenfield/` | Demo / greenfield template stubs (not mesh finals) |
| `data/packs/` | Scenario locks (e.g. `castra-vetera`) |

## Wizard

Green-phosphor full-screen TUI hosted in a **custom GTK window** (embedded VTE + Mechanicus background). Boot splash is a GIF built from your Aquila + Mechanicus stills (`python3 scripts/bake_boot_from_logos.py`). Skip: `--no-splash`. Classic terminal: `BIOLOGIS_NO_WINDOW=1 biologis-cogitator`.

1. **Boot** — **Rite of Registration** | **Rite of Amendment** | **Rite of Consultation** (`q` / header **Terminate** quits)  
   - **Registration** — Register stellar system · Register biosphere upon known system · **Invoke template litany** (packs as templates)  
   - **Amendment** — open a body (pack / sealed) to amend; biomes & species are registered here  
   - **Consultation** — sealed archive only (read-only)  
2. **System (L-1)** — mode; star **Roll / Pick / Skip** (overrides warn) — skipped on biosphere registration  
3. **Body** — init from slug/pack; pick planet type & immaterium; reroll  
4. **Biomes (L4)** — add/remove class+richness; **Roll / Skip**; trophic rebuilds from the list  
5. **Review** — **Seal to results**, **Open in Archive**, Save as pack, propose-export; **Return to menu** (does not exit)

**Amendment:** load from pack or sealed results → edit… → **Save pack** + **Seal results**.

**Chrome (every screen):** **Menu** (main menu) · **Reload** (schema + last body from disk) · **Terminate** (exit). Unsaved changes prompt Save / Don’t save / Cancel — also on **Back** / Return to menu.

**Species profile:** Specimens screen is **read-only**. **New** → pick primary biome → profile with auto Entry ID (`AAAA-BBB-NNN`); **Edit** opens the selected specimen; **Add subspecies** clones answers into `…-AA` / `…-AB` (disk write only on Save). Schema: `templates/species-generation-profile.yaml`.

**Consultation (archive):** bodies and systems under sealed results — view `magos.md` / `literary.md` / `state.json` / `species/...` (systems: `system.json` / `system.md`). Read-only; does not load into the active rite yet.

Biosphere registration: pick a system from sealed `systems/` or a pack, then continue at body → biomes → review.

## Packs

```text
data/packs/<id>/
  pack.yaml
  systems/*.yaml
  bodies/*.yaml
```

| Pack | Role |
|------|------|
| `castra-vetera` | Optional Nine Phalanx / mesh example |
| *(your export)* | Created via wizard **Save as pack** |

Core enums/matrices stay generic under `data/enums/` and `data/matrices/`.

## Pipeline

| Layer | Role |
|-------|------|
| **L-1** | Star, orbit bands, formations, body slots |
| **L0** | Pack/YAML pins |
| **L1–L6** | Planet type → geology → climate (+ immaterium grade) → biomes → trophic → bauplan |
| **L7** | Magos + literary Markdown + `state.json` |

Species are **biome-born**: `biome → trophic slot → bauplan`.

## CLI

```text
./run wizard [--seed N] [--pack NAME]
./run packs
./run generate-system <slug> [--seed N] [--spark] [--mode natural|engineered_mesh] [--existing] [--pack NAME]
./run generate <body> [--seed N] [--spark] [--from-lock path] [--system slug] [--existing-system slug] [--pack NAME]
./run show <slug> [--json] [--as-system]
./run propose-export <body>
./run layers
```
