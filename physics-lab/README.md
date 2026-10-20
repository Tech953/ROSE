# Rose.ENGINE browser physics lab

Serve this folder with any static HTTP server. From the repository root:

```sh
python -m http.server 8080 --directory physics-lab
```

Open http://localhost:8080. No API key, build step, or remote assets are needed.

This is the source of the separate browser prototype: six materials, five structures, forces, equivalent aging, finite salvage and maintenance stock, before/after comparison, telemetry, reduced motion, and matched monolith/seamless-terrain visual review. Experiment state stays in browser-local storage and can be exported as JSON.

The full Python game engine and its original assets live in `../rose/`. This browser workbench is a game-tuned proxy, not a port of that engine or a calibrated engineering tool. Source references are retained in `references/`. The earlier prototype's full modeled-DOM test harness was not available in the surviving local source; this import does not claim a new run of its historical checks.
