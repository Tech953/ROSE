# Rose 0.13.2 — Continuous scenery and portrait reference guide

Rose's local scenery now covers the viewport continuously. Ground, worn approaches and practical light pools no longer expose the movement cells or the jagged outline of the finite field. Walking, distance, cover, line of sight, action points and physical interactions still use the existing registered hexes.

All seven supplied screenshots have been inspected and retained unchanged in `reference/art/continuous-scenery`. The source record identifies the original files and their checksums. They inform the art direction; their pixels are not used as game textures, sprites or portraits.

## Reference observations and decisions

| Supplied view | Visible quality to carry into Rose | Implementation or production requirement |
| --- | --- | --- |
| Cavern | Continuous irregular floor and rock masses; isolated targeting feedback | Ground has no movement-cell cutout. Original rocks keep their prepared silhouettes. Complete organic cliff/cavern assets remain pending. |
| Interior | Architectural floor patterns, contiguous rooms and walls | Future paving follows the building design; movement hexes must not determine grout lines. Enterable interiors and roof/wall cutaways remain pending. |
| Settlement | Soil and gravel between buildings, natural grass placement, grounded scale | Seeded material patches, scattered fine detail and foot-worn building approaches cover continuous regional ground. |
| Salvage yard | Clusters of machinery, debris and dry vegetation; varied negative space | Future salvage assets need individual source meshes, prepared shadows and grouped placement. Existing terrain dressing remains sparse. |
| Three dialogue views | Sculptural faces, asymmetric wear, location backgrounds, warm lamps and worn CRT panels | Original portrait and dialogue-staging brief below. This update does not introduce a portrait performance bank. |

## Shipped scenery changes

`static/terrain.js` composes existing regional material textures with irregular low-opacity patches, grain and scattered vegetation. Ground cover responds to registered growth. The surface continues past the finite navigation domain, rather than stopping at a polygon made from movement cells. A broad atmospheric vignette has no hex perimeter.

Worn approaches connect the settlement center to reachable building aprons. They follow passable ground, with curved centerlines, rounded ends and layered shoulders. Circulation reservations and utility branches remain navigation/network records: marking a passable tile as `path` cannot paint a lattice into the landscape. Moving characters and ecological growth do not reshape established approaches. Physically present construction stages can add a project approach.

Practical light pools use continuous elliptical gradients and tangent shadows from circular ground-footprint approximations of solid scenery. Opening a blocker restores the receiver behind it. Actor spill retains solid-cell visibility and combines overlapping fixture colors. Neither effect changes sprite alpha, picking masks or physical work/energy records. These are bounded visual approximations, rather than ray-traced illumination or wavelength-resolved optics.

Entry clears the previous selection, so ordinary exploration no longer begins with an automatically selected water structure and tactical route. Structure labels appear when hovered, selected or revealed. Scene Objects, the inspector, construction panels and keyboard controls retain access to registered records.

| Control or situation | Visible behavior |
| --- | --- |
| Ordinary exploration | Continuous ground and scenery; no full grid or automatic route |
| Pointer over ground | One movement indicator can identify the destination |
| Selected destination or object | Explicit route and selection feedback |
| HEX GRID | Optional tactical overlay |
| Active combat | Existing reachable-cell and AP feedback |
| Reveal / hold Shift | Object labels and bounds aid discovery |
| Click beyond the local domain | Notice directs onward travel through World Map |

Ground outside the local domain is scenery. The update does not expand registered fields or create resource patches. Player-planted vegetation remains an authoritative lifecycle record; extra grass marks are cosmetic ground dressing.

## Original sculpted portrait brief

The three additional dialogue references make the face and conversation one scene. Build each named character from their persisted embodiment, appearance, trade, personal history, injuries, attitude and faction ties. Their face must remain stable across dialogue, travel and save/reload.

Use an original Blender sculpt or original physical sculpture digitized for animation. Preserve asymmetry, broad facial planes, rough skin, uneven cloth and readable eyes. Use an eye-level camera and a simple background belonging to the character's location. Worn hardware, warm fixtures and restrained jade/cyan/rose accents should support the face. Field bodies retain the dimetric camera; portraits require separate prepared assets.

Render neutral/listening, talk, blink, guarded, pleased, worried, exhausted and hurt states into registered 2D atlases. Expressions follow resolved attitude and condition. Generated text can use listening/talk gestures; lip sync requires an actual voiced performance and timing data. Written biography alone does not generate a finished animated likeness.

Accept a portrait only after reviewing stable identity, consistent anatomy/clothing, readable native-size expression, prepared lighting/shadows, smooth state transitions, readable dialogue text and a usable text fallback. Review faces and location backdrops individually. Do not replace every resident with one generic head or imply recordings that have not been produced.

**0.13.2 ships this reference brief, not sculpted portrait atlases, voice acting, lip sync or a portrait dialogue interface.** Five shared field-body families and prototype buildings remain the current library. Richer biome dressing, dedicated salvage/interior/cliff assets, individual likenesses and portrait performances are the asset work needed to approach the requested hyper/faux-realism.

## Verification

The full Python suite passes **330 tests in 26.680 seconds**. The full real-HTTP/interface/native-canvas flow passes, including movement/AP combat, two companions, maintenance/trade, construction, optics and hidden VREX/physics integration.

Matched 0.13.1/0.13.2 scenes use identical frozen geometry, sprites, camera and CRT off. Each of two regions preserves **127 sampled sprite/ground picks and 113 navigation paths**. Controls verify continuous opaque ground outside the navigation domain, growth response, stable passable approaches, approach rendering at local radii 5, 6 and 9, explicit grid display, cleared entry selection, onward-travel feedback and unchanged host state. Changing only passable circulation tags produces identical scenery pixels.

Terrain caches retain at most two views; ground-light caches at most thirty-two masks. Focused light controls verify blocked/reopened receivers, additive color, bounded caches and unchanged sprite alpha/shadows. Warm frozen-frame means are approximately **1.5 ms for WN_TOWER** and **1.3 ms for CITY_CLOUD_S** on the native backend. These are draw-only samples, not device FPS or full-browser measurements.

`Rose-continuous-terrain-comparison.png` and `renderer-audit-v0132.json` retain the native evidence. Source meshes, prepared sprites and physics/VREX implementations are preserved. Full browser layout, audible playback, Windows launch, LAN play and human balance remain outside the verified scope.
