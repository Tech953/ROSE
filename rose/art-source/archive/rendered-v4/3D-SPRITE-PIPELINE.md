# Rose 0.7.0 — Detailed 3D sprite pipeline

Rose’s default **Detailed / Pre-rendered** bank uses original Blender meshes rendered into indexed 2D sprites. Five field-body families, a mechanical threat, regional infrastructure, obstacles and ground relief share a fixed dimetric camera. This fidelity pass refines continuous facial and clothing volumes, eyelids, lips, individual fingers, rounded boots, wood grain, woven fabric, surface wear and practical building detail.

The library remains finite. Written appearance stays registered for dialogue; it does not synthesize a new mesh. Costume gear does not grant inventory or permissions. Bespoke faces for every named NPC, inventory-matched weapons, firearm-specific clips, talking portraits, voice and lip sync remain production work.

## Source files

| File | Purpose |
| --- | --- |
| `art-source/Rose-prefabs.blend` | Editable final meshes, shaders, pose controls, keyframes and markers |
| `tools/individual_models.py` | Original body families, regional construction and terrain foundations |
| `tools/fidelity_models.py` | Continuous anatomy, tailored legs/boots, fingers and construction detail |
| `static/visual-catalog.json` | Profile names, role defaults, regions, functions and tone treatments |
| `visuals.py` | Persistent designation, independent of simulation RNG |
| `art-source/render-settings.json` | Fixed camera, lighting, sampling and action timing |
| `art-source/render-catalog.json` | Exact timelines, clips, cells, origins and per-model supersampling |
| `art-source/rose-palette-v4.json` | Common RGB palette and reserved shadow-opacity slots |
| `art-source/render-record.json` | Final saved-source and shipped-atlas checksums |
| `art-source/rerender-check-v4.json` | Measured repeat-render comparison |
| `tools/render_blender.py` | Procedural source construction and optional rendering |
| `tools/render_saved_blend.py` | Render saved geometry without rebuilding it; supports independent shards |
| `tools/merge_render_shards.py` | Require matching source, settings, complete models and file coverage |
| `tools/export_sprites.py` | Palette learning, indexed shadows, tone lookup, atlas export and previews |
| `art-source/archive/rendered-v3/` | Exact 0.6 source, recipe, manifest, receipts, body-reuse proof and review panels |
| `art-source/archive/rendered-v2/` | Preserved grounded 0.5 source and receipts |
| `art-source/archive/rendered-v1/` | Original first 3D source and selectable archive bank |

`refine_fidelity_source.py` and `configure_fidelity_render.py` document the development refinements to the saved trial. A fresh build already includes the final anatomy and materials. Repeated source editing should use the saved `.blend` and normal renderer rather than rerunning development patches.

The runtime needs Python and a JavaScript-enabled browser. Blender and Pillow are authoring tools only.

## Coverage and registration

| Source models | Raw frames |
| --- | ---: |
| Five field-body families, 192 frames each | 960 |
| One construct threat, 192 frames | 192 |
| Four regional power collectors, four idle and four worn frames each | 32 |
| Six other functions in four regions, idle and worn | 48 |
| Four regional obstacles | 4 |
| Four modeled ground fills | 4 |
| **42 models** | **1,240** |

Each body and construct has idle, walk, attack, guard, work, talk, hit and down in six facings. Source cells gain 50% more pixels on both axes; an inverse **2/3 runtime scale** preserves the existing world footprint and foot registration.

| Model type | Native cell | Projected foot origin |
| --- | --- | --- |
| Character | 192 × 192 | `[96.000057, 136.621485]` |
| Scenery | 288 × 336 | `[144.000051, 202.849943]` |
| Ground | 192 × 240 | `[96.000046, 154.849942]` |

Scenery retains its expanded transparent margins. Its 48 source pixels per world unit become the existing 32 drawing pixels after scaling. Do not crop runtime frames or recenter feet around changing silhouettes. Ground pattern transforms use the same drawing scale. The scene’s hex collision, movement costs and cover are independent of these image cells.

Forty-two base atlases gain 74 cool-patina/warm-dust palette treatments, for **116 PNGs and 128 game entries**, including role/function aliases. Treatments preserve every alpha value; they are not new meshes. The earlier v1, v2 and v3 atlas bytes remain unchanged.

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

Render the remaining 36 model names into another shard. Merge only completed shards from the same final saved source and recipe:

```sh
python tools/merge_render_shards.py --input build/body-a build/body-b build/environment --output build/complete
python tools/export_sprites.py --input build/complete
```

`--resume` requires matching saved source, renderer scripts, Blender version and settings. The normal exporter reuses the v4 palette; use `--rebuild-palette` deliberately after a material-range change. Every frame must pass cell-boundary or opaque-ground validation before export. The manifest is written only after all atlases finish.

`Rose-3D-Render-Frames.zip` contains the complete unquantized frames, catalog, identity and repeat-render measurements. Extract its directory and pass it to `--input` to experiment with export without another full bake. Earlier saved versions retain previous raw bakes. This release renders every model from one final saved source; the earlier verified body-reuse workflow remains historical under the v3 archive.

## Review artifacts

`Rose-individual-prefabs-preview.png` shows bodies and regional buildings at exact 2× nearest-pixel magnification. Review crops omit transparent margins and faint shadow fringes; runtime cells stay complete. `Rose-3D-prefabs-preview.png` shows default infrastructure and six facings. The eight-frame walk GIF retains the opaque palette colors and composites shadow slots against its neutral background. Field, enlarged-detail and display-comparison panels use the actual renderer. `Rose-fidelity-comparison.png` compares preserved v3 art with the new bank at the same world scale.

See `VALIDATION.md` for verification and repeat-render measurements. These are original tactile prototypes, not finished photorealistic human scans or a bespoke likeness for every NPC.
