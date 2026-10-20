# ROSE

Rose engine source, art, documentation, and the browser physics lab.

- **Engine:** [`rose/`](rose/) contains all 1,100 members of the supplied Rose 0.18.0 archive. Start with [the engine README](rose/README.md); Windows users can launch `rose/Start-Windows.bat`.
- **Browser physics lab:** [`physics-lab/`](physics-lab/) contains the material, force, aging, destruction, telemetry, and seamless-terrain/monolith study. Serve that directory locally with `python -m http.server 8080 --directory physics-lab`, then open `http://localhost:8080`. It is a separate browser emulation, not the complete Python engine.
- **Supplied standalone references:** [`reference-files/`](reference-files/) retains the two Markdown documents and original comparison image.
- **File verification:** [`upload-manifest.json`](upload-manifest.json) records original archive provenance and per-file hashes.

The original ZIP is 393,034,436 bytes and exceeds GitHub's normal per-file limit. Its contents are uploaded unpacked, preserving their paths and bytes. No original archive member is omitted.

The engine's historical audit results remain in its documentation. This upload does not claim a new run of those tests. Hosting access for the separately deployed physics lab is independent of this repository.
