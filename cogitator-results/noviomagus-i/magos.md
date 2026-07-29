# Magos Biologis Dossier — noviomagus-i

**System:** system-i-central-bastion
**Seed:** None
**Spark:** False
**Generated:** 2026-07-26T16:45:31Z

## Classification

- **Body kind:** `planet`
- **Planet type (Administratum):** `mining_world`
- **Local notes:** —

## Geology

- Gravity: 0.9 g
- Crust: rocky
- Volcanism: high
- Connectivity: pangaea
- Tidal lock: False
- Hydrosphere: 5%
- Insolation hint: standard (G-dwarf)
- Topology: Mineral crucible world.

## Chemistry & climate

- Atmosphere: thin
- Water: False
- Solvent: water
- Cryosphere: hot
- Climate belts: mineral
- **Immaterium stress:** `minoris`
- Stress reading: Thin omens, rare anomalies; ecology mostly physico-chemical
- Flavor tags: —

## Biomes

- `novio_i_null` — class `barren_null`, richness `None`, medium `terrestrial`, overlay=False
- `novio_i_dock` — class `dock_hull`, richness `sparse`, medium `industrial_void`, overlay=True

## Trophic webs (per biome)

### novio_i_null

- (empty web)

### novio_i_dock

- **microbiota** — Hull / radiation biofilms | Origin: `exotic` / `voidborne` | analogue: `radiation_biofilm`
  - Bauplan: locomotion `crawl`, respiration `filter`, size `microscopic` (ceiling `small`)
- **decomposer** — hull_biofilm | Origin: `exotic` / `voidborne` | analogue: `hull_biofilm`
  - Bauplan: locomotion `crawl`, respiration `filter`, size `small` (ceiling `small`)

## Biological risks (locked)

- Radiation exposure
- Dock contamination

## Warnings / contradictions

- specimen hull_biofilms slot microbiota not in richness ladder for novio_i_dock; placing anyway (lock wins)
