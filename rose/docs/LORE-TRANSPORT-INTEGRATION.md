# Rose.ENGINE 0.16.0 — Lore transport integration

**0.17.1 supplement:** `reference/visual-corpus/catalog.json` now indexes 93 independently supplied PNG names / 80 unique images, including complete Designer. Browse `/visual-references.html`; see `VISUAL-REFERENCE-REVIEW.md`. The partial ZIP receipt below remains historical.

5 October 2026 · systems and source update

The recovered source pack now supports Rose’s regional descriptions, optional narrator context and NPC biome briefings. It also supplies an authoring catalog for future geography, materials, infrastructure and unit assets. The current update adds source context; it does not claim to have built the additional cities, rendered new sprites or implemented every described phenomenon.

## What is available

The uploaded `LORE TRANSPORT.zip` is 14,544,869 bytes and ends inside `PROTOTYPE IMAGE v2/Designer (2).png`, before the ZIP central directory. An independent download yielded the same bytes. Local member recovery produced **13 complete DOCX documents and four complete PNG images**. Each recovered file matches its advertised ZIP CRC, and all DOCX containers and PNG decodes pass inspection. The incomplete image is excluded; files after it are unknown and unavailable. This is a partial recovery, not a complete repaired archive.

The recovered documents contain **19,468 words**, with **1,504 nonempty paragraphs**. Text extraction retains numbered paragraphs from `word/document.xml`. Structural inspection found no tracked insertions or deletions, tables, embedded images, comments, footnotes or endnotes in these documents. The original DOCX bytes remain available alongside the extracts. Source citations below and in the catalog refer to the extraction’s numbered nonempty paragraphs, rather than Word page numbers.

Five document titles were already represented in the previous engine reference folder: WN_TOWER, ENACT_HILLS, CITY_CLOUD_S, AETHERGALE and NULL_FIELD.OMNI. The new source directory retains this upload separately; previous reference text has not been overwritten. Eight additional source documents are now included.

## Implemented behavior

`reference/lore-transport/catalog.json` contains **11 biome profiles, 58 sourced facts and 43 individually named product specifications**. Each fact carries its document, paragraph span and evidence status. Source-backed setting statements, in-world observation reports, unresolved theories, source fragments, draft lists and visual prototypes retain different classifications.

The four existing engine regions use the catalog’s sensory motifs in their procedural descriptions. Existing ecological state still owns moisture, growth, damage and weather. The new prose does not enact source phenomena, refill supplies or add objects. It is identified as Rose adaptation by the existing description provenance.

At an existing route custodian, select **Ask about the regional biome record**, or type **`ask about biomes`**. The current region supplies a seeded source briefing. The interaction uses the existing Rapport/teaching check with the NPC context and records the character and response in persistent dialogue history. A failed check keeps the explanation provisional. The briefing never confers inventory, a companion, a contract, a credential, an admin identity or a new route.

The optional local narrator receives the current region’s source context and bounded environmental observations. Its instructions distinguish background lore from current objects, people, actions and permissions. Bodily regional context is omitted during remote viewing and `void_null` percept expeditions. No external model is required for the procedural descriptions or biome dialogue.

The source archive is accessible through **World Map → Atlas Record → Lore and biome source archive**. It displays profile records and the four recovered test images, with deliberate full-resolution links. Framework diagrams remain in this reference archive rather than becoming measurements on the play screen.

## Biome mapping

| Source | Environment and infrastructure | Evidence and placement |
| --- | --- | --- |
| WN_TOWER Reference | Neural-wood harvest/recovery, darkwood ash, black soil-clay outskirts, bio-plast maintenance and Greatweb services | Existing interpreted region. Farmland and craft: ¶4–7; Embrite: ¶12–15; Harvet cycle: ¶44–47; MOD_OP: ¶52–54. |
| ENACT_HILLS | Civilian household work and farming, worked-metal teaching, archival boundary, digiPRINT pattern preservation | Existing interpreted region. GRAVESITE: ¶3–6; FOOTHILL CUSP: ¶7–17; UPPER RUNEHILLS: ¶18–22; MMTX<: ¶44–47. |
| CITY_CLOUD_S | Mountain metallurgy, metal salvage, embedded education, contrasting middle and peak access regimes | Existing interpreted region. Eastern mountain city: ¶1–2; ED.NET: ¶3–9; unregulated middle: ¶10–12; peak security: ¶13–16. |
| AETHERGALE | Jade/rose dustland currents, tent settlements, crystalline imbuement, pilgrimage provision and border observation | Existing interpreted region. Contrails: ¶1–6; OMNICURRENT: ¶14–22; RESID: ¶23–26; CASC: ¶27–30; closed gate: ¶36–42. |
| AquiSphere | Re-forming water battlestation, stable iceTRACK, distinct partitions and retained interior defense | Unplaced. Morphology/access: ¶1–12; core: ¶13–14; upper defenses: ¶15–17. No map coordinate inferred. |
| The ArK | Atmospheric branches, runoff-driven growth, sap research, root memetics and organic conversion into Lifestring | Unplaced. Origin/expansion: ¶1–7; conversion: ¶16–19; branches: ¶24–33; roots: ¶46–55. CASC’s recorded interaction does not assign the whole ArK a coordinate. |
| Snail Wood | Mollusk lifecycle, bio-gel stalks, shell dwellings, pilgrimage outposts and reputation-dependent rentals | Unplaced. Lifecycle: ¶1–2; teacher: ¶3–7; contract node: ¶8–10; settlements/services: ¶11–35; properties: ¶34–72. |
| Mesas.D.S.CONV | Neon skyline, fuel and manufacturing supply, vehicle and transit systems, regulated upper districts and changing under-freeway markets | Unplaced. Skyline: ¶1–2; companies/products: ¶3–308; transit/districts: ¶339–406; archive-only STAT.D: ¶407–431; BLACK.HAT: ¶469–476. Visibility from ENACT_HILLS is relative evidence. |
| NULL_FIELD.OMNI | Observed flake/reform constructs, constrained weather, cold projections, conditional teal light and uncertain ceramic/void composites | Remote reports; closed border retained. Independent signatures: ¶7–40; weather/stations: ¶52–115; ceramic observations: ¶120–139; unresolved theories: ¶149–159. |
| io_COMBI_oi | Miles-high bio-glass city, bio-nano self-expression and sustainable service provision | Short unplaced overview, ¶1–2. ContriFID is low priority here; detailed districts are not supplied. |
| mollusk_crescent_MOONLAND | Twilight sand, wild mollusks, hibernation, larval construction and extract-driven terraforming | Unplaced source fragment, ¶1–2. The complete DOCX ends mid-sentence at “imbued through”; the mechanism is unfinished. |

`The Long Tar Location Guide and Plot Ideas` contributes **148 title entries**. `Thorns Book Series` contributes **84 chapter-title entries**. Both lists are preserved for authoring, with paragraph numbers. A title does not establish a location, quest, chronology, faction, route or completed event.

## Unit-by-unit asset references

The Mesas product record retains source designations, classifications, disciplines/materials, contractor, manufacturer and capability text. Its **13 framegens, eight wirelets, 12 bio-mods and 10 defense tools** can inform individual modeling briefs. Source qualitative ranges, speeds and functions remain text; no AP cost, damage, numeric speed, fuel consumption or playable inventory is invented.

| Recovered image | Useful visual requirements | Production boundary |
| --- | --- | --- |
| CORP-E PRODUCTS.png | Distinct vehicle silhouettes, metallic surfaces, crystalline wirelets, brand-specific storefront light and different service presentations | Presentation sheet. It contains no animation frames, alpha cutouts, collision masks, directional views or scale registration. |
| CORP-E PRODUCTS pt. 2.png | Tissue/hard-surface contrast, druid materials, company-specific practical lighting, institutional tools and daily supplies | Presentation sheet. Individual products still need models, shared camera/lighting setup, size references and prepared directional sprites. |
| CODE.png | Percept/semblance distinction, MMTX< baseline, simultaneous encap/resolution and NULL_0 vocabulary | Conceptual pseudocode and setting vocabulary; not executable code or calibrated physics. |
| CODE FINAL.png | Localization, continuation, manifestation views and stated continuity requirements | Filename suggests a revision; precedence over CODE.png is unconfirmed. It supplies no numeric VREX parameters. |

For future prepared assets, keep an individual material identity and readable silhouette before adding emission. Separate dull metal, wet biomass, ceramic, crystal, bio-glass and textile responses. Use source-local practicals—gas.op red, AETHER jade/rose, PYR_REZ conditional teal—without assigning one neon treatment to every object. Colored light should leave surfaces, wear, contact shadows and forms legible. These are production requirements; this update does not claim a higher-resolution sprite bake.

Existing art-source files, prepared assets and art manifests retain their bytes. The original reference PNGs are preserved as references rather than inserted as a replacement environment backdrop.

## Physics, growth and animation handoff

The catalog records dynamic requirements without treating every fictional process as an implemented physical event. Ordinary decay, weather wear, construction, weapon condition, collapse and committed action animation remain owned by Rose’s existing systems. `physics.py`, `vrex.py`, `photonics.py` and `research.py` retain their bytes.

| Source requirement | Existing system to extend | Required work before a playable event |
| --- | --- | --- |
| Wind-worked AETHER tent construction | Weather, material wear and committed motion cues | Cloth response driven by bounded wind, stable anchors and collision-safe geometry. |
| ArK growth and Lifestring conversion | Lifecycle, registered material identity and resource ledgers | Distinct growth/assimilation states, gated extraction, conservation rules and specific assets. |
| AquiSphere reformation | Infrastructure, topology and collision | Reconcile stable access, occupancy and service networks before revealing changed partition geometry. |
| Snail Wood hibernation, death and shell reuse | NPC lifecycle and construction | Distinguish sleeping from dead entities and register ownership and occupancy of reused shells. |
| Mesas vehicles and moving markets | Navigation, materials and infrastructure | Vehicle dimensions, collision envelopes, transit rules, fuel ledgers and safe layout transactions. |
| NULL_FIELD flaking/reformation and particulate capture | Material states, particles and committed visual cues | Preserve report uncertainty; implement a bounded model and matching assets before showing it as current behavior. |
| STAT.D temporal aging reports | Material aging and hidden relational measurement context | Preserve the aging hypothesis as reported lore; do not substitute speculative prose for calibrated time or solver data. |

These handoffs are not active feature claims. They identify where the new source material belongs in later implementation. The existing closed RED>GATE> and ordinary local hex/overworld travel distinction remain authoritative.

## Ambiguity retained

Mesas/CITY_CLOUD_S/ENACT_HILLS/gate spellings appear in several variants. The catalog records them alongside current engine keys without creating extra places. KHO.DEV is explicitly not the KHO processing intelligence (Mesas ¶309–312). The druid role definition in Mesas ¶170 sits alongside other faction/CORP-E terminology, including ¶426; those contexts are preserved. WN’s MOD_OP exchange basis and CITY_CLOUD_S vending currency apply locally rather than defining a universal economy.

NULL_FIELD defines **1 ib = 0.5 miles** at ¶188. That source-local unit supports its reports; it does not establish a conversion from the perceived continent or immense monuments to the finite survey grid. The prior planetary/Africa approximate framing remains intact.

## Verification

Thirteen focused checks pass: recovered-byte identity, source and paragraph resolution, unplaced geography, fragment/draft/theory status, defensive context copies, qualitative unit specifications, read-only prose/briefings, character history, contextual skill checks, failed-check boundaries, current-region narrator context, remote/void separation and bounded local interpretation.

Full engine regression and HTTP/interface results are recorded in `docs/VALIDATION.md` and `docs/validation-results-v016.json`. See those files for the completed run rather than interpreting the handoff table as a tested implementation of new physics or asset generation.

The complete original archive is needed to review `Designer (2).png` and any later references. No claim is made about their content.
