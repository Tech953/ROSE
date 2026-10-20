# Rose 0.8 — Prefab reference guide

Rose uses the 22 supplied Fallout 2 Mapper / Pixote GIF index sheets as visual reference for its original Blender assets. Every supplied sheet is a single-frame index. They do not provide an animation rig, motion timing, collision map or a complete production atlas for Rose. No sheet pixels or meshes are included in the engine ZIP.

This release refines all 28 regional infrastructure models, four obstacle models and four field surfaces, then adds four regional path surfaces. Its 92 newly rendered environment frames join 1,152 preserved body frames. Five body families and the construct keep their established eight action clips in six directions. The shared palette, fixed camera and inverse drawing scale remain consistent across the bank.

## Reference-to-engine mapping

| Supplied sheet | Visual lesson | Rose coverage |
| --- | --- | --- |
| `Critters_PID.gif` | Small grounded body silhouettes, stable identities and readable costume masses. | Five existing body families and six facings retained; body atlas bytes preserved. |
| `Inventory-Images_FRM.gif` | Larger inventory views separate from small ground objects. | Reference registered; item-specific inventory illustrations remain a later asset pass. |
| `Items_PID.gif` | Small floor objects and containers need readable silhouettes. | Reference registered; existing object selection and labels retained, no new loot assets implied. |
| `Markers-Icon_Description.gif` | Editor blockers, light and exit markers describe authoring semantics. | Editor colors stay out of scene art; Rose keeps host-owned passability, visibility and entry rules. |
| `Misc_PID.gif` | Small effect and exit icons use distinct presentation categories. | Reference registered; no new complete effect animation bank added. |
| `Scenery-001_PID.gif` | Containers, worn street props, shelving and practical clutter. | Stock wrapping, loose bench tools and service-drum details on original structures. |
| `Scenery-002_PID.gif` | Mechanical fittings, screens and small industrial props. | Service grilles, pipe details and retained localized nano indicators. |
| `Scenery-003_PID.gif` | Utility objects, infrastructure and weathered industrial mass. | Handled metal and separate rust relief on registered utility models. |
| `Scenery-004_PID.gif` | Vehicles, benches and work-area silhouettes. | Workshop clutter and fitted facade surfaces; no vehicle system added. |
| `Scenery-005_PID.gif` | Rock clusters, debris and irregular natural silhouettes. | Original eroded stones, smaller scree and finer terrain aggregates. |
| `Scenery-006_PID.gif` | Compound industrial forms and substantial scenery pieces. | Regional architecture retains its distinct structural silhouette and rendered condition states. |
| `Scenery-007_PID.gif` | Signs, utility details and mixed environmental props. | Physical service seams and repair details; new signs remain future content. |
| `Scenery-008_PID.gif` | Large compound walls and industrial facade groups. | Structure-wide wear and recessed details rather than additional free-standing runtime walls. |
| `Tiles-001_PID.gif` | Dirty metal and weathered paired floor texture variants. | Finer regional field relief and a worn city path surface. |
| `Tiles-002_PID.gif` | Ground, board and coarse mineral texture groups. | Smaller aggregates, muted soil and decomposing leaf detail. |
| `Tiles-003_PID.gif` | Transition pieces and damaged floor sections. | Path surfaces follow existing path hexes with one shared pattern origin; edge-transition bank remains future work. |
| `Tiles-004_PID.gif` | Crater, water and floor/roof surface variations. | Granular terrain treatment; new water-edge, crater and roof tile systems remain future work. |
| `Tiles-005_PID.gif` | Roof panels, holes and composite roof arrangements. | Separate roof repair patches on original workshops; no new traversable roof layer added. |
| `Walls-001_PID.gif` | Modular wall faces, corners and openings. | Fitted front/side cladding, visible joints and maintained doorway silhouette. |
| `Walls-002_PID.gif` | Weathered masonry, industrial panels and recesses. | Separate plaster/stone/metal finishes, pane, sill and rain-hood treatment. |
| `Walls-003_PID.gif` | Curving plaster, recessed door/window modules, railings and wood supports. | Irregular masonry/plaster treatment and repaired shelter battens; curved runtime wall modules remain future work. |
| `Walls-004_PID.gif` | Timber supports, worn plaster/brick openings and riveted industrial facades. | Regional cladding and industrial service detail; no forcefield or arch-opening gameplay added. |

## Original asset treatment

Buildings gain fitted individual cladding, handled material variation, a smoked window pane and hood, roof patches, counter boards, bindings, small tools and service details. Eroded apron edges and fine rubble soften their original regular platforms. These details belong to each registered structure; they do not create additional interactable items or grant inventory. Healthy and worn clips retain the existing condition rules.

Rock prefabs use irregular eroded volumes and small scree. Field surfaces use fine periodic mineral/soil relief instead of the previous oversized scatter. The forest floor keeps small decomposing leaves; the city path includes worn paving fragments; hills use warm clay; Aethergale uses pale mineral dust. Paths replace the faint ellipse treatment in the Detailed bank. They follow the host’s existing path designations and use the same global pattern origin across clipped hexes. This pass does not change passability, AP costs, cover, line of sight or overworld travel.

The shader and physical scatter use a repeating screen-space period. Exported pixels, tile joins and in-field appearance are reviewed separately: periodic modeling alone does not guarantee pixel-identical opposite image edges after lighting, antialiasing and palette reduction.

## Identity and reproducibility

`art-source/prefab-references.json` records every filename, dimensions, frame count, byte size and SHA-256. `tools/reference_models.py` contains the original environment models and shaders. `art-source/Rose-prefabs.blend` contains the editable final scene. The 0.7 source, recipe, manifest, receipts and previews remain under `art-source/archive/rendered-v4/`; all earlier atlas bytes stay available.

`body-reuse-proof-v5.json` compares the six saved body collections before and after scenery edits. The fingerprint covers mesh faces and vertices, transforms, parents, supported modifiers, material nodes/links, pose curves, body camera, sampling, sunlight and area fill, ambient, shadow floor and color management. Composition checks the archived body renderer recipe and registration before reusing frames. Receipts distinguish the archived body source from the current scenery source. Body and body-treatment PNGs match the preserved 0.7 bytes.

The v5 palette inherits the exact v4 RGB entries and shadow table. This preserves character colors and avoids introducing a second lighting or color standard. A developer can rebuild the palette after a deliberate change to the material range; that is a separate complete export.

## Review and production scope

`Rose-fidelity-comparison.png` compares preserved 0.7 and current 0.8 scenery at equal registered world scale. `Rose-prefab-reference-preview.png` shows the eight actual indexed field/path samples at 2× nearest-pixel magnification. Field and display panels are produced by the real game renderer in the native canvas test backend. They are not full webpage screenshots.

These remain original tactile pre-rendered prototype assets. The library has five shared body families, not a bespoke mesh for every named NPC. New inventory art, item-matched weapons, modular room/wall/roof banks, terrain-edge variants, vehicles, effects, talking portraits, voice acting and lip sync remain production milestones. The reference inventory and marker sheets are documented as guidance; they are not presented as newly implemented systems.

Playing uses Python and a JavaScript-enabled browser. Blender and Pillow are authoring tools only. The software does not require runtime 3D rendering. See `VALIDATION.md` for completed checks and live browser/Windows limits.
