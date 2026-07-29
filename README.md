<p align="center">
  <img src="assets/app-icon-256.png" alt="Biologis Cogitator" width="128" height="128" />
</p>

<h1 align="center">Biologis Cogitator</h1>

<p align="center">
  <strong>A Magos Biologis mesh workshop</strong><br/>
  Generate stellar systems, biospheres, biomes, and species<br/>
  for <em>Warhammer 40,000</em> — then seal them as Magos &amp; literary archives.
</p>

<p align="center">
  <a href="#install">Install</a> ·
  <a href="#what-it-is">What it is</a> ·
  <a href="#how-it-started">Origin</a> ·
  <a href="#dependencies">Dependencies</a> ·
  <a href="REFERENCE.md">Lexicon</a>
</p>

---

## Install

**Linux.** One command — no manual `git clone` required:

```bash
curl -fsSL https://raw.githubusercontent.com/pmattochech/biologis-cogitator/master/scripts/remote-install.sh | bash
```

That script will:

1. Clone the repo into `~/.local/share/biologis-cogitator` (or update it if already present)
2. Check / install Python deps
3. Put `biologis-cogitator`, `cogitator`, and `init-cogitator` on your PATH (`~/.local/bin`)
4. Install shell completions + a desktop launcher
5. Open the first-run folder picker (results + scratch)

Then launch:

```bash
biologis-cogitator
```

| Want… | Do this |
|--------|---------|
| Skip the folder picker for now | `BIOLOGIS_NO_SETUP=1 curl -fsSL … \| bash` then later `biologis-cogitator setup` |
| Install somewhere else | `BIOLOGIS_HOME=~/src/biologis-cogitator curl -fsSL … \| bash` |
| Pin a branch/tag | `BIOLOGIS_REF=master curl -fsSL … \| bash` |
| Classic terminal (no GTK window) | `BIOLOGIS_NO_WINDOW=1 biologis-cogitator` |

Already have the tree locally?

```bash
./install.sh          # interactive pip prompt
./install.sh --yes    # auto-install missing pip packages
```

> Open a **new shell** after install (or `source ~/.bashrc`) so Tab completion and `~/.local/bin` are live.

---

## What it is

Biologis Cogitator is a **standalone cogitator** — a green-phosphor TUI in a custom Mechanicus GTK window — for building and filing 40k biospheres as structured data, then rendering them as in-universe Magos reports and literary prose.

Three rites on the boot screen:

| Rite | Purpose |
|------|---------|
| **Registration** | Birth a stellar system, hang a biosphere on a known system, or invoke a pack template |
| **Amendment** | Open a body, register biomes & species, reshape the mesh |
| **Consultation** | Read sealed archives only — Magos, literary, state, species files |

Under the chassis sits a layered generator: star & orbit bands → planet type → geology → climate → biomes → trophic web → bauplan → species profiles → **Seal** into your results folder.

Species are **place-born**: every entry needs an origin (a biome on the body, or **void / warp / outer_space**). Filing IDs follow `AAAA-BBB-NNN` (and subspecies `…-AA`).

**Optional example pack:** [Castra Vetera](data/packs/castra-vetera/) — a full Nine Phalanx mesh for demos and regression. The engine does not depend on it.

Deep glossary of layers, enums, biomes, and paths: **[REFERENCE.md](REFERENCE.md)**.

---

## How it started

This project began life inside **Codex-Batavi** as `tools/castra-biogen` — a Castra Vetera–oriented biosphere generator for a larger lore mesh. It grew into a full workshop: packs, locks, trophic rolls, Magos/literary seal, and a Textual wizard.

It was then **cut free** into its own public home:

- Clean standalone tree (no runtime dependency on a Codex checkout)
- Product name **Biologis Cogitator** (`cogitator` / `init-cogitator` aliases)
- Linux installer, XDG config, GTK host window, boot splash, and a three-rite hub
- Castra Vetera kept only as an **optional pack**, not the core identity

In short: a Magos’s desk that outgrew the fortress it was forged in.

---

## Dependencies

### Required

| Dependency | Why |
|------------|-----|
| **Linux** | Supported desktop release |
| **git** | Remote install / updates |
| **python3** + **pip** | Runtime + packaging |
| **PyYAML** ≥ 6 | Packs, enums, profiles, schema |
| **textual** ≥ 0.47 | Cogitator TUI |

Python packages are pulled from [`requirements.txt`](requirements.txt) by the installer.

### Recommended (graphical app)

| Dependency | Why |
|------------|-----|
| **python3-gobject** + **vte291** (GTK3 + VTE) | Embedded terminal window + splash |
| **python3-tkinter** | First-run folder picker GUI |

Fedora examples:

```bash
sudo dnf install python3 python3-pip git python3-tkinter python3-gobject vte291
```

Debian / Ubuntu examples:

```bash
sudo apt install python3 python3-pip git python3-tk python3-gi gir1.2-gtk-3.0 gir1.2-vte-2.91
```

Without GTK/VTE the cogitator still runs in a normal terminal (`BIOLOGIS_NO_WINDOW=1` or automatic fallback).

### Optional

| Dependency | Why |
|------------|-----|
| **Pillow** | Smoother boot-GIF decode in the GTK window (pre-baked `assets/cogitator-boot.gif` still works via GdkPixbuf alone) |

```bash
python3 -m pip install Pillow
```

---

## After install

```bash
biologis-cogitator                 # window + wizard (or terminal fallback)
biologis-cogitator setup           # re-pick results & scratch folders
cogitator --pack castra-vetera --seed 42
```

Config lives at `~/.config/biologis-cogitator/config.yaml`.

| Path | Role |
|------|------|
| **Results** dir (you choose; often `~/BiologisCogitator/results`) | Sealed Magos / literary / `state.json` / species |
| **Scratch** / out dir | Working copies |
| `data/packs/` | Scenario locks (templates you can invoke or save) |

### CLI (same install)

```bash
biologis-cogitator packs
biologis-cogitator generate-system demo-system --seed 42 --spark
biologis-cogitator generate aethelgard-prime --existing-system system-ii-crucible --pack castra-vetera
biologis-cogitator show aethelgard-prime
biologis-cogitator layers
```

Local checkout without global install: `./run wizard`.

---

## Pipeline (short)

```text
L-1  Star / bands / body slots
L0   Pack pins
L1–L6  Planet → geology → climate → biomes → trophic → bauplan
L7   Magos.md + literary.md + state.json   ← Seal
```

Species schema (edit freely, then Reload schema / re-open the screen):  
[`templates/species-generation-profile.yaml`](templates/species-generation-profile.yaml)

---

## License & lore

Warhammer 40,000 is © Games Workshop. This is a **fan workshop tool** for generating structured fiction and filing aids — not a commercial product and not affiliated with Games Workshop.

---

<p align="center">
  <sub>THE FLESH IS WEAK · THE ARCHIVE ENDURES</sub>
</p>
