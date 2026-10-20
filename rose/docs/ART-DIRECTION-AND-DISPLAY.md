# Rose 0.14.0 — Art direction and display

## Current fidelity audit

The [material update](MATERIAL-AGING-AND-DESTRUCTION-GUIDE.md) adds current-object staining, fractures and lower debris piles derived from prepared sprite pixels. Resulting frames share drawing, alpha selection, bounds, inspection and project clipping. These are deterministic prototype condition graphics rather than a new Blender fracture bake; source models and baked PNG bytes remain retained.

The [monolith scale update](MONOLITH-SCALE-GUIDE.md) associates water, power and relay works with original solid 3D cores of approximately four to six character heights. Human-scale service frames and light fixtures remain at their bases. The twelve regional meshes and twenty-four idle/worn frames use a separate software 3D bake and the locked v6 palette. Composed frames share picking, player fade-through, inspection and construction reveal; original Blender sources and sprite PNGs are preserved.

The [0.13.2 update](CONTINUOUS-TERRAIN-AND-PORTRAIT-GUIDE.md) replaces movement-cell cutouts and circulation paint with continuous ground, irregular detail and worn approaches. Ground-light pools and shadows have continuous shapes; actor spill retains solid-cell visibility and additive colors. Structure labels follow hover, selection or Reveal, and entry has no automatic route. All seven supplied references are retained, including the sculpted dialogue-head examples. Matched native fixtures preserve picking, paths and host state. Individual likenesses, richer terrain dressing, dedicated construction/mechanism art, interiors and portraits remain production milestones; fidelity is a partial pass against the requested hyper/faux-realism.

The following material recipe and bake history describe the retained regional spectrum asset release.

Rose uses tactile, grounded pre-rendered scenery and actors, with muted earth, stone, metal and fabric. Druid craft appears through grown materials and repaired timber; nano systems appear through small embedded devices; neon appears as restrained biolight on useful objects. Hard sunlight, heavy silhouettes and surface wear carry the scene.

## Retained regional asset bake

The default **Detailed / Regional Spectrum** bank keeps five anatomical field bodies and four regional constructions for seven infrastructure functions. Its 1,244 frames preserve the established camera, facings, world placement and foot registration. Thirty-four physical practical fixtures and refined wood, stone, metal, canvas and organic materials add regional light, surface relief and controlled highlights. Ninety-two environment frames are newly rendered at doubled maximum sampling and 2× supersampling. All 1,152 raw body/construct frames remain checksum-pinned; current body RGB is reindexed into the new palette while alpha and registration remain preserved. Exact v1–v5 source/atlas bytes are retained.

| Region | Signature | Source direction |
| --- | --- | --- |
| WN_TOWER | Jade canopy and amber hearth | Grown timber, living shade, repaired craft and practical warmth |
| ENACT_HILLS | Ochre earth and buried jade signal | Mineral soil, administrative network and embedded projection |
| CITY_CLOUD_S | Cyan machinery and rose network | Service panels, luminous pillars and cyber-neon infrastructure |
| AETHERGALE | Jade and rose through violet crystal | Crystal surfaces, contrails and lightPROKT motifs |

Each character and structure retains a stable visual designation. The scene, bounds, alpha masks, occlusion and enlarged field appearance use the actual selected asset key. Worn frames follow condition, disabled/offline network status, power deficits and poor garden moisture/growth. Construction stages reveal only the registered portion of the building; planted patches and ground traces follow current lifecycle values. Shared bodies may recur across NPCs. Free-text appearance, stats and inventory remain distinct records; costume gear grants no equipment or authority.

| Browser choice | Appearance |
| --- | --- |
| Signature Radiance | Regional prepared light with local ground pools and actor spill |
| Subdued Radiance | Gentler local spill using the same prepared assets |
| Baked Light Only | Exact prepared field frames without runtime spill |
| Detailed / Regional Spectrum | Current original bodies, regional architecture, condition frames and patina |
| Original 3D / Archive | Preserved first 3D bake |
| CRT / Material Prefabs | Preserved painted material sheets |
| Original Vector Style | Preserved geometric renderer |
| Soft Phosphor | Gentle field pixel blending, static scanlines and restrained glow |
| Sharp Pixels / CRT Off | Native field samples; CRT Off fully bypasses the display pass |

Lighting, graphics, display and CRT preferences are saved in the browser. Switching them advances no game turn and changes no world resources, permissions or picking geometry. Runtime spill checks actual fixtures, condition, enabled state, connection and solid blockers. Portable hearths have a documented connection exception. Lit frames are bounded at sixty-four entries, ground-light masks at thirty-two and terrain views at two. Every sprite alpha byte and graded black-shadow pixel remains unchanged.

Field labels and selection outlines render after the display pass. The Detailed bank uses its prepared shadows rather than adding an oval placeholder. World travel stays a clear map instrument; local exploration and combat still share the bodily hex scene. The particle/fractal instrument and branching void text are separate percept views.

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

`art-source/render-settings.json` owns baseline studio, materials, camera and timing. `tools/reference_models.py` retains fitted facades, wear, rocks and terrain; `tools/spectrum_models.py` adds separate environment material response and practical lights. `static/lighting-signatures.json` carries the four authored regional profiles. These profiles use artistic RGB values rather than measured wavelengths.

The unchanged body studio uses forty-eight Cycles CPU samples and seed 417. New scenery and ground use a ninety-six-sample maximum, 2× supersampling, adaptive threshold 0.035/minimum twenty-four, denoising and eight AO bounces. Regional sun, fill and ambient colors follow the chosen model's signature. The camera stays at −45° azimuth, about 31.332° elevation and 0.52 ground compression.

Timber preserves grain and fitted joints; cloth shows directional weave and broad handled wear; skin retains restrained subsurface response. Environment metal separates reflective highlights from matte corrosion, stone/plaster carries localized roughness, and canvas/organic surfaces preserve readable silhouettes. Physical practical emitters cast prepared light into the materials. Runtime pools and body spill support nearby service light without replacing these prepared forms.

The newly learned common v6 palette reserves one transparent slot, sixteen black-shadow alpha slots and 239 opaque colors. Floyd–Steinberg color dithering and fixed Bayer partial-edge coverage preserve the low-resolution texture. Palette treatments leave alpha intact. Body raw renders are unchanged; their new RGB quantization differs from the old bank. The archived v5 palette and atlas bytes remain available for exact prior-color reference.

Keep luminous accents concentrated at practical fixtures and signaling surfaces. Larger forms should remain readable in grayscale. New tools/weapons need their own source geometry, clear grips and matching clips. Five shared bodies remain prototypes; individual registered character lore does not imply a bespoke mesh or likeness.

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

**No portrait atlas, voice acting, scanned clay source or lip-sync system is shipped in 0.13.2.** The shipped talk clips are small field-body gestures. NPC designation, lore, personality, attitude, standing, contracts and dialogue remain individually registered. The three added dialogue screenshots guide original sculpts, location backgrounds, warm lamps and worn CRT framing. A finished portrait library is a separate milestone, with a text fallback. See the [current reference guide](CONTINUOUS-TERRAIN-AND-PORTRAIT-GUIDE.md) for acceptance criteria and coverage.

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

The release checks the full composed bake, palette consistency, source/atlas hashes, retained raw-body provenance, alpha/registration and preserved earlier-pack bytes. Regional lighting, physical construction, ecology, particle continuity and void returns are also covered. Native canvas checks compare Sharp and CRT Off against the exact unprocessed image, exercise Soft Phosphor's changed pixels, check buffer dimensions and reuse, retain the rendering context, and test unavailable-canvas fallback. The host flow verifies all five body families, regional graphics, alpha picking, condition frames, sprite loading, all script routes, four graphics choices, saved preferences, native label settings and painting order, and unchanged world state across display changes. The lossless `Rose-display-comparison.png` shows the same frozen field in both profiles. See `VALIDATION.md` for completed test results, repeat-render measurements and remaining browser/Windows coverage.
