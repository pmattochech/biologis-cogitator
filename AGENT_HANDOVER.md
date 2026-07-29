# Agent handover — Biologis Cogitator

**Read this first** when opening `/home/paulom/biologis-cogitator` as a new Cursor workspace.

This repo is a **standalone copy** of the mesh workshop formerly living at `Codex-Batavi/tools/castra-biogen/`. The Codex tree was **not** deleted or rewritten for this cut; work continues here.

---

## 1. Identity & naming

| | |
|--|--|
| **Product / CLI** | Biologis Cogitator (`biologis-cogitator`, aliases `cogitator` / `init-cogitator`) |
| **Repo path** | `/home/paulom/biologis-cogitator` |
| **Intended GitHub** | `git@github.com:pmattochech/biologis-cogitator.git` (remote set; **push pending** — `gh` not logged in when created) |
| **Old name** | `castra-biogen` (keep that name **only** as historical reference to the Codex tool path / Castra Vetera lore pack — do **not** rename the product back) |
| **Example pack** | `data/packs/castra-vetera/` — optional scenario data, **not** the engine core |
| **Sealed test data** | `cogitator-results/` — full CV mesh seals copied so the pack is a working regression fixture |

---

## 2. Origin & method

- **Source:** `/home/paulom/Codex-Batavi/tools/castra-biogen/` on branch `cursor/castra-biogen-wizard` (last biogen feature tip around `acb23a9` + local checkpoint noise on that branch).
- **Method:** **clean copy** (not `git filter-repo`). History in this repo starts at import commit `c75edf0`.
- **Codex:** leave intact until an explicit later retirement PR. Do not assume this agent session still has Codex as cwd.

### Migration scripts (this repo)

```text
scripts/migration/01_copy.sh          # rsync from Codex tools/castra-biogen → here
scripts/migration/02_scrape_links.py  # scrub Codex path strings (skips scripts/migration/)
```

Re-run only if re-copying from Codex; scrape **must not** rewrite `scripts/migration/` (it once self-corrupted when that exclusion was missing).

---

## 3. Absolute migration objectives (locked)

1. **Decouple absolutely** from Codex-Batavi — no runtime checkout, no imports, no required `codex-batavi/` tree.
2. **Keep `cogitator-results/`** so `castra-vetera` remains a known-good test pack.
3. **Product changes still ahead:**
   - ~~**Setup phase:**~~ Linux `./install.sh` + XDG config + Tk/CLI folder setup (`biologis-cogitator setup`).
   - **Refactor the main / boot screen** (hub UX).
4. Future Codex retirement is a **separate** Codex PR (delete or stub `tools/castra-biogen/`) — not done yet.

---

## 4. What already works (verified)

From this tree, smoke checks passed:

- `./run packs` → `castra-vetera`
- Boot UI lists the pack
- Biosphere-only lists 3 systems (results + pack)
- Load `system-ii-crucible` → body list with 9 slots
- Load `aethelgard-prime` from results → 4 biomes
- `./run wizard` boots to “AWAITING RITE SELECTION”

```bash
cd /home/paulom/biologis-cogitator
python3 -m pip install -r requirements.txt   # PyYAML, textual
chmod +x run bin/cli.py bin/biologis-cogitator
./run wizard --seed 42 --pack castra-vetera
# or: ./install-cli.sh  → biologis-cogitator on PATH
```

**Deps:** `requirements.txt` — `PyYAML>=6.0`, `textual>=0.47.0`.

**ROOT model:** `lib/util.py` — `ROOT = Path(__file__).resolve().parent.parent` (this repo root). No climb to Codex. `RESULTS` / `OUT` come from `~/.config/biologis-cogitator/config.yaml` after setup (`lib/config.py` + `apply_config()`).

**Linux install:** `./install.sh` — deps check first, then `~/.local/bin` links, bash/zsh completion under `~/.local/share/…`, desktop entry with `Terminal=true`, then setup GUI.

---

## 5. Decoupling status (link scrub)

### Done in this import

| Old | New / status |
|-----|----------------|
| `codex-batavi/biological-encyclopedia-bestiary/...` | `external/lore/bestiary/...` (string only) |
| `codex-batavi/atlas-and-topography/cultures/...` | `external/lore/cultures/...` |
| Absolute `/home/paulom/Codex-Batavi/tools/castra-biogen/...` | Relative / dropped in seals & packs |
| `propose_codex` / Propose-codex | `propose_export` / Propose-export (`lib/propose_export.py`) |
| README north star “write back to codex” | Softened — no Codex dependency |

`rg 'codex-batavi|/home/paulom/Codex-Batavi|propose_codex'` over the tree (excluding `.git` / `scripts/migration`) should be **clean**.

### Soft leftovers (intentional)

- Pack `sources:` / `dossier:` may still **name** `external/lore/...` files that **do not exist** in this repo — provenance / reminders only; the engine does **not** open them.
- Batav Wolf `dossier:` on Aethelgard is such a string.
- `propose-export` still prints suggested external paths (dry-run).

### Hard blockers for standalone

**None** for core generate / wizard / pack load / seal.

---

## 6. Layout (repo root)

```text
biologis-cogitator/
├── README.md, REFERENCE.md, requirements.txt, .gitignore
├── run, run.cmd, install-cli.sh
├── bin/cli.py, bin/biologis-cogitator
├── lib/          # engine + Textual TUI
├── data/
│   ├── enums/          # SoT tables + filing_ids.csv
│   ├── matrices/
│   └── packs/castra-vetera/
├── templates/
├── cogitator-results/  # sealed fixtures (tracked)
├── out/                # scratch (gitignored)
└── scripts/migration/
```

No `docs/` folder — docs are README + REFERENCE.

---

## 7. Recent feature context (inherited from Codex biogen work)

Useful if continuing UX/engine work (already in the copied code):

- **Filing IDs:** `data/enums/filing_ids.csv` — body `AAAA`, biome `AAAA-BBB`, species `AAAA-BBB-NNN`; API in `lib/entry_id.py`.
- **Species:** Entry ID filing; Specimens screen read-only + New/Edit; profiles as `profile.yaml` (legacy questionnaire loadable).
- **Biosphere load:** body list fills from system slots / sealed bodies / pack even when `pack_id` is unset (`lib/tui/screens/body_flow.py`).
- **List visibility:** theme — `ListItem > Label` must keep `margin: 0` or list text clips (`lib/tui/theme.py`).
- **Biome instance ids:** `{body_prefix}_{class}`, not `{class}_{list_index}` (`lib/layers/biomes.py` `unique_biome_instance_id`).
- **Classes:** `oceanic_pelagic` / `oceanic_abyssal` (renamed from `pelagic` / `abyssal`).
- **Save to existing pack:** Review + Edit hub pack Select (`lib/tui/screens/review.py`, `edit_hub.py`); `export_pack` upserts without wiping sibling bodies.

---

## 8. Git status (as of handover)

- **Branch:** `master`
- **Commit:** `c75edf0` — *Initial import: biologis-cogitator (copy from Codex castra-biogen).*
- **Remote:** `origin` → `git@github.com:pmattochech/biologis-cogitator.git`
- **Push:** blocked until GitHub repo exists + auth. Suggested:

```bash
gh auth login --hostname github.com --git-protocol ssh --web
cd /home/paulom/biologis-cogitator
gh repo create biologis-cogitator --public --source=. --remote=origin --push
# if remote already set:
# gh repo create biologis-cogitator --public --push
# or create empty repo on GitHub then: git push -u origin master
```

SSH to GitHub as `pmattochech` already works for **existing** repos; create-repo needs `gh` login or manual empty repo.

---

## 9. Suggested next work for the new agent

Priority order matching locked objectives:

1. ~~Confirm push~~ — done (`origin/master` in sync).
2. ~~Setup phase / Linux install~~ — `./install.sh` (deps check, PATH, completion, `.desktop`), XDG config + Tk folder picker (`biologis-cogitator setup`).
3. **Refactor boot / main screen** — clearer hub; keep greenfield / biosphere / pack / edit / archive entry points.
4. **Optional hygiene** — drop or stub dead `external/lore` dossier strings; decide whether sealed results stay fully git-tracked long-term.
5. **Do not** delete Codex `tools/castra-biogen` from this repo’s agent session unless the user explicitly opens Codex and orders retirement.

---

## 10. Codex-Batavi note (for humans)

- Working biogen copy still at `Codex-Batavi/tools/castra-biogen` on `cursor/castra-biogen-wizard`.
- A mistaken local branch named `castra-biogen-wizard` (without `cursor/`) previously looked “empty”; the real app is on **`cursor/castra-biogen-wizard`**.
- Codex `.cursorrules` / canon write rules apply **only** inside Codex-Batavi — this repo is a separate product tree.

---

## 11. Quick commands cheat sheet

```bash
./install.sh                           # Linux: deps, PATH, completion, desktop, setup
./run wizard [--seed N] [--pack castra-vetera]
./run setup                            # re-pick results/out folders
./run packs
./run generate-system <slug> ...
./run generate <body-slug> ...
./run show <slug>
./run propose-export <body-slug>    # dry-run external paths
```

---

*Handover updated after Linux install/setup landed. Prefer updating this file when the boot-hub refactor lands.*
