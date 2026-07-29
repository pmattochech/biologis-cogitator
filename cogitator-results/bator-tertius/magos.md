# Magos Biologis Dossier — bator-tertius

**System:** system-i-central-bastion
**Seed:** None
**Spark:** False
**Generated:** 2026-07-26T16:45:32Z

## Classification

- **Body kind:** `planet`
- **Planet type (Administratum):** `death_world`
- **Local notes:** Greenhouse / radiation jungle; guillotine trees; Grox-Prime. Atlas-locked; missing from Central Bastion matrix.

## Geology

- Gravity: 1.0 g
- Crust: rocky
- Volcanism: moderate
- Connectivity: isoterra
- Tidal lock: False
- Hydrosphere: 40%
- Insolation hint: standard (G-dwarf)
- Topology: Radiation jungle greenhouse world (Bator-Sol).

## Chemistry & climate

- Atmosphere: dense
- Water: True
- Solvent: water
- Cryosphere: hot
- Climate belts: radiation_jungle
- **Immaterium stress:** `majoris`
- Stress reading: Recurring veil weather; mutation/psychic pressure shapes niches
- Flavor tags: —

## Biomes

- `bator_jungle` — class `jungle`, richness `rich`, medium `terrestrial`, overlay=False
- `bator_mono` — class `monoculture_plain`, richness `moderate`, medium `terrestrial`, overlay=True

## Trophic webs (per biome)

### bator_jungle

- **mesopredator** — Guillotine trees | Origin: `native` / `pre_compliance` | analogue: `ambush_meso`
  - Bauplan: locomotion `cursorial`, respiration `pulmonary_analogue`, size `medium` (ceiling `large`)
- **producer** — canopy_tree | Origin: `native` / `aboriginal` | analogue: `canopy_tree`
  - Bauplan: locomotion `cursorial`, respiration `pulmonary_analogue`, size `medium` (ceiling `large`)
- **decomposer** — tropical_fungus | Origin: `native` / `aboriginal` | analogue: `tropical_fungus`
  - Bauplan: locomotion `cursorial`, respiration `pulmonary_analogue`, size `small` (ceiling `large`)
- **primary_consumer** — arboreal_browser | Origin: `native` / `aboriginal` | analogue: `arboreal_browser`
  - Bauplan: locomotion `cursorial`, respiration `pulmonary_analogue`, size `medium` (ceiling `large`)
- **secondary_consumer** — ambush_meso | Origin: `native` / `aboriginal` | analogue: `ambush_meso`
  - Bauplan: locomotion `cursorial`, respiration `pulmonary_analogue`, size `medium` (ceiling `large`)
- **apex** — jungle_apex | Origin: `native` / `aboriginal` | analogue: `jungle_apex`
  - Bauplan: locomotion `cursorial`, respiration `pulmonary_analogue`, size `large` (ceiling `large`)
- **scavenger** — forest_scavenger | Origin: `native` / `aboriginal` | analogue: `forest_scavenger`
  - Bauplan: locomotion `cursorial`, respiration `pulmonary_analogue`, size `medium` (ceiling `large`)

### bator_mono

- **primary_consumer** — Grox-Prime (irradiated) | Origin: `exotic` / `imperial_tithe` | analogue: `herd_tithe_stock`
  - Bauplan: locomotion `cursorial`, respiration `pulmonary_analogue`, size `medium` (ceiling `large`)
- **producer** — tithe_crop | Origin: `exotic` / `imperial_tithe` | analogue: `tithe_crop`
  - Bauplan: locomotion `cursorial`, respiration `pulmonary_analogue`, size `medium` (ceiling `large`)
- **decomposer** — soil_amendment_fungus | Origin: `exotic` / `deliberate_transplant` | analogue: `soil_amendment_fungus`
  - Bauplan: locomotion `cursorial`, respiration `pulmonary_analogue`, size `small` (ceiling `large`)
- **mesopredator** — agro_pest_meso | Origin: `exotic` / `deliberate_transplant` | analogue: `agro_pest_meso`
  - Bauplan: locomotion `cursorial`, respiration `pulmonary_analogue`, size `medium` (ceiling `large`)

## Biological risks (locked)

- Bator-Sol radiation
- Predatory flora

## Warnings / contradictions

- specimen guillotine_trees slot mesopredator not in richness ladder for bator_jungle; placing anyway (lock wins)
