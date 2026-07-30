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

### Linux

One command — no manual `git clone` required:

```bash
curl -fsSL https://raw.githubusercontent.com/pmattochech/biologis-cogitator/master/scripts/remote-install.sh | bash
```

That script will:

1. Clone the repo into `~/.local/share/biologis-cogitator` (or update it if already present)
2. Check / install Python deps
3. Put `biologis-cogitator`, `cogitator`, and `init-cogitator` on your PATH (`~/.local/bin`)
4. Install shell completions + a desktop launcher
5. Open the first-run folder picker (results + scratch)

> **Trust note:** `curl | bash` runs remote code. Prefer a **verified install** (clone, inspect, then `./install.sh`). Updates prompt before re-installing unless `BIOLOGIS_ASSUME_YES=1`. Pin a tag with `BIOLOGIS_REF=<tag>` when you publish releases.

Then launch:

```bash
biologis-cogitator
```

| Want… | Do this |
|--------|---------|
| Skip the folder picker for now | `BIOLOGIS_NO_SETUP=1 curl -fsSL … \| bash` then later `biologis-cogitator setup` |
| Install somewhere else | `BIOLOGIS_HOME=~/src/biologis-cogitator curl -fsSL … \| bash` |
| Pin a branch/tag (install or launch) | `BIOLOGIS_REF=cursor/my-branch biologis-cogitator` |
| Classic terminal (no GTK window) | `BIOLOGIS_NO_WINDOW=1 biologis-cogitator` |
| Disable auto-update | `BIOLOGIS_NO_AUTOUPDATE=1 biologis-cogitator` |
| Update check interval (seconds) | `BIOLOGIS_UPDATE_CHECK_SECONDS=30` (default 30, min 10) |

**Build channel (test before master):** auto-update tracks one origin branch/tag.

1. **Env (wins):** `BIOLOGIS_REF=<branch>` for this process only.
2. **In-app:** boot screen → **Build channel** — pick a remote branch, Apply, then **Terminate and reopen**.
3. **Config:** saved as `git_ref` in `~/.config/biologis-cogitator/config.yaml` (used when env is unset).

Priority: `BIOLOGIS_REF` → config `git_ref` → `master`.

**Auto-update:** on every launch the cogitator fetches that channel and fast-forwards a clean install checkout. While open, a **green** banner confirms you are on the latest build (then fades); if the remote moves ahead, an **amber** banner asks you to save, Terminate, and reopen. Dirty developer working trees are never force-updated.

Already have the tree locally?

```bash
./install.sh          # interactive pip prompt
./install.sh --yes    # auto-install missing pip packages
```

**Verified install** (no pipe-to-shell):

```bash
git clone https://github.com/pmattochech/biologis-cogitator.git
cd biologis-cogitator
git checkout master   # or a release tag
./install.sh
```

> Open a **new shell** after install (or `source ~/.bashrc`) so Tab completion and `~/.local/bin` are live.

### Windows

Native **Python + Textual** in Windows Terminal (recommended). The Mechanicus GTK window is Linux/WSL-only.

**PowerShell** (no manual clone):

```powershell
irm https://raw.githubusercontent.com/pmattochech/biologis-cogitator/master/scripts/remote-install.ps1 | iex
```

> Same trust note as Linux: prefer `git clone` + `.\install.ps1`. Updates prompt unless `$env:BIOLOGIS_ASSUME_YES=1`.

Then open a **new** terminal and run:

```powershell
biologis-cogitator
```

| Want… | Do this |
|--------|---------|
| Skip setup for now | `$env:BIOLOGIS_NO_SETUP=1; irm … \| iex` then `biologis-cogitator setup` |
| Install somewhere else | `$env:BIOLOGIS_HOME="$env:USERPROFILE\src\biologis-cogitator"; irm … \| iex` |
| Local checkout | `.\install.ps1` or `.\install.ps1 -Yes` |
| Full Linux/GTK via WSL | Install under WSL with the Linux one-liner, or `.\run.cmd --wsl` from a checkout |
| Disable auto-update | `$env:BIOLOGIS_NO_AUTOUPDATE=1` |
| Pin a branch/tag | `$env:BIOLOGIS_REF='cursor/my-branch'` |

Config on Windows: `%APPDATA%\biologis-cogitator\config.yaml` (includes optional `git_ref`)  
Default results: `%USERPROFILE%\BiologisCogitator\results`

Use **Windows Terminal** (not legacy `conhost`) for correct colors and keyboard handling. Auto-update / Build channel work the same as Linux (`BIOLOGIS_REF` or in-app **Build channel**).

---

## What it is

Biologis Cogitator is a **standalone cogitator** — a green-phosphor Textual TUI (on Linux, optionally hosted in a Mechanicus GTK window) — for building and filing 40k biospheres as structured data, then rendering them as in-universe Magos reports and literary prose.

Rites on the boot screen:

| Rite | Purpose |
|------|---------|
| **Registration** | Birth a stellar system, hang a biosphere on a known system, or invoke a pack template |
| **Amendment** | Open a **body dossier** (plate + sections) to register biomes & species |
| **Consultation** | Read-only sealed **dossiers** (bodies / systems with plates) |

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
- Windows installer (native Textual TUI; GTK window via WSL)
- Castra Vetera kept only as an **optional pack**, not the core identity

In short: a Magos’s desk that outgrew the fortress it was forged in.

---

## Dependencies

### Required

| Dependency | Why |
|------------|-----|
| **Python 3** + **pip** | Runtime |
| **git** | Remote install / updates |
| **PyYAML** ≥ 6 | Packs, enums, profiles, schema |
| **textual** ≥ 0.47 | Cogitator TUI |

Python packages come from [`requirements.txt`](requirements.txt).

### Linux (graphical window)

| Dependency | Why |
|------------|-----|
| **python3-gobject** + **vte291** (GTK3 + VTE) | Embedded terminal + splash |
| **python3-tkinter** | First-run folder picker |

```bash
# Fedora
sudo dnf install python3 python3-pip git python3-tkinter python3-gobject vte291

# Debian / Ubuntu
sudo apt install python3 python3-pip git python3-tk python3-gi gir1.2-gtk-3.0 gir1.2-vte-2.91
```

Without GTK/VTE the cogitator still runs in a normal terminal (`BIOLOGIS_NO_WINDOW=1` or automatic fallback).

### Windows

| Dependency | Why |
|------------|-----|
| **Python 3** from [python.org](https://www.python.org/downloads/) (PATH + tcl/tk) | Runtime + setup GUI |
| **Git for Windows** | Remote install |
| **Windows Terminal** (recommended) | Best Textual experience |

No GTK/VTE on native Windows — the TUI runs in the console. For the Mechanicus window, use **WSL** and the Linux installer.

Pillow and **textual-image** are required (profile picture resize + in-pane preview; boot-GIF decode). Both are listed in `requirements.txt` and installed with the app. Preview uses Kitty/Sixel when the terminal supports them, otherwise Unicode half-blocks (works in the Mechanicus VTE window).

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
