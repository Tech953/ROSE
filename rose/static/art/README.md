# Rose rendered prefabs, material art and preserved vectors

Rose 0.13.3 adds twelve `rose-monolith-*-v1.png` atlases containing twenty-four prepared condition frames. Closed original 3D cores associate with the water, power and relay service sprites at their foot origins. The complete Detailed bank now has 132 indexed PNGs and 144 game entries. These additions use a separate NumPy/Pillow software 3D bake and the locked v6 palette; the Blender source bank described below stays unchanged. See `../../docs/MONOLITH-SCALE-GUIDE.md` for scale, registration, provenance and rebuilding.

The retained Blender portion of **Detailed / Regional Spectrum** uses 120 `rose-3d-*-v6.png` atlases and 132 game entries in `../art-manifest-rendered.json`. The complete bank has 1,244 prepared Blender frames from 46 original models: five body families, one construct, 28 regional infrastructure models, four obstacles and eight field/path surfaces. Regional materials and 34 practical fixtures supply druid jade/amber, ochre/jade, cyber cyan/rose and violet/crystal signatures. The 92 environment frames are new; 1,152 raw body frames, geometry, registration and exported alpha remain preserved. Body RGB is reindexed into the newly learned common v6 palette. Its transparent slot, sixteen black-shadow opacity slots and 239 opaque colors preserve the indexed style. Earlier v1–v5 atlases remain unchanged. Runtime Signature/Subdued/Baked light preferences affect appearance only. See `../../docs/3D-SPRITE-PIPELINE.md` and `../../docs/PREFAB-REFERENCE-GUIDE.md`.

The selectable **Original 3D / Archive** bank uses the preserved fourteen `rose-3d-*-v1.png` atlases and sixteen gameplay entries in `../art-manifest-rendered-legacy.json`. Its exact source/recipe lives under `../../art-source/archive/rendered-v1/`. The v2, v3, v4 and v5 source/atlas bytes also remain preserved.

The preserved **CRT / Material Prefabs** style uses these original, generated image sheets:

- `rose-prefabs-crt-v1.png`: seven public-works families, rocks and a quadruped maintenance construct.
- `rose-ground-materials-v1.png`: four regional surface materials, mapped onto the local floor.
- `rose-traveler-walk-v1.png`: four walking frames in each of six isometric directions.
- `rose-traveler-actions-v1.png`: idle, strike, guard, work, talk and down poses in six directions. Attack combines prepared idle/strike/recovery frames; environment props are static sprites.

Generation used built-in image generation. The exact prompts are retained in `../../docs/ART-PROMPTS.json`. The camera, foot placement, light direction, worn materials and restrained jade/cyan/rose indicators form the art direction. The shared traveler is a provisional visual body; character creation, equipment statistics, lore and dialogue remain distinct saved records.

Select **Original Vector Style** in Graphics to use the original shape/pose implementation. Its exact earlier source is archived as `prefabs-vector-v0.1.js`, its manifest is `../art-manifest-vector.json`, and its earlier preview is `../../docs/Rose-vector-preview.png`.

## Register another sheet

Put original PNG/WebP files here using letters, numbers, dots, underscores or hyphens. Files are served at `/art/NAME.png` or `/art/NAME.webp`. No runtime dependency download is needed.

`../art-manifest.json` registers source rectangles and animation clips. Single-sheet `frames` are `[x,y,width,height]`; multi-sheet frames add a fifth sheet index and use `images` instead of `image`. `anchor` is a shared foot anchor, or `anchors` supplies one per frame. `scale` is shared, or `scales` supplies one per frame. Directional clips use names such as `walk_0` through `walk_5`, with generic clips as fallback. Direction order is east, northeast, northwest, west, southwest, southeast. Ground entries use kind `texture`.

The developer-only `../../tools/build_art_manifest.py` registers the bundled sheets using their actual dimensions and alpha foot bounds. It requires Pillow and does not modify the generated images. The game host itself requires only the Python standard library.

Gameplay owns animation state, position and facing. Art cannot alter collision, range, conditions, reputation or permission. Image-loading failure retains the vector fallback. No Fallout assets, portraits or voice performances are bundled.
