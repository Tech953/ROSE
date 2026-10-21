# Rose reference audit

The original 0.2 mapping below is retained. Rose 0.4 additionally verifies manual printed 4-8 through 4-11 (PDF 47-50) for local cursor/action controls and 5-3 through 5-4 (PDF 81-82) for targeted-shot terminology. See [LOCAL-INTERACTION-GUIDE.md](LOCAL-INTERACTION-GUIDE.md) for the implemented menu, visibility aids and remaining scene-content limits.

Reviewed the two supplied PDFs: `Fallout_manual_English_copy.pdf` (121 PDF pages) and `Fallout 1 Vision Statement.pdf` (6 PDF pages). The manual's illustrated world-map and movement pages were rendered and inspected. The Vision Statement is design intent, including early GURPS references; it is not treated as the shipped game's rules.

| Source and location | Reference principle | Rose 0.2 implementation / limit |
|---|---|---|
| Manual, printed 4—25 / PDF 64 | World view is distinct from the local game map. Exploration reveals nearby map areas. | Separate World Map and Local Field views; persistent per-player visited/viewed sectors. Local hex movement remains bodily and isometric. |
| Manual, printed 4—26 / PDF 65 | Click arbitrary world ground, including unexplored ground, to travel automatically. | Fractional destinations, continuous host-clock marker motion, weighted land routes and click-to-redirect. Numeric controls provide a keyboard alternative. The interpreted world remains finite. |
| Manual, printed 4—26 / PDF 65 | Previously visited locations offer return destinations; arrival offers local entry. | Visited-location buttons, arrival triangle and explicit Enter Location. The separate drawing registry retains source landmarks before physical visits. |
| Manual, printed 4—26 / PDF 65 | Terrain changes travel time; encounters interrupt travel and open a terrain scene. | Terrain speed/cost, traversal checks, survival costs and automatic transition to the existing local combat scene. Routes survive interruptions. |
| Manual, movement and combat sections | Local cursor movement follows hexes; combat spends AP in turns. | Physical local paths, occupancy, collision, initiative, AP, range, line of sight and guard remain authoritative. World travel does not spend local AP. |
| Vision Statement, points 2–4 / PDF 1–2 | Choices have costs, alternative approaches and persistent consequences. | Existing contracts, public stores, maintenance, dialogue memory, factions, combat and parley provide distinct paths. This release does not establish multiple solutions for every possible generated scenario. |
| Vision Statement, points 5–7 / PDF 2–3 | Time, exploration and the journal help the player understand a changing world. | Survival stops, ecological clock, infrastructure ledgers, NPC engagement cycles, discovered routes and persistent journal. No borrowed water-chip deadline or Fallout plot is added. |
| Vision Statement, points 8–10 / PDF 3–4 | Player intent stays central; interface supports actions; NPC reactions remember interaction. | A quieter split-view terminal, retained typed intentions, context/skill/reputation checks, stable NPC lore, attitude, dialogue and faction records. Input remains a bounded parser with optional model interpretation. |
| Vision Statement, point 11 / PDF 4 | On-screen characterization should reflect actions and equipment. | Six directional walk clips and idle/strike/guard/work/talk/down poses; role rings identify player, companions and NPCs. A shared provisional traveler body is used. Individual body forms, outfits and equipment silhouettes are not yet a full art library. |
| Vision Statement, point 12 / PDF 5 | Comprehensive creation and approachable presets support different players. | Existing six disciplines, attributes, training, identity, appearance, voice, biography, goal and boundaries persist throughout the atlas and dialogue system. |

## Art interpretation

The user-requested CRT / prepared-animation style is implemented through original material prefabs, fixed directional frames, a worn terminal enclosure, optional scanlines and reduced-motion support. Darkwood, bio-plast, cultivated earth, salvaged metal and restrained jade/cyan/rose indicators connect the druid, nano and neon palette. Four ground materials share the same lighting and texture scale.

No artwork, characters, map geography, plot or branding from Fallout is embedded in Rose. The PDFs guide controls and the audit; the supplied Rose world documents and drawings remain the world source. The old vector art is selectable and its manifest, prefab source and preview are retained. Generation prompts and image registration are included for reproducible art direction.

## Remaining production work

- Additional body forms, distinct companion silhouettes, armor/loadout variants and fully articulated animation sequences; current attack uses prepared idle/strike/recovery poses rather than a full skeletal motion library.
- Portrait and facial-expression assets, lip sync and voice performance; the current NPC system provides written characterization and memory.
- Bespoke local environments and authored encounter arcs; current local terrain/public works are seeded prefabs with persistent mechanics.
- Full browser, Windows, screen-reader and live LAN playtesting; native canvas and HTTP checks do not establish those results.
