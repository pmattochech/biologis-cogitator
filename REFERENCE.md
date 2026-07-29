# Castra Biogen — term reference

Lexicon for tags, categories, and fields used by the generator, packs, Magos dossiers, and the cogitator wizard. Machine sources of truth live under `data/enums/` and `data/matrices/`; this file explains them in plain language.

**Scope:** tool vocabulary only (not Chapter doctrine / gene-line canon). Origin tags are ecological provenance, not progenitor claims.

---

## Pipeline layers

| Layer | Name | What it produces |
|-------|------|------------------|
| **L-1** | Stellar / system | Star class, orbit bands, companions, formations, body slots |
| **L0** | Hardlock ingest | Pack/YAML pins into `locks{}` (never overwritten by sparks) |
| **L1** | Planet type | Administratum `planet_type` + `body_kind` |
| **L2** | Geology | Gravity, crust, volcanism, connectivity, hydrosphere, topology |
| **L3** | Chemistry + climate | Atmosphere, water, solvent, cryosphere, climate belts, **immaterium_stress** |
| **L4** | Biomes | List of biomes (class, richness, medium, overlay flag) |
| **L5** | Trophic niches | Per-biome food web slots + Earth niche analogues + origin tags |
| **L6** | Bauplan | Body-plan traits constrained by biome medium |
| **L7** | Dual render | `magos.md` + `literary.md` + `state.json` |

**Biome-born law:** species are created as `biome → trophic slot → bauplan`. There is no single planet-wide food chain.

---

## Paths and product roles

| Path | Role |
|------|------|
| `cogitator-results/` | **Sealed finals** — Magos / literary / state (Archive + Seal target) |
| `cogitator-results/<body>/species/<Entry-ID>/` | Per-species profile + Midjourney + filing reminders |
| `data/enums/filing_ids.csv` | Universal filing registry (body `AAAA`, biome `AAAA-BBB`) |
| `out/` | Scratch / working only (gitignored) |
| `templates/greenfield/` | Demo / greenfield stub layout (not mesh finals) |
| `templates/species-generation-profile.yaml` | **Cogitator profile schema** (edit → restart / Reload schema) |
| `templates/species-generation-profile.md` | Human/chat copy of the same profile |
| `data/packs/<id>/` | Scenario locks (systems + bodies YAML) |
| `data/enums/` | Controlled vocabularies |
| `data/matrices/` | Spark / trait tables |

### Filing IDs (body / biome / species)

Prose folder slugs stay (`aethelgard-prime`, `aethelgard_shoreline`). Filing IDs are for app ops only, auto-allocated, unique via `data/enums/filing_ids.csv`.

| Level | ID | Example |
|-------|-----|---------|
| Body | `AAAA` | `AETH` |
| Biome | `AAAA-BBB` | `AETH-SHR` |
| Species | `AAAA-BBB-NNN` | `AETH-SHR-001` |
| Variant | `AAAA-BBB-NNN-AA` | `AETH-SHR-001-AA` |

CSV columns: `kind,filing_id,slug,parent_filing_id,label`. New body/biome creation registers rows automatically (no manual abbrev edit).

| Artifact | Meaning |
|----------|---------|
| `magos.md` | Structured Magos Biologis dossier |
| `literary.md` | Short ecology brief (prose seed) |
| `state.json` | Full WorldState dump |
| `system.json` / `system.md` | SystemState + optional summary |

---

## System mode (L-1)

| Value | Meaning |
|-------|---------|
| `natural` | Soft astrophysical suggestions; orbit bands propose typical body kinds/counts |
| `engineered_mesh` | Atlas-style mesh; body inventory comes from locks, not “realistic” planet rolls |

**Orbit bands (soft):** `inner` \| `habitable` \| `outer` \| `ice` — suggestions only; violations emit `warnings[]`, not hard rejects.

**Formations (examples):** asteroid belt, steel belt, debris field, ring system, captured giant, ice sentinel cloud, accretion disk.

---

## Star class (L-1)

Coarse fiction table — not HR-diagram physics.

| Field | Values | Meaning |
|-------|--------|---------|
| **spectral** | `M` `K` `G` `F` | Cool → warmer main-sequence letters |
| **size_band** | `dwarf` `subgiant` `giant` | Luminosity / size band for HZ / insolation hints |

Label form: `{spectral}-{size_band}` (e.g. `G-dwarf`).

---

## Body kind vs planet type (L1)

**`body_kind`** — what the object *is* physically:

| Value | Meaning |
|-------|---------|
| `planet` | Primary world |
| `moon` | Satellite of a larger body |
| `gas_giant` | Gas giant (may have moons filed separately) |
| `asteroid` | Individual rock |
| `belt_object` | Named belt constituent |
| `station` | Hab / dock / void platform |
| `engineered_construct` | Artificial mesh construct |

**`planet_type`** — classic Imperial Administratum class (habitation / threat filing). CV flavor words (`ecumenopolis`, Needles, etc.) go in **notes / biomes**, not here.

| Value | Typical Magos reading |
|-------|----------------------|
| `agri_world` | Tithe monoculture / food production |
| `cardinal_world` | Ecclesiarchy seat-world |
| `cemetery_world` | Burial / ossuary world |
| `civilised_world` | Mixed Imperial settlement |
| `dead_world` | No (or null) biosphere under filing |
| `death_world` | Hostile ecology; high mortal attrition |
| `desert_world` | Arid dominant |
| `feudal_world` | Low-tech stratified society |
| `feral_world` | Pre- or post-Imperial savage ecology |
| `forge_world` | Adeptus Mechanicus industry |
| `fortress_world` | Bastion / military primacy |
| `frontier_world` | Edge settlement |
| `garden_world` | Cultivated park / controlled life |
| `hive_world` | Vertical city stacks |
| `ice_world` | Cryosphere-dominant |
| `industrial_world` | Industry without full forge classification |
| `jungle_world` | Dense tropical / jungle belts |
| `knight_world` | Knight household world |
| `mining_world` | Extractive primacy |
| `ocean_world` | Hydrosphere-dominant |
| `paradise_world` | Luxury / recreational filing |
| `penal_world` | Penal / labour filing |
| `quarantine_world` | Sealed / forbidden contact |
| `shrine_world` | Pilgrimage / faith primacy |
| `war_world` | Continuous warfare filing |

---

## Immaterium stress (L3)

Veil / Warp pressure on the **body** (ecology hazard — not calendar physics).

| Grade | Magos reading |
|-------|----------------|
| `neutral` | Stable realspace veil; no Warp-driven climate/mutation pressure |
| `minoris` | Thin omens, rare anomalies; ecology mostly physico-chemical |
| `majoris` | Recurring veil weather; mutation/psychic pressure shapes niches |
| `extremis` | Storm-shadow / rift-margin normal; many biomes warp-conditioned |
| `terminus` | Survival ecology only under extreme veil load; most natural gardens impossible |

**Default:** `neutral`. Locks win. Never auto-`terminus` without lock/spark. Optional free-text **flavor tags** (e.g. `storm_shadow`, `rift_adjacent`) do not replace the grade.

---

## Biomes (L4)

Each biome record has:

| Field | Meaning |
|-------|---------|
| `id` | Local slug (e.g. `aethelgard_shoreline`) |
| `class` | Generic class id from the catalogue below |
| `richness` | How full the trophic ladder is (see below) |
| `medium` | Physical medium for bauplan inheritance |
| `overlay` | `true` = Imperial occupation ecology; `false` = natural/wild |

### Medium

| Value | Meaning |
|-------|---------|
| `terrestrial` | Land surface |
| `freshwater` | Rivers, wetlands, lakes |
| `marine` | Seas / ocean |
| `aerial` | Open air column |
| `subterranean` | Caves / undercrust |
| `industrial_void` | Hive / station / slag / dock ecology |

### Richness (trophic ladder gate)

| Value | Slots filled (base → top) |
|-------|---------------------------|
| `null` | None |
| `barren` | `microbiota` only |
| `sparse` | producer, decomposer |
| `moderate` | … + primary_consumer, mesopredator |
| `rich` | … + secondary_consumer, apex, scavenger |

(`parasite` exists in slot order but is not on the default rich ladder.)

### Biome classes — natural / wild

| Class id | Medium | Default richness |
|----------|--------|------------------|
| `shoreline_intertidal` | marine | rich |
| `swamp_wetland` | freshwater | rich |
| `taiga` | terrestrial | moderate |
| `montane` | terrestrial | moderate |
| `desert` | terrestrial | sparse |
| `grassland` | terrestrial | moderate |
| `jungle` | terrestrial | rich |
| `temperate_forest` | terrestrial | moderate |
| `tundra` | terrestrial | sparse |
| `oceanic_abyssal` | marine | moderate |
| `oceanic_pelagic` | marine | moderate |
| `freshwater_river` | freshwater | moderate |
| `cave_subterranean` | subterranean | sparse |
| `volcanic_thermophile` | terrestrial | sparse |
| `acid_swamp` | freshwater | moderate |
| `ice_cryogenic` | terrestrial | sparse |
| `aerial_open` | aerial | sparse |
| `barren_null` | terrestrial | null |

### Biome classes — Imperial overlay

| Class id | Medium | Default richness |
|----------|--------|------------------|
| `hive_stack` | industrial_void | moderate |
| `monoculture_plain` | terrestrial | moderate |
| `hydroponic` | freshwater | sparse |
| `slag_industrial` | industrial_void | sparse |
| `archival_garden` | terrestrial | sparse |
| `penal_infrastructure` | industrial_void | barren |
| `dock_hull` | industrial_void | sparse |
| `station_hab` | industrial_void | barren |

Overlay biomes default new trophic slots toward **exotic** origins; natural biomes default **native**.

---

## Trophic slots (L5)

| Slot | Role in the web |
|------|-----------------|
| `microbiota` | Trace / microbial base (barren worlds) |
| `producer` | Primary production (flora / phototroph analogues) |
| `decomposer` | Detritus / decay niche |
| `primary_consumer` | Grazers / browsers / low consumers |
| `secondary_consumer` | Mid predators / piscivores |
| `mesopredator` | Middle carnivore tier (moderate richness) |
| `apex` | Top predator of **this biome** (not of the whole world) |
| `scavenger` | Carrion / opportunistic cleanup |
| `parasite` | Optional parasite niche (catalogue-ready) |

**Niche analogue:** Earth-comparison label drawn from the biome-indexed matrix (`data/matrices/niche_analogues.yaml`), not a flat global predator table.

**Range:** default `single`. `range: multi` + `secondary_biomes` means the specimen’s primary web is one biome; secondary appearances are links (engine support evolving).

---

## Origin and origin_subtype (L5 / L6)

Every filled slot carries both.

### `origin: native`

Established / evolved on this body (as Magos currently files it).

| Subtype | Meaning | Example pattern |
|---------|---------|-----------------|
| `aboriginal` | Deep-time / pre-colonial biota | Uncatalogued swamp flora treated as endemic |
| `neo_endemic` | Speciated **on this body** from colonizer stock; now of the world | *Canis Batavorum* (Batav) |
| `pre_compliance` | Long-established before current Imperial filing; ancestry unclear | Folk taxa without clear import receipt |

### `origin: exotic`

Not of this world’s evolutionary story (as currently filed).

| Subtype | Meaning | Example pattern |
|---------|---------|-----------------|
| `imperial_tithe` | Tithe / agri / ration imports | Grox-line stock |
| `deliberate_transplant` | Magos / Administratum / Chapter planted | Combat cultures |
| `voidborne` | Hull / station hitchhikers | Radiation biofilms |
| `xenos_invasive` | Non-human xenos intrusion | Threat biospheres |
| `relic_import` | Rare offworld relic organisms | Named relic beasts |
| `feral_exotic` | Introduced and gone feral **without** local speciation | Hive pests still “the import” |

**Neo-endemic is native**, not exotic. Feral import without speciation stays exotic.

---

## Bauplan traits (L6)

Constrained by biome **medium**. Typical fields:

| Field | Meaning |
|-------|---------|
| `locomotion` | How it moves (e.g. cursorial, swim, cling) |
| `respiration` | Gas / solvent exchange analogue |
| `size_class` / `size_ceiling` | Typical vs maximum size band for the medium |
| `dossier` | Locked codex path — bauplan not rewritten |

Size bias by slot (defaults): microbiota → microscopic; apex → large; parasite → tiny; etc. (`data/matrices/bauplan_traits.yaml`).

---

## Wizard provenance

How a field was set in the cogitator session:

| Tag | Meaning |
|-----|---------|
| `rolled` | Dice / spark filled an unlocked field |
| `picked` | User chose an explicit value |
| `skipped` | User skipped; layer kept prior / empty policy |
| `locked` | Pack or YAML hardlock |
| `overridden` | User changed a locked value — **lock kept in warnings** |

Hardlocks win on contradiction: spark/override records `warnings[]` and does not silently erase pins.

---

## Packs and locks

| Term | Meaning |
|------|---------|
| **Pack** | Named scenario under `data/packs/<id>/` (`pack.yaml` + systems + bodies) |
| **Lock** | Curated YAML pin for a system or body |
| **Specimen** | Named fauna/flora entry in a body lock (`primary_biome`, `origin`, `origin_subtype`, optional dossier) |
| **Spark** | Optional dice against matrices where fields are unlocked (`--spark` / wizard spark) |
| **Propose-export** | Dry-run list of suggested `external/lore/` paths — **never writes** without a later explicit apply |
| **Custom enums** | Pack-local tags in `data/packs/<id>/custom_enums.yaml` — invent in Editor, **Promote** into `data/enums/` |
| **Prose override** | Optional `prose.magos` / `prose.literary` on a body lock — preferred on Seal over generated text |
| **Range link** | Specimen with `range: multi` + `secondary_biomes` appears as a link in those webs (not a second birth) |

Castra Vetera is an **optional example pack**, not the engine core.

---

## Geology / climate fields (common Magos lines)

| Field | Typical meaning |
|-------|-----------------|
| `gravity_g` | Surface gravity in g |
| `crust` | Crust character tag |
| `volcanism` | Volcanic activity band |
| `connectivity` | Land–sea continuity (`pangaea` / `semi_archipelago` / `archipelago` — migratory hint) |
| `tidal_lock` | Tidally locked to primary |
| `hydrosphere_pct` | Surface water fraction |
| `insolation_hint` | Star-driven energy hint |
| `topology` | Free-text landform summary |
| `atmosphere` | Breathability / composition tag |
| `water` / `solvent` | Liquid water present; chemistry solvent |
| `cryosphere` | Ice / cold belt character |
| `climate_belts` | Named belts (e.g. taiga, shoreline) |

---

## Related files

- Enums: [`data/enums/`](data/enums/)
- Matrices: [`data/matrices/`](data/matrices/)
- Product overview: [`README.md`](README.md)
- Pipeline contracts: `./run layers`
