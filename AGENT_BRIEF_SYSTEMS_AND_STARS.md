# Agent brief — System layer (L-1): stars, modes, and soft rules

**Audience:** another coding/worldbuilding agent working on **Biologis Cogitator** (`/home/paulom/biologis-cogitator`) or the legacy Codex copy under `tools/castra-biogen/`.

**Scope:** how **systems** and **stars** work in this tool. Not body biomes, species Entry IDs, or Codex canon geography (except that the `castra-vetera` pack is an optional engineered-mesh example).

**SoT files:**
- `data/enums/star_classes.yaml` — spectral letters, size bands, soft orbit hints
- `lib/layers/stellar.py` — roll / pin / engineered behavior
- `REFERENCE.md` — human glossary (this brief is the chat-portable cut)

---

## 1. What a “system” is here

A **system** is the L-1 stellar container before biospheres:

- **mode** (`natural` | `engineered_mesh`)
- **star** (`spectral` × `size_band` → label like `G-dwarf`)
- **orbit bands** (soft zones: inner / habitable / outer / ice)
- **companions** (binary/etc.; often `none`)
- **formations** (belts, debris, rings, …)
- **body_slots** (named places where worlds/stations will attach)

Bodies (planets/moons/…) are **not** fully rolled at L-1; they get slots, then L1–L6 run per body.

Wizard: **Roll / Pick / Skip** star. Overrides of locked stars emit **warnings**, not hard fails.

---

## 2. System mode (critical rule)

| Mode | Meaning | Body inventory |
|------|---------|----------------|
| **`natural`** | Soft “astrophysics fiction” | Orbit bands **suggest** typical body kinds/counts; rolls allowed |
| **`engineered_mesh`** | Atlas / mesh construct (Castra Vetera style) | Bodies come from **locks**, not realistic planet rolls. Star may be symbolic/pinned (default often G-dwarf if unset) |

**Rule of thumb:** CV Nine Phalanx packs → `engineered_mesh`. Greenfield sandbox → usually `natural`.

---

## 3. Star = spectral letter × size band

Label form: **`{spectral}-{size_band}`** (example: `G-dwarf` ≈ Sun-like main sequence).

This is a **coarse fiction table**, not a Hertzsprung–Russell diagram.

### 3.1 Spectral letters — are they words?

**No.** They are **not acronyms**. They are Harvard spectral-class **labels** from an old line-strength catalog, later sorted by temperature.

Full classic ladder (hot → cool): **O B A F G K M**  
Mnemonic only: *“Oh Be A Fine Girl/Guy, Kiss Me”* — the words are memory aids, **not** expansions of the letters.

The cogitator only exposes the cooler useful set: **M K G F** (listed cool → warm in the enum file).

| Letter | Color (rough) | Temperature vs Sun | Picture |
|--------|---------------|--------------------|---------|
| **M** | Red / deep orange | Coolest | Red dwarfs; dim; habitable belt close in |
| **K** | Orange | Cooler than Sol | “Orange sun” |
| **G** | Yellow-white | Sun class | **Sol is a G** (G2) |
| **F** | White / yellow-white | Hotter than Sol | Brighter; more heat/UV at same distance |

Enum order in YAML: `M`, `K`, `G`, `F` = cool → warmer.

### 3.2 Size bands

| Band | Meaning in-tool |
|------|-----------------|
| **`dwarf`** | Main-sequence “normal” star (Sun = G-dwarf) |
| **`subgiant`** | Leaving main sequence — brighter, aging |
| **`giant`** | Expanded / luminous — strong insolation; harsh for close worlds |

Spectral = *how hot is the light?*  
Size band = *how big/evolved/bright is the star?*

Examples:
- `G-dwarf` — Sun-like
- `M-dwarf` — cool small main-sequence
- `K-giant` — cool spectrum but giant luminosity

---

## 4. Soft rules (warnings, not rejects)

### Orbit bands

| Band | Soft typical body kinds (suggestions) |
|------|----------------------------------------|
| **inner** | rocky, greenhouse, belt |
| **habitable** | rocky, ocean, greenhouse |
| **outer** | gas_giant, ice, rocky, belt |
| **ice** | ice, belt, captured_giant |

Violating a suggestion → append to `warnings[]`. **Do not hard-block** generation.

### Formations (examples)

asteroid belt, steel belt, debris field, ring system, captured giant, ice sentinel cloud, accretion disk.

### Provenance / locks

- Locked star / bodies / mode **win** over rolls.
- User override of a lock → warning + provenance `overridden` where applicable.
- `spark` can empty or thin rolls; engineered_mesh + spark + no locked bodies → warn, empty slots.

---

## 5. Agent do / don’t

**Do**
- Treat letters as spectral **classes**, not English words.
- Use `engineered_mesh` when the inventory is an authored mesh (CV pack).
- Keep star label as `{spectral}-{size_band}`.
- Prefer soft warnings over rejecting invalid orbit/body combos.

**Don’t**
- Invent O/B/A classes unless the enum is extended on purpose.
- Treat star pick as full N-body physics.
- Confuse **system** L-1 with **body** planet_type / biomes (those are later layers).
- Assume `castra-vetera` is required — it is an optional pack.

---

## 6. One-paragraph paste (minimal)

> Biologis Cogitator systems (L-1) have a mode (`natural` soft rolls vs `engineered_mesh` lock-driven mesh), a star labeled `{spectral}-{size_band}`, soft orbit bands, and body slots. Spectral letters M/K/G/F are Harvard temperature classes (not acronyms; G ≈ Sun); size bands are dwarf/subgiant/giant. Orbit hints are soft: mismatches warn, they do not hard-fail. Castra Vetera uses engineered_mesh; star physics is fiction-grade, not HR-diagram accuracy.

---

*For fuller layer glossary see `REFERENCE.md`. For repo migration / setup work see `AGENT_HANDOVER.md`.*
