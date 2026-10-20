# Preserved original 3D pack

This directory preserves the Rose 0.3.0 editable source and original procedural recipe. Its 14 indexed atlas files remain unchanged under `static/art/rose-3d-*-v1.png`; `static/art-manifest-rendered-legacy.json` selects them. The original source and atlas hashes are retained in `render-record.json`. The runtime labels this pack **Original 3D / Archive**.

The copied scripts are historical source. They expect their original project layout. To rebuild this archive, copy the project to a separate folder, replace its three `tools` scripts and five `art-source` files with the corresponding archived versions, and follow the 3D pipeline commands there. Avoid running the historical export against the current default pack. The current tools can rerender this saved Blender source with `--blend art-source/archive/rendered-v1/Rose-prefabs.blend` into a separate raw-frame folder; use the historical exporter in the isolated copy to pack those frames.
