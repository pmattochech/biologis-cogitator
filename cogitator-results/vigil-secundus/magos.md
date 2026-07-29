# Magos Biologis Dossier — vigil-secundus

**System:** system-iii-threshold
**Seed:** 42
**Spark:** True
**Generated:** 2026-07-28T22:59:21Z

## Classification

- **Body kind:** `moon`
- **Planet type (Administratum):** `ice_world`
- **Local notes:** Blind tectothermal moon; sonar leviathans.

## Geology

- Gravity: 0.8 g
- Crust: icy
- Volcanism: moderate
- Connectivity: isoterra
- Tidal lock: True
- Hydrosphere: 60%
- Insolation hint: standard (K-dwarf)
- Topology: Blind tectothermal moon.

## Chemistry & climate

- Atmosphere: thin
- Water: True
- Solvent: water
- Cryosphere: cold
- Climate belts: tectothermal, oceanic_abyssal
- **Immaterium stress:** `majoris`
- Stress reading: Recurring veil weather; mutation/psychic pressure shapes niches
- Flavor tags: rift_adjacent

## Biomes

- `vigil_abyssal` — class `oceanic_abyssal`, richness `moderate`, medium `marine`, overlay=False
- `vigil_ice` — class `ice_cryogenic`, richness `sparse`, medium `terrestrial`, overlay=False

## Trophic webs (per biome)

### vigil_abyssal

- **apex** — Sonar leviathans | Origin: `native` / `aboriginal` | analogue: `sonar_leviathan_analogue`
  - Bauplan: locomotion `benthic_crawl`, respiration `gill_analogue`, size `large` (ceiling `leviathan`)
- **producer** — chemosynthetic_mat | Origin: `native` / `aboriginal` | analogue: `chemosynthetic_mat`
  - Bauplan: locomotion `swim`, respiration `gill_analogue`, size `medium` (ceiling `leviathan`)
- **decomposer** — abyssal_detritivore | Origin: `native` / `aboriginal` | analogue: `abyssal_detritivore`
  - Bauplan: locomotion `swim`, respiration `gill_analogue`, size `small` (ceiling `leviathan`)
- **primary_consumer** — benthic_filter | Origin: `native` / `aboriginal` | analogue: `benthic_filter`
  - Bauplan: locomotion `benthic_crawl`, respiration `gill_analogue`, size `medium` (ceiling `leviathan`)
- **mesopredator** — sonar_meso | Origin: `native` / `aboriginal` | analogue: `sonar_meso`
  - Bauplan: locomotion `jet`, respiration `gill_analogue`, size `medium` (ceiling `leviathan`)

### vigil_ice

- **producer** — radiotrophic_lichen | Origin: `native` / `aboriginal` | analogue: `radiotrophic_lichen`
  - Bauplan: locomotion `cursorial`, respiration `pulmonary_analogue`, size `medium` (ceiling `large`)
- **decomposer** — cryo_detritivore | Origin: `native` / `aboriginal` | analogue: `cryo_detritivore`
  - Bauplan: locomotion `cursorial`, respiration `pulmonary_analogue`, size `small` (ceiling `large`)

## Biological risks (locked)

- Vibration predation
- Cryogenic breach
- Immediate thermal collapse

## Warnings / contradictions

- specimen sonar_leviathans slot apex not in richness ladder for vigil_abyssal; placing anyway (lock wins)
