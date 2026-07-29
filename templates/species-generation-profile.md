# Species generation profile

Reusable template for elevating Magos niche placeholders into named fauna/flora (dossier + Midjourney).

**Registry order:** names + taxonomy → body/morphology → origin → ecology → look → filing.

**Cogitator source of truth:** [`species-generation-profile.yaml`](species-generation-profile.yaml)  
Edit the YAML to change fields/menus. Restart the cogitator, re-open the species screen, or hit **Reload schema** — no code patch needed. This Markdown file is the human/chat copy (keep roughly aligned).

**Cogitator UI:** Edit body → Specimens → **New** / **Edit**.  
Answers seal under `cogitator-results/<planet>/species/<Entry-ID>/` (`profile.yaml`, `midjourney.md`, `filing-reminders.md`).  
Minimum to save: **Entry ID** + **C17 origin** + **B6 bodyshape** + at least one name (YAML `minimum:`). Section G is reminder-only (no `external/lore/` writes).

Copy this file (or answer in chat by number). Blank fields = invent later.

**Entry ID (required to save):** `AAAA-BBB-NNN` (e.g. `AETH-SHR-001`) or variant `AAAA-BBB-NNN-AA`. Filing key only — not vernacular / Magos binomial. Serial is unique per planet+biome.  
**World / biome / trophic slot (optional):**  

---

## A. Taxonomy & names

1. **Vernacular name** (local / dock speech — working label)?
2. **Formal registry name** (Magos / binomial)?
3–4. Phylum / class (menus below)
5. Confusions to avoid?

Pick phylum/class from the lists (or write **other:** …). Use the **common name in parentheses** when thinking / prompting; the Latin label is for Magos filing.

### Phylum menu (question 3)

| Pick | Phylum (common name) |
| --- | --- |
| P1 | **Chordata** (animals with a backbone / notochord — fish, reptiles, birds, mammals, and analogues) |
| P2 | **Arthropoda** (jointed-limb armor animals — insects, spiders, crabs, and analogues) |
| P3 | **Mollusca** (soft-bodied, often shelled — snails, clams, octopuses, and analogues) |
| P4 | **Cnidaria** (sac-body stingers — jellyfish, anemones, corals, and analogues) |
| P5 | **Echinodermata** (spiny radial sea animals — starfish, urchins, sea cucumbers, and analogues) |
| P6 | **Annelida** (segmented worms — earthworms, leeches, bristle worms, and analogues) |
| P7 | **Nematoda** (roundworms — unsegmented worm tubes) |
| P8 | **Platyhelminthes** (flatworms — flat ribbon / leaf worms) |
| P9 | **Porifera** (sponges — filter mats, no true organs) |
| P10 | **Bryozoa** (moss animals — colonial filter crusts) |
| P11 | **Brachiopoda** (lamp shells — hinged shell, not clam anatomy) |
| P12 | **Ctenophora** (comb jellies — soft luminous swimmers, not true jellyfish) |
| P13 | **Rotifera** (wheel animals — microscopic whirling filterers) |
| P14 | **Tardigrada** (water bears — tiny eight-legged extremophiles) |
| P15 | **Onychophora** (velvet worms — soft lobed-limb worm-predators) |
| P16 | **other** (name + short common gloss) |

### Class menus (question 4) — by phylum

*Only use the block that matches your phylum pick. “Class” here = Magos genetic / body-grade filing, not Earth taxonomy law.*

**If Chordata (backbone line):**

| Pick | Class (common name) |
| --- | --- |
| C-ch1 | **Agnatha** (jawless fish — lamprey / hagfish analogues) |
| C-ch2 | **Chondrichthyes** (cartilage fish — sharks, rays, and analogues) |
| C-ch3 | **Osteichthyes** (bony fish — typical ray-finned / lobe-finned fish analogues) |
| C-ch4 | **Amphibia** (amphibians — frog / salamander / mud-lunger analogues) |
| C-ch5 | **Reptilia** (reptiles — lizard, snake, croc, turtle analogues) |
| C-ch6 | **Aves** (birds — feathered flyers / flightless bird analogues) |
| C-ch7 | **Mammalia** (mammals — fur, milk, warm-blooded analogues) |
| C-ch8 | **other chordate class** (name + gloss — e.g. armored tide-fish grade) |

**If Arthropoda (jointed armor):**

| Pick | Class (common name) |
| --- | --- |
| C-ar1 | **Insecta** (insects — six-leg hexapod analogues) |
| C-ar2 | **Arachnida** (arachnids — spiders, scorpions, mites, and analogues) |
| C-ar3 | **Crustacea** (crustaceans — crabs, shrimp, lobsters, and analogues) |
| C-ar4 | **Chilopoda** (centipedes — many-leg hunters) |
| C-ar5 | **Diplopoda** (millipedes — many-leg grazers) |
| C-ar6 | **Merostomata** (horseshoe-crab grade — shield-body sea arthropods) |
| C-ar7 | **other arthropod class** (name + gloss) |

**If Mollusca (soft / shell):**

| Pick | Class (common name) |
| --- | --- |
| C-mo1 | **Gastropoda** (snails / slugs — crawling foot + often shell) |
| C-mo2 | **Bivalvia** (clams / mussels — two-shell filterers) |
| C-mo3 | **Cephalopoda** (octopuses / squids / cuttlefish — arms + beak) |
| C-mo4 | **Polyplacophora** (chitons — multi-plate armored crawlers) |
| C-mo5 | **other mollusc class** (name + gloss) |

**If Cnidaria (stingers):**

| Pick | Class (common name) |
| --- | --- |
| C-cn1 | **Scyphozoa** (true jellyfish — bell swimmers) |
| C-cn2 | **Anthozoa** (anemones / corals — sessile polyps) |
| C-cn3 | **Hydrozoa** (hydroids / siphonophores — colonial / mixed forms) |
| C-cn4 | **other cnidarian class** (name + gloss) |

**If Echinodermata (radial sea):**

| Pick | Class (common name) |
| --- | --- |
| C-ec1 | **Asteroidea** (starfish) |
| C-ec2 | **Echinoidea** (sea urchins / sand dollars) |
| C-ec3 | **Holothuroidea** (sea cucumbers) |
| C-ec4 | **Crinoidea** (sea lilies / feather stars) |
| C-ec5 | **Ophiuroidea** (brittle stars) |
| C-ec6 | **other echinoderm class** (name + gloss) |

**If Annelida / Nematoda / Platyhelminthes (worm grades):**

| Pick | Class / grade (common name) |
| --- | --- |
| C-wo1 | **Polychaeta** (bristle worms — often marine, parapodia paddles) |
| C-wo2 | **Oligochaeta** (earthworm grade — soil / sediment burrowers) |
| C-wo3 | **Hirudinea** (leeches — sucker worms) |
| C-wo4 | **roundworm grade** (unsegmented nematode tube) |
| C-wo5 | **flatworm grade** (flat ribbon / leaf worm) |
| C-wo6 | **other worm grade** (name + gloss) |

**If Porifera / Bryozoa / Brachiopoda / Ctenophora / Rotifera / Tardigrada / Onychophora:**

| Pick | Class / grade (common name) |
| --- | --- |
| C-ot1 | **sponge grade** (filter mat / vase body) |
| C-ot2 | **moss-animal colony** (bryzoan crust / fan colony) |
| C-ot3 | **lamp-shell grade** (brachiopod hinged shell) |
| C-ot4 | **comb-jelly grade** (ctenophore soft swimmer) |
| C-ot5 | **wheel-animal grade** (rotifer micro-filterer) |
| C-ot6 | **water-bear grade** (tardigrade) |
| C-ot7 | **velvet-worm grade** (onychophoran) |
| C-ot8 | **other** (name + gloss) |

**Answers A:**
- 1 (vernacular):
- 2 (formal registry):
- 3 (phylum):
- 4 (class):
- 5 (confusions):

---

## B. Body plan & morphology

All size, head, **limb**, and **jaw** locks live here.

6. Basic bodyshape?
7. Minimum size (life stage if split)?
8. Maximum size?
9. Sexual dimorphism?
10. How many eyes?
11. **Limb disposition** (list each type)?
12. Ancestral limb count?
13. **Limb mode today?** (A–K; whales/seals = **D** flipper-paddles)
14. **Jaw disposition** (hinges, tusks, tooth rows, beak, etc.)?
15. **Jaw / bite mode today?**
    - A) Crushing / grinding
    - B) Shearing / flesh-cut
    - C) Impaling / tusk-ram (forward spears) ← **Ash-Back tusks**
    - D) Filter / gulp
    - E) Suction / engulf
    - F) Beak / scissor
    - G) Combined (describe in 15b)
    - H) Other (describe in 15b)
16. Skull seams / weak points?

**Answers B:**
- 6:
- 7:
- 8:
- 9:
- 10:
- 11:
- 12:
- 13:
- 14:
- 15:
- 16:

---

## C. Origin

17. Exotic or native to this world?

**Answers C:**
- 17:

---

## D. Ecology & behavior

18. Diet (by life stage if split)?
19. Average lifespan?
20. Predators (by life stage if split)?
21. Temperament (by life stage if split)?

**Answers D:**
- 18:
- 19:
- 20:
- 21:

---

## E. Appearance (for Midjourney / art)

22. Skin / armor / color?
23. Head / face must-haves and hard excludes?
24. What should look “wrong” or iconic at silhouette distance?

**Answers E:**
- 22:
- 23:
- 24:

---

## G. Filing targets (optional — reminders only)

- New dossier path under `external/lore/bestiary/`:
- Update `fauna-flora-named-specimens.md`: yes / no
- Update bestiary `INDEX.md`: yes / no
- Cross-link from geography / Magos food web: yes / no
