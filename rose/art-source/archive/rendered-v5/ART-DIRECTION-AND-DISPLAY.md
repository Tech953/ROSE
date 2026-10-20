# Rose 0.8.0 — Art direction and display

Rose uses tactile, grounded pre-rendered scenery and actors, with muted earth, stone, metal and fabric. Druid craft appears through grown materials and repaired timber; nano systems appear through small embedded devices; neon appears as restrained biolight on useful objects. Hard sunlight, heavy silhouettes and surface wear carry the scene.

## What this release changes

The default **Detailed / Pre-rendered** bank uses five original anatomical field bodies and four regional constructions for each of seven infrastructure functions. Its 1,244 frames share the established camera, actor facings, world placement and 256-entry palette with sixteen shadow-opacity slots. This release applies the supplied prefab sheets to original environment modeling: fitted front/side cladding, window pane and hood details, roof repairs, counter boards, stock wrapping, serviced utility fittings and eroded stone. Finer granular field textures and four distinct path surfaces replace oversized ground scatter and faint path ellipses. The body assets retain their 0.7 geometry, animations and exact atlas bytes after dependency checks. Three palette treatments provide stable patina; they do not add body models. All earlier sources and atlas bytes, including fidelity-v4, remain preserved. See `PREFAB-REFERENCE-GUIDE.md` for the 22-sheet mapping.

Each person has a persistent visual designation connected to their registered character. Character creation can choose a field presentation independently of stats and pronouns. Automatic follows discipline and embodiment. Travel, recruitment and dialogue preserve that identity. Each structure chooses its regional architecture and retains a sector-qualified designation; condition below 50 or isolation selects a rendered worn frame. The same key and current frame govern art, bounds, alpha picking and prop fading. Scenery cells have extra transparent render margins to retain complete roof shadows. Native cells gain 50% more pixels on each axis, with an inverse 2/3 drawing scale preserving the foot origin and world placement. Scenery keeps its transparent margins; collision cells do not grow. Selecting a person, structure or obstacle opens an enlarged rendering of that same current field asset, facing, patina and condition. This view is read-only and is not a separate portrait asset.

**Soft Phosphor** adds a restrained display pass to local field art. **Sharp Pixels** draws the native field without that pass. The header **CRT OFF** control also bypasses it. The graphics bank, display profile and CRT preference are separate settings; changing one spends no AP, advances no game turn and changes no saved world record.

| Choice | Appearance | Persistence |
| --- | --- | --- |
| Detailed / Pre-rendered | Distinct bodies, regional architecture, worn condition frames and stable patina | Browser graphics preference |
| Original 3D / Archive | Preserved first 3D bake, original colors and materials | Browser graphics preference |
| CRT / Material Prefabs | Preserved earlier painted material sheets | Browser graphics preference |
| Original Vector Style | Preserved geometric field renderer | Browser graphics preference |
| Soft Phosphor | Gentle pixel blending, static fine scanlines, modest glow and darkened edges | Browser display preference |
| Sharp Pixels | Native field samples and indexed-art texture | Browser display preference |
| CRT Off | Complete local-field display-pass bypass | Browser CRT preference |

The Detailed bank uses its baked shadows without adding an oval placeholder beneath each object. Role rings and selection outlines remain visible. Earlier styles and missing-image fallbacks retain their previous presentation. The world map remains a clear travel instrument with selectable destinations and arbitrary land points. Local exploration and tactical combat still share the bodily hex scene.

## Hidden local hexes, movement cost and range

Local field positions are axial hex coordinates, hidden during ordinary play. **HEX GRID** reveals the overlay when wanted. The fixed isometric projection and between-cell animation describe those positions on screen; submitted movement and action targets resolve to registered cells or object IDs. Pixels do not determine combat range.

A move commits one of six adjacent cells after the host checks passability, occupancy, turn ownership and AP. The default combat movement cost is **1 AP per hex**, configurable to 1 or 2 in the saved world rules. Route previews count actual walked steps, including detours. Outside combat, movement spends energy and applies one survival/ecological cycle per six local steps, with no combat AP charge. Each step retains the existing skill/context/standing check.

| Local action | Authoritative spatial rule |
| --- | --- |
| Walk | One adjacent passable, unoccupied hex per committed step |
| Staff strike | One visible hex |
| Crystallin shot | One through six hexes, clear line of sight, registered weapon/ammunition |
| Construct negotiation | Within four visible hexes |
| Selected resident conversation | Within two hexes of the registered resident |
| Generated structure work / public-stock access / exchange trade | One adjacent hex beside the target structure |
| Companion make room | Adjacent companion; one free neighboring destination, plus willingness and check |
| Look / sensory observation | Registered scene target; read-only observation can use labelled remote scope |

Direct range uses cube distance: `max(abs(dq), abs(dr), abs(dq + dr))`. Walking uses routes through neighboring cells, so a detour can cost more AP than direct target range. Line-of-sight checks traverse intervening hexes and reject opaque barriers. Cover, inventory, credentials and skill/context/standing checks then add their own prerequisites and outcome rules.

The overworld remains continuous point travel with selectable destinations and explicit local entry. This local hex system applies inside each location.

The original Fallout manual, printed page 5–3, Table 5-1, lists walking at one AP per hex; the same page describes movement-cursor cost feedback. This provides a primary reference for the local AP convention. Rose's weapon ranges, survival costs and interactions remain its own rules. [Original Fallout manual](https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/38400/manuals/Fallout_manual_English.pdf?t=1572025441).

## Material recipe

`art-source/render-settings.json` owns the baseline material controls, camera, light and timing. `tools/reference_models.py` owns the new environment-only wear, terrain and cladding recipes. The current set uses Cycles on CPU, 48 jittered ray samples, denoising, native higher-resolution body/scenery cells, 2× ground rendering and seed 417. Sun energy is 2.65, sun angle 4°, ambient strength 0.42 and ambient RGB `[0.48, 0.455, 0.40]`. The camera registration is unchanged: −45° azimuth, approximately 31.332° elevation and a 0.52 ground-depth compression.

| Surface | Linear base RGB | Roughness | Treatment |
| --- | --- | ---: | --- |
| Metal | `[0.19, 0.21, 0.185]` | 0.53 | Dull olive-gray patina with controlled highlights; metallic 0.46 |
| Brass | `[0.36, 0.27, 0.14]` | 0.57 | Tarnished warm fittings; metallic 0.52 |
| Cloth | `[0.235, 0.205, 0.145]` | 0.92 | Worn brown fabric with grain and broad mottling |
| Leather | `[0.16, 0.105, 0.066]` | 0.72 | Rounded boots and worn costume fittings |
| Skin | `[0.43, 0.285, 0.185]` | 0.66 | Subdued subsurface response and fine relief; lighter and deeper variants |
| Timber | `[0.215, 0.14, 0.075]` | 0.93 | Elongated color grain and physical plank joints |
| Canvas | `[0.36, 0.31, 0.225]` | 0.94 | Weathered tan coverings |
| Concrete | `[0.215, 0.205, 0.175]` | 0.95 | Dry gray-brown panels |
| Stone | `[0.275, 0.27, 0.215]` | 0.96 | Muted, coarse mineral faces |
| Leaves | `[0.19, 0.255, 0.105]` | 0.90 | Dull living olive; region descriptions retain the world lore |
| Nano indicator | `[0.18, 0.49, 0.385]` | 0.77 | Small cyan-green accent; emission 0.32 |
| Rose indicator | `[0.38, 0.13, 0.17]` | 0.86 | Small red-purple accent; emission 0.08 |

Non-emissive materials combine fine noise at scale 34 with broad weathering noise at scale 2.1. Broad color multiplication uses strength 0.24; bump strength is 0.16 with distance 0.007, reduced to 0.0015 for skin. Cloth and timber have additional material-specific detail. Skin uses subdued subsurface scattering; fabric uses a small sheen response. A broad neutral area fill supplements the fixed sun. These nodes belong to the model materials and follow the objects through the prepared poses. They are baked into the sprites. The palette reserves transparent index zero, sixteen black shadow-opacity slots and 239 opaque color entries. The opaque quantizer excludes all shadow slots, keeping opaque black intact. The browser selects prepared variants. Cool-patina and warm-dust treatments are exported through a palette lookup that preserves alpha; the geometry and weathered surfaces originate in Blender.

Environment-only reference materials use separate datablocks, leaving body materials and the shadow floor intact. Wood stretches localized wear along its grain; metal separates highlights from rust; plaster, stone and canvas carry matte handled wear. Terrain uses periodic procedural relief and small physical aggregates in the camera’s ground basis. The palette inherits the exact v4 colors.

Keep chromatic accents small enough that a silhouette reads in grayscale. Reserve brighter status colors for player rings, warnings and selection outlines. Add new weapon/tool silhouettes through the 3D source, with a clear grip, readable stock or head, and a matching action clip. Five body families are shipped; these shared prefabs can recur across NPCs. Registered free-text appearance and inventory still exceed the finite asset library. Costume equipment does not grant possessions or credentials.

## Unit-by-unit art direction

| Field body | Physical design |
| --- | --- |
| Wayfarer | Lean proportions, exposed weathered face, swept gray hair, patched olive layers, gaiters, bedroll and route staff |
| Archivist | Taller narrow proportions, close cropped hair, slate coat tails, single brow lens and document case |
| Artisan | Broad shoulders, bearded jaw, ochre work jacket, leather apron, tool harness and reinforced boots |
| Mediator | Shorter proportions, shaved head, burgundy mantle, layered cloth and provision pack |
| Metal-kin | Humanoid segmented chassis, ceramic faceplate, exposed joint fittings, utility apron and a small seam light |

Darkwood root framing and living roof strips express WN_TOWER. Salvaged panels, louvres, service conduits and armored corners express CITY_CLOUD_S. Plaster piers, clay roof courses and drainage earthwork express ENACT_HILLS. Crystal struts, mineral fins and tensioned canopy fabric express AETHERGALE. Biome floors and solid obstacles carry corresponding relief rather than relying only on a color swap.

For every future named NPC, begin with their existing biography, embodiment, origin, trade, voice, personal items, injuries and faction history. Make an individual art brief and review their silhouette at native field size before adding detailed surfaces. Require consistent face, costume and scale across every facing/action. Keep their authored costume separate from earned equipment until inventory-matched layers are implemented. A unique high-detail sculpt or portrait for every named person is an additional production milestone.

`Rose-individual-prefabs-preview.png` shows actual exported sprites at exact 2× nearest-pixel magnification. Review crops exclude transparent margins and the faintest shadow fringe; runtime frames retain their registered cells. The library is an original tactile prototype, with five body families and regional variants; it is not a finished photorealistic human/architecture library.

## Display implementation and limits

`static/display.js` samples the completed local field art into a reusable 800×496 buffer for the 1000×620 field. This preserves the field aspect ratio. Bilinear reconstruction softens pixel edges; a second smaller buffer provides a weak screen-blended glow at 0.045 opacity. Static scanlines use 0.032 opacity at three-pixel spacing, followed by a mild edge vignette. The profile uses no flashing, random noise, screen shake or animated phosphor trail.

Labels, selected-object outlines and cursor indicators are painted afterward at the native field resolution. HTML text, menus, focus borders and travel controls are outside the compositor. Alpha masks, occlusion checks, route geometry, line of sight and picking continue to use the original sprite frames and registered scene coordinates. The display pass changes the appearance of pixels without changing those records.

The buffers are reused and require no pixel readback. A missing canvas facility disables the pass and retains the normal field renderer. Reduced-motion mode already suppresses the game's continuous animation loop; display treatment remains static when a scene redraws. Blocked browser storage retains the settings for the active page.

This is a CRT-inspired art presentation, with an optional clean display. It approximates softness and contrast; it does not model a particular physical monitor, electron beam, phosphor persistence, color convergence or display calibration. Browser canvas sampling and monitor scaling can differ from the native QA backend.

## Sculptural talking-head production plan

Talking heads should become intimate, tactile performances with asymmetric cheeks, jaw and brow, rough skin, uneven teeth, worn clothing and restrained light. The field camera and portrait camera serve different purposes: portraits use a fixed close view at eye level, with a simple dark setting belonging to that NPC's actual location.

For a production portrait, sculpt an original digital head in Blender or scan an original physical clay sculpture. Retopologize for brow, eyelid, cheek and jaw movement, preserve the rough sculptural surface, texture and light it, then render a prepared 2D portrait atlas. The reference technique digitized sculptures before digital animation; a static clay photo alone does not provide an animated performance.

| Portrait record | Proposed content | Why it matters |
| --- | --- | --- |
| Stable identity | Registered NPC ID and a persisted portrait asset key | A traveler keeps the same face after world generation, travel and save/reload |
| Visible states | Neutral/listening, talk, guarded, pleased, worried, exhausted, hurt | Expression follows the registered attitude and condition |
| Prepared motion | Small blinks, breath, head turns, mouth forms | Gives a sculptural head life without runtime 3D |
| Dialogue binding | Selected resident ID, actual dialogue record and existing skill/context/standing result | Expression supports the character whose dialogue was resolved |
| Spoken performance | Authored recordings and phoneme timing where available | Deliberate lip sync matches actual recorded words |
| Generated text | Text remains readable with listening/talk gestures | Avoids implying voice or phoneme data that has not been produced |

**No portrait atlas, voice acting, scanned clay source or lip-sync system is shipped in 0.8.0.** The shipped talk clips are small field-body gestures. The NPC designation, lore, personality, attitude, faction standing, contracts and dialogue remain individually registered. A finished portrait library is a separate asset milestone, with a text fallback for any missing portrait.

## Reference audit

Tim Cain's GDC postmortem describes Fallout's third-person hex presentation as cavalier oblique, and documents the original 640×480, 256-color display and detailed sprites. It credits Leonard Boyarsky's talking-head idea and Scott Rodenhizer's work, including phoneme matching. Those historical display dimensions describe the original game as a whole; Rose retains its responsive UI and registered field geometry.[1]

Rob Nesler's first-person account in the oral history describes recruiting clay modelers, sculpting the Overseer's head, digitizing heads and passing them to the animation team. Cain and Boyarsky's Dev Game Club interview also discusses clay heads and digitization.[2][3]

The ghoul head example is **Set**, the leader in Necropolis. The supplied phrase “Seth the Ghoul” is corrected in this guide; Seth is the human guard captain at Shady Sands.[4] The H&K G11 and H&K P90c weapon examples belong to **Fallout 2**.[5][6] Their presence alone does not establish how the artists made each weapon asset. Rose's equipment and 3D assets are original to this prototype.

The two supplied YouTube URLs could not be fetched during this audit, and the supplied forum technology page returned an access error. Their contents were not treated as verified testimony. The accessible primary accounts above informed the production distinction between sculpting, digitizing, digital animation and prepared frames.

1. [Tim Cain, Classic Game Postmortem: Fallout — GDC slides, pages 20 and 29–31](https://media.gdcvault.com/gdc2012/slides/Design%20Track/Cain_Timothy_Classic_Game_Postmortem_Fallout.pdf).
2. [World on Fire: The Oral History of Fallout and Fallout 2 — Rob Nesler's talking-head account](https://www.shacknews.com/article/114982/world-on-fire-the-oral-history-of-fallout-and-fallout-2).
3. [Dev Game Club, episode 033 — interview with Tim Cain and Leonard Boyarsky](https://www.devgameclub.com/blog/2016/10/19/dgc-ep-033-interview-with-tim-cain-and-leonard-boyarsky).
4. Character registries: [Set](https://fallout.fandom.com/wiki/Set) and [Seth](https://fallout.fandom.com/wiki/Seth).
5. [H&K G11 — Fallout 2 weapon record](https://fallout.fandom.com/wiki/H%26K_G11).
6. [P90c — Fallout 2 weapon record](https://fallout.fandom.com/wiki/P90c).

## Verification

The release checks the full bake, palette consistency, source/atlas hashes, frame registration and preserved earlier-pack bytes. Native canvas checks compare Sharp and CRT Off against the exact unprocessed image, exercise Soft Phosphor's changed pixels, check buffer dimensions and reuse, retain the rendering context, and test unavailable-canvas fallback. The host flow verifies all five body families, regional graphics, alpha picking, condition frames, sprite loading, all script routes, four graphics choices, saved preferences, native label settings and painting order, and unchanged world state across display changes. The lossless `Rose-display-comparison.png` shows the same frozen field in both profiles. See `VALIDATION.md` for completed test results, repeat-render measurements and remaining browser/Windows coverage.
