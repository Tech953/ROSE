# Rose 0.8.0 — Detailed 3D sprite pipeline

Rose’s default **Detailed / Pre-rendered** bank uses original Blender meshes rendered into indexed 2D sprites. Five field-body families, a mechanical threat, regional infrastructure, obstacles and ground relief share a fixed dimetric camera. The reference pass refines original scenery using the supplied prefab indexes: fitted cladding, recessed details, granular floors, regional paths, eroded stone and practical repair/service objects. Body geometry and exported PNG bytes remain preserved from 0.7.

The library remains finite. Written appearance stays registered for dialogue; it does not synthesize a new mesh. Costume gear does not grant inventory or permissions. Bespoke faces for every named NPC, inventory-matched weapons, firearm-specific clips, talking portraits, voice and lip sync remain production work.

## Source files

| File | Purpose |
| --- | --- |
| `art-source/Rose-prefabs.blend` | Editable final meshes, shaders, pose controls, keyframes and markers |
| `tools/individual_models.py` | Original body families, regional construction and terrain foundations |
| `tools/fidelity_models.py` | Continuous anatomy, tailored legs/boots, fingers and construction detail |
| `tools/reference_models.py` | Environment-only wear, fitted facades, rocks, field and path relief |
| `tools/body_dependencies.py` | Fail-closed body/studio dependency fingerprint |
| `tools/compose_reference_pack.py` | Verified archived-body and current-environment composition |
| `art-source/prefab-references.json` | All 22 supplied sheet identities and dimensions |
| `art-source/body-reuse-proof-v5.json` | Before/after body dependency and archived-recipe evidence |
| `static/visual-catalog.json` | Profile names, role defaults, regions, functions and tone treatments |
| `visuals.py` | Persistent designation, independent of simulation RNG |
| `art-source/render-settings.json` | Fixed camera, lighting, sampling and action timing |
| `art-source/render-catalog.json` | Exact timelines, clips, cells, origins and per-model supersampling |
| `art-source/rose-palette-v5.json` | Common RGB palette and reserved shadow-opacity slots |
| `art-source/render-record.json` | Final saved-source and shipped-atlas checksums |
| `art-source/rerender-check-v5.json` | Measured repeat-render comparison |
| `tools/render_blender.py` | Procedural source construction and optional rendering |
| `tools/render_saved_blend.py` | Render saved geometry without rebuilding it; supports independent shards |
| `tools/merge_render_shards.py` | Require matching source, settings, complete models and file coverage |
| `tools/export_sprites.py` | Palette learning, indexed shadows, tone lookup, atlas export and previews |
| `art-source/archive/rendered-v4/` | Exact 0.7 source, full recipe, manifest, receipts and previews |
| `art-source/archive/rendered-v3/` | Exact 0.6 source, recipe, manifest, receipts, body-reuse proof and review panels |
| `art-source/archive/rendered-v2/` | Preserved grounded 0.5 source and receipts |
| `art-source/archive/rendered-v1/` | Original first 3D source and selectable archive bank |

`refine_fidelity_source.py` and `configure_fidelity_render.py` document the development refinements to the saved trial. A fresh build includes final anatomy, materials and reference-driven environment models. `refine_reference_source.py` documents the one-time 0.7-to-0.8 environment update; it requires the preserved 0.7 source and fails if body dependencies change. Repeated source editing should use the saved `.blend` and normal renderer rather than rerunning development patches.

The runtime needs Python and a JavaScript-enabled browser. Blender and Pillow are authoring tools only.

## Coverage and registration

| Source models | Raw frames |
| --- | ---: |
| Five field-body families, 192 frames each | 960 |
| One construct threat, 192 frames | 192 |
| Four regional power collectors, four idle and four worn frames each | 32 |
| Six other functions in four regions, idle and worn | 48 |
| Four regional obstacles | 4 |
| Four modeled field fills | 4 |
| Four modeled regional path fills | 4 |
| **46 models** | **1,244** |

Each body and construct has idle, walk, attack, guard, work, talk, hit and down in six facings. Source cells gain 50% more pixels on both axes; an inverse **2/3 runtime scale** preserves the existing world footprint and foot registration.

| Model type | Native cell | Projected foot origin |
| --- | --- | --- |
| Character | 192 × 192 | `[96.000057, 136.621485]` |
| Scenery | 288 × 336 | `[144.000051, 202.849943]` |
| Ground | 192 × 240 | `[96.000046, 154.849942]` |

Scenery retains its expanded transparent margins. Its 48 source pixels per world unit become the existing 32 drawing pixels after scaling. Do not crop runtime frames or recenter feet around changing silhouettes. Ground pattern transforms use the same drawing scale. The scene’s hex collision, movement costs and cover are independent of these image cells.

Forty-six base atlases gain 74 cool-patina/warm-dust palette treatments, for **120 PNGs and 132 game entries**, including role/function aliases. Treatments preserve every alpha value; they are not new meshes. The earlier v1, v2, v3 and v4 atlas bytes remain unchanged. The new body and body-treatment PNGs match their v4 bytes.

## Materials, light and indexed shadows

The orthographic camera stays at −45° azimuth and `asin(0.52)` = 31.332° elevation, with six 60° facing rotations. Cycles CPU uses seed 417, denoising and **48 jittered ray samples**. Body/scenery render at their higher native resolution. Ground renders at **2× resolution** so its central crop retains at least one real source pixel per atlas pixel.

The fixed sun has energy 2.65 and a 4° angle. Ambient strength is 0.42 with neutral warm RGB `[0.48, 0.455, 0.40]`. A broad neutral area fill uses energy 38 and size 5. Fabric includes directional weave, broad handled wear and a small sheen response; timber adds elongated color grain. Skin uses restrained subsurface scattering, subtle grain and reduced bump depth. Metal, leather and masonry have their own roughness and relief.

The palette has **one transparent index, sixteen graded black-shadow indices and 239 opaque RGB entries**. Shadow slots use alpha 15, 30, …, 240 through PNG’s transparency table. Near-black translucent shadow samples choose the closest slot, replacing dotted shadow coverage with smooth grading. Other partially covered edges retain fixed 4 × 4 Bayer coverage. RGB uses Floyd–Steinberg dithering. The opaque quantizer excludes every transparent/shadow slot, so opaque black stays opaque. Tone lookups leave all seventeen reserved indices unchanged.

The browser plays prepared images; it does not run Blender or synthesize bodies from prompts. Selecting an object opens a read-only 360 × 360 view of that same current asset and animation frame. The view applies no world action or equipment change.

## Build or edit

From the `rose` directory, with Blender 4.2 LTS on your PATH:

```sh
blender --background --factory-startup --python tools/render_blender.py -- --output build/detailed --build-only
blender --background --python tools/render_saved_blend.py -- --output build/detailed-render
python tools/export_sprites.py --input build/detailed-render
```

Use the saved-source renderer after editing and saving the `.blend`. Rebuilding procedurally replaces your source edits. `--frames 129,1167,1237` produces a partial visual check, which cannot be exported as a complete game bank.

Independent shards need separate output folders and the same worker settings:

```sh
blender --background --python tools/render_saved_blend.py -- --output build/body-a --threads 3 --models traveler,archivist,artisan
blender --background --python tools/render_saved_blend.py -- --output build/body-b --threads 3 --models mediator,metal_kin,construct
```

Render the remaining 40 model names into another shard. Merge only completed shards from the same final saved source and recipe:

```sh
python tools/merge_render_shards.py --input build/body-a build/body-b build/environment --output build/complete
python tools/export_sprites.py --input build/complete
```

`--resume` requires matching saved source, renderer scripts, Blender version and settings. The normal exporter reuses the v5 palette, which inherits the exact v4 RGB entries and shadow table; use `--rebuild-palette` deliberately after a material-range change. Every frame must pass cell-boundary or opaque-ground validation before export. The manifest is written only after all atlases finish.

`Rose-3D-Render-Frames.zip` contains the complete unquantized frames, catalog, identity and repeat-render measurements. Extract its directory and pass it to `--input` to experiment with export without another full bake. Earlier saved versions retain previous raw bakes. This release freshly renders 92 environment frames from the final source and retains 1,152 body frames from the preserved v4 source. The editable final source has the same verified body dependencies. Receipts carry per-model source hashes, and composition checks the exact archived saved-renderer recipe before reuse.

## Review artifacts

`Rose-individual-prefabs-preview.png` shows bodies and regional buildings at exact 2× nearest-pixel magnification. Review crops omit transparent margins and faint shadow fringes; runtime cells stay complete. `Rose-3D-prefabs-preview.png` shows default infrastructure and six facings. The eight-frame walk GIF retains the opaque palette colors and composites shadow slots against its neutral background. Field, enlarged-detail and display-comparison panels use the actual renderer. `Rose-fidelity-comparison.png` compares preserved v4 scenery with the reference-v5 bank at the same world scale. `Rose-prefab-reference-preview.png` shows the eight current field/path textures at exact 2× nearest pixels.

See `VALIDATION.md` for verification and repeat-render measurements. These are original tactile prototypes, not finished photorealistic human scans or a bespoke likeness for every NPC.

## Reproducing this release’s body reuse

The raw archive already contains the complete composed bank. For a full fresh render, use the normal saved-source commands above. For the documented reuse workflow, first render all 40 non-character models from the final source into complete environment shards, with identical thread settings. Use the previous version of `Rose-3D-Render-Frames.zip` for the 0.7 raw body input.

```sh
python tools/compose_reference_pack.py --bodies build/raw-v4 --environment build/environment-a build/environment-b --output build/complete-v5
python tools/export_sprites.py --input build/complete-v5
```

Composition requires all expected models and files, matching registration and recipes, the final source hash, and unchanged before/after body fingerprints. It rejects missing/duplicate models and unsafe file paths. `body-reuse-proof-v5.json` includes the fingerprint implementation hash; `render-record.json` includes actual per-model source provenance. The archive’s v4 renderer and source are preserved, rather than silently attributing retained frames to a new render.

Path and field materials use periodic procedural relief and repeated small physical scatter. The renderer samples the central opaque ground area; lighting, palette dithering and antialiasing can still produce small edge differences. The runtime clips one shared global pattern to the existing path hexes; it does not restart texture coordinates per tile. See `PREFAB-REFERENCE-GUIDE.md` for all supplied-sheet mappings.
