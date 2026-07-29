# Magos Biologis Dossier — aethelgard-prime

**System:** system-ii-crucible
**Seed:** 42
**Spark:** True
**Generated:** 2026-07-28T22:59:21Z

## Classification

- **Body kind:** `moon`
- **Planet type (Administratum):** `death_world`
- **Local notes:** Cyclopean tide moon — Needles shoreline, swamps, taiga, snowy mountains.

## Geology

- Gravity: 1.0 g
- Crust: rocky
- Volcanism: moderate
- Connectivity: semi_archipelago
- Tidal lock: False
- Hydrosphere: 70%
- Insolation hint: standard (G-dwarf)
- Topology: Snowy mountains, taiga, interior swamps, shoreline Needles/cliffs and intertidal spires.

## Chemistry & climate

- Atmosphere: breathable
- Water: True
- Solvent: water
- Cryosphere: cool
- Climate belts: polar_montane, taiga, swamp, shoreline
- **Immaterium stress:** `majoris`
- Stress reading: Recurring veil weather; mutation/psychic pressure shapes niches
- Flavor tags: storm_shadow

## Biomes

- `aethelgard_shoreline` — class `shoreline_intertidal`, richness `rich`, medium `marine`, overlay=False
- `aethelgard_swamp` — class `swamp_wetland`, richness `rich`, medium `freshwater`, overlay=False
- `aethelgard_taiga` — class `taiga`, richness `moderate`, medium `terrestrial`, overlay=False
- `aethelgard_montane` — class `montane`, richness `moderate`, medium `terrestrial`, overlay=False

## Trophic webs (per biome)

### aethelgard_shoreline

- **apex** — Canis Batavorum (Batav Wolf) | Origin: `native` / `neo_endemic` | analogue: `wetland_ambush_apex`
  - Locked dossier: `external/lore/bestiary/batav-wolf-canis-batavorum.md` (bauplan not rewritten)
- **secondary_consumer** — Leviathans (young) | Origin: `native` / `aboriginal` | analogue: `tidal_piscivore`
  - Bauplan: locomotion `benthic_crawl`, respiration `gill_analogue`, size `medium` (ceiling `leviathan`)
- **producer** — intertidal_algae | Origin: `native` / `aboriginal` | analogue: `intertidal_algae`
  - Bauplan: locomotion `swim`, respiration `gill_analogue`, size `medium` (ceiling `leviathan`)
- **decomposer** — coastal_detritivore_crab | Origin: `native` / `aboriginal` | analogue: `coastal_detritivore_crab`
  - Bauplan: locomotion `swim`, respiration `gill_analogue`, size `small` (ceiling `leviathan`)
- **primary_consumer** — shorebird_analogue | Origin: `native` / `aboriginal` | analogue: `shorebird_analogue`
  - Bauplan: locomotion `benthic_crawl`, respiration `gill_analogue`, size `medium` (ceiling `leviathan`)
- **scavenger** — beach_scavenger | Origin: `native` / `aboriginal` | analogue: `beach_scavenger`
  - Bauplan: locomotion `jet`, respiration `gill_analogue`, size `medium` (ceiling `leviathan`)

### aethelgard_swamp

- **producer** — peat_reed | Origin: `native` / `aboriginal` | analogue: `peat_reed`
  - Bauplan: locomotion `swim`, respiration `gill_analogue`, size `medium` (ceiling `large`)
- **decomposer** — bog_fungus | Origin: `native` / `aboriginal` | analogue: `bog_fungus`
  - Bauplan: locomotion `swim`, respiration `gill_analogue`, size `small` (ceiling `large`)
- **primary_consumer** — wetland_browser | Origin: `native` / `aboriginal` | analogue: `wetland_browser`
  - Bauplan: locomotion `bottom_walk`, respiration `gill_analogue`, size `medium` (ceiling `large`)
- **secondary_consumer** — swamp_stalker | Origin: `native` / `aboriginal` | analogue: `swamp_stalker`
  - Bauplan: locomotion `bottom_walk`, respiration `cutaneous`, size `medium` (ceiling `large`)
- **scavenger** — carrion_wader | Origin: `native` / `aboriginal` | analogue: `carrion_wader`
  - Bauplan: locomotion `swim`, respiration `gill_analogue`, size `medium` (ceiling `large`)
- **apex** — Canis Batavorum (Batav Wolf) [range link] | Origin: `native` / `neo_endemic` | analogue: `wetland_ambush_apex`
  - Locked dossier: `external/lore/bestiary/batav-wolf-canis-batavorum.md` (bauplan not rewritten)

### aethelgard_taiga

- **producer** — conifer_analogue | Origin: `native` / `aboriginal` | analogue: `conifer_analogue`
  - Bauplan: locomotion `cursorial`, respiration `pulmonary_analogue`, size `medium` (ceiling `large`)
- **decomposer** — needle_litter_fungus | Origin: `native` / `aboriginal` | analogue: `needle_litter_fungus`
  - Bauplan: locomotion `cursorial`, respiration `pulmonary_analogue`, size `small` (ceiling `large`)
- **primary_consumer** — taiga_browser | Origin: `native` / `aboriginal` | analogue: `taiga_browser`
  - Bauplan: locomotion `cursorial`, respiration `pulmonary_analogue`, size `medium` (ceiling `large`)
- **mesopredator** — taiga_meso_carnivore | Origin: `native` / `aboriginal` | analogue: `taiga_meso_carnivore`
  - Bauplan: locomotion `fossorial`, respiration `pulmonary_analogue`, size `medium` (ceiling `large`)

### aethelgard_montane

- **producer** — alpine_herb | Origin: `native` / `aboriginal` | analogue: `alpine_herb`
  - Bauplan: locomotion `fossorial`, respiration `pulmonary_analogue`, size `medium` (ceiling `large`)
- **decomposer** — highland_detritivore | Origin: `native` / `aboriginal` | analogue: `highland_detritivore`
  - Bauplan: locomotion `cursorial`, respiration `pulmonary_analogue`, size `small` (ceiling `large`)
- **primary_consumer** — cliff_grazer | Origin: `native` / `aboriginal` | analogue: `cliff_grazer`
  - Bauplan: locomotion `fossorial`, respiration `pulmonary_analogue`, size `medium` (ceiling `large`)
- **mesopredator** — mountain_meso | Origin: `native` / `aboriginal` | analogue: `mountain_meso`
  - Bauplan: locomotion `cursorial`, respiration `pulmonary_analogue`, size `medium` (ceiling `large`)

## Named species profiles

### Tide-Ox (`AETH-SHR-001`)

- **Filing:** biome `aethelgard_shoreline`, slot `secondary_consumer`
- **Taxonomy:** phylum P1, class C-ch7
- **Bodyshape:** whale-shaped
- **Size:** 8 meters (calf/estuary stage) → 60 meter (Ash-Back ancient)
- **Dimorphism:** Males have proeminent bone protusions and plates on their first pair of pectoral flippers
- **Eyes:** 4 eyes (2 pairs)
- **Limb disposition:** two pairs of pectoral flippers, one pair of pelvic fins, one large and broad tail with a larger tip for swimming
- **Ancestral limbs / mode:** 6 / D
- **Origin:** `native`
- **Names:** formal `Leviathus Spinaculii`; vernacular `Tide-Ox`
- **Artifacts:** `species/AETH-SHR-001/profile.yaml`, `species/AETH-SHR-001/midjourney.md`

## Biological risks (locked)

- Extreme osmotic pressure at tide line
- Territorial predation (Batav Wolf)
- Chemical burn in swamp belts

## Warnings / contradictions

- (none)
