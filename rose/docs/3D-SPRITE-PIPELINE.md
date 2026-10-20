# Rose 0.9 — Regional spectrum 3D sprite pipeline

Rose's default **Detailed / Regional Spectrum** bank uses original Blender models rendered into prepared indexed sprites. Four regional lighting signatures, physical practical fixtures and material response extend the existing tactile reference pass. The fixed dimetric camera, native cells, six facings and inverse drawing scale preserve world placement.

The 0.13.3 [monolith extension](MONOLITH-SCALE-GUIDE.md) adds twelve closed solid meshes and twenty-four condition frames through `tools/build_monoliths.py`, a separate NumPy/Pillow software 3D rasterizer. These cores share the camera and v6 palette, and compose behind the unchanged Blender service sprites. The total Detailed bank now contains 132 indexed PNGs and 144 game entries. The Blender bake counts below describe the retained source bank; the new cores are recorded separately under `art-source/monoliths-v1/`. After re-exporting the Blender bank, run `python3 tools/build_monoliths.py` to restore its monument associations.

The asset library remains finite: five shared anatomical body families, one construct, regional public works, obstacles and field/path surfaces. Written appearance, inventory and dialogue stay individually registered; they do not synthesize a new mesh. Bespoke NPC faces, inventory-matched layers, sculpted talking portraits and voice/lip sync remain production work.

The 0.14.0 material extension composes stains, fracture cuts and debris from those actual prepared surfaces in `static/material-visuals.js`. Its cache is bounded at 32 derived frames and shared with drawing/picking/inspection. It does not modify the original bake or add new Blender fracture geometry. See the [material guide](MATERIAL-AGING-AND-DESTRUCTION-GUIDE.md) for physical consequences and production scope.

## Source and provenance

| File | Purpose |
| --- | --- |
| `art-source/Rose-prefabs.blend` | Editable final geometry, shaders, fixtures, pose controls, animation markers and keyframes |
| `tools/individual_models.py`, `tools/fidelity_models.py`, `tools/reference_models.py` | Original bodies, tailored anatomy, regional construction, fitted surfaces, rocks and relief |
| `tools/spectrum_models.py` | Environment-only material response, physical emitters and per-region scene lighting |
| `static/lighting-signatures.json` | Authored WN, ENACT, CITY and AETHER profile definitions |
| `tools/body_dependencies.py` | Fail-closed body/studio dependency fingerprint |
| `tools/refine_spectrum_source.py` | Documented one-time update from the preserved v5 source; fails if body dependencies change |
| `tools/compose_spectrum_pack.py` | Checksum-pinned raw-body reuse and complete fresh-environment composition |
| `art-source/body-reuse-proof-v6.json` | Inherited source/recipe hashes and before/after body dependencies |
| `art-source/archive/rendered-v5/raw-body-checksums.json` | All 1,152 retained unquantized body/construct checksums |
| `art-source/render-settings.json`, `art-source/render-catalog.json` | Camera, baseline studio, timings, exact cells/clips and per-model render settings |
| `art-source/rose-palette-v6.json` | Shared new palette and sixteen reserved black-shadow slots |
| `art-source/render-record.json` | Current saved source and atlas checksums with actual per-model source provenance |
| `art-source/repeat-render-v6.json` | Independent saved-source comparison for two environment frames |
| `tools/render_blender.py`, `tools/render_saved_blend.py` | Fresh procedural source build, or render existing edited source without rebuilding |
| `tools/merge_render_shards.py`, `tools/export_sprites.py` | Strict shard merge, indexed export, palette/tone treatment and review panels |
| `static/visual-catalog.json`, `visuals.py` | Stable presentation designations independent of simulation RNG |
| `art-source/prefab-references.json` | Identities and dimensions of all 22 supplied reference index sheets |
| `art-source/archive/rendered-v1/` through `rendered-v5/` | Preserved previous source banks and recipes; matching earlier atlases remain unchanged |

The 22 supplied Fallout/Pixote index sheets inform original modeling; no sheet pixels, Fallout meshes, portraits or voice are shipped. See `PREFAB-REFERENCE-GUIDE.md` for their exact mapping.

## Coverage and registration

| Source models | Raw frames |
| --- | ---: |
| Five body families, 192 frames each | 960 |
| One construct, 192 frames | 192 |
| Four power collectors, four idle and four worn frames each | 32 |
| Six other functions in four regions, idle and worn | 48 |
| Four regional obstacles | 4 |
| Four field fills and four path fills | 8 |
| **46 models** | **1,244** |

Bodies and the construct carry idle, walk, attack, guard, work, talk, hit and down clips in six facings. Forty-six base atlases gain seventy-four cool-patina/warm-dust treatments: **120 indexed PNGs and 132 game entries**, including aliases. Palette treatments are not new meshes.

| Native cell | Dimensions | Projected foot origin |
| --- | --- | --- |
| Body | 192 × 192 | `[96.000057, 136.621485]` |
| Scenery | 288 × 336 | `[144.000051, 202.849943]` |
| Ground | 192 × 240 | `[96.000046, 154.849942]` |

All use inverse **2/3 runtime scale**. Scenery retains transparent margins and complete roof shadows; do not crop cells or recenter feet around different poses. Alpha picking, enlarged appearance, draw depth and occlusion resolve the same selected asset and current frame. Hex collision and line of sight remain separate host rules.

## Render recipe

The camera stays orthographic at −45° azimuth and `asin(0.52)` = 31.332° elevation. Six facing rotations are sixty degrees apart. Cycles CPU and seed 417 are recorded in the saved-source recipe.

The unchanged body studio uses forty-eight ray samples at the established native resolution. Fresh environment and ground frames use a ninety-six-sample maximum, 2× supersampling, denoising, adaptive threshold 0.035/minimum twenty-four, and eight AO bounces. Each model stores its actual settings in the catalog; the top-level forty-eight-sample baseline does not describe every environment model.

Regional materials are separate from body materials. Wood, stone, metal, canvas and organic surfaces receive controlled roughness, relief, highlights and coating. Thirty-four modeled practical fixtures cast prepared local light across the scenery. Regional scene sun/fill/ambient recipes preserve the same camera. WN combines jade canopy and amber hearth; ENACT ochre earth and buried jade; CITY cyan machinery and rose network; AETHER jade/rose through violet crystal. These are artistic RGB lighting signatures, rather than a wavelength-resolved spectral simulation.

Runtime `lighting.js` can add restrained ground pools and actor spill in Signature/Subdued modes. Actual condition, enabled state, network service and intermediate solid hexes govern that spill. Portable hearths retain their explicit exception to grid connection. The cache holds at most sixty-four current lit frames. Baked Light Only uses original prepared pixels. All modes preserve original alpha and graded black-shadow pixels, exact picking and game state.

## Palette and retained bodies

The v6 palette has one transparent index, sixteen black-shadow alpha indices and 239 opaque RGB entries. Graded shadow alpha is 15, 30, …, 240. Opaque quantization excludes reserved slots; near-black translucent samples use the nearest shadow slot. Remaining partial coverage uses fixed 4 × 4 Bayer coverage, with Floyd–Steinberg RGB dithering. Tone treatments preserve all alpha values.

The palette is newly learned from the current regional material/light range. Therefore current v6 body RGB and indexed PNG bytes can differ from v5. All **1,152 raw body/construct frames**, body geometry, studio dependencies, timelines, foot registration and exported body alpha are preserved. The exact previous v1–v5 atlases remain untouched. The proof traces inherited bodies to their actual original v4 render source; it does not attribute them to a new full body bake.

## Render or edit the saved source

Playing needs Python 3.10+ and a JavaScript-enabled browser. Blender and Pillow are authoring tools only. With Blender 4.2 LTS on your PATH, render artist-edited and saved source without rebuilding it:

```sh
blender --background --python tools/render_saved_blend.py -- --output build/spectrum-render
python tools/export_sprites.py --input build/spectrum-render
```

A partial check such as `--frames 1167,1187` cannot be exported as a complete game bank. For a fresh procedural rebuild, which replaces source edits:

```sh
blender --background --factory-startup --python tools/render_blender.py -- --output build/spectrum-source --build-only
blender --background --python tools/render_saved_blend.py -- --output build/spectrum-render
python tools/export_sprites.py --input build/spectrum-render
```

Independent complete-model shards require identical final source, recipes and worker settings:

```sh
blender --background --python tools/render_saved_blend.py -- --output build/body-a --threads 3 --models traveler,archivist,artisan
blender --background --python tools/render_saved_blend.py -- --output build/body-b --threads 3 --models mediator,metal_kin,construct
python tools/merge_render_shards.py --input build/body-a build/body-b build/environment --output build/complete
python tools/export_sprites.py --input build/complete
```

Render all remaining forty models into the environment shard. Merge rejects incomplete coverage, duplicated models, unsafe paths or mismatching settings. `--resume` requires matching source, renderer and recipe. Export reuses the locked v6 palette; use `--rebuild-palette` deliberately after changing its range. Every raw frame must pass cell-boundary or opaque-ground validation before a complete manifest is published.

## Reproduce the documented raw-body composition

`Rose-3D-Render-Frames.zip` contains all 1,244 unquantized frames, catalog, identity and current proof/repeat-render records. Extract and pass its directory to the exporter to experiment without another full bake. To reproduce this release's reuse procedure, use the previous 0.8 raw bank as body input and render all forty non-body models from the current saved source into matching complete environment shards:

```sh
python tools/compose_spectrum_pack.py --bodies build/raw-v5 --environment build/environment-a build/environment-b --output build/complete-v6
python tools/export_sprites.py --input build/complete-v6
```

Composition checks all pinned body checksums, inherited proof, original body recipe, current source/renderer hash, matching registration, complete model coverage and safe paths. A fresh full render is also possible; it is distinct from the documented retained-body release composition.

## Review artifacts

`Rose-fidelity-comparison.png` compares preserved v5 and current v6 scenery at equal registered scale. `Rose-spectrum-preview.png` shows four regional fields using the actual canvas renderer. `Rose-environment-preview.png` shows foundation/frame/finishing cutaways and planted stages. `Rose-individual-prefabs-preview.png`, the prefab sheet and walk GIF review finite original assets. The field, enlarged detail and Sharp/Soft comparison show real renderer output, rather than full webpage screenshots.

Two independently repeated environment frames from the final saved source have identical decoded RGBA pixels and zero maximum channel difference; PNG metadata bytes differ. This is a two-frame repeat measurement, not a claim of a second complete bake. See `VALIDATION.md` for the complete verified scope and platform limits.
