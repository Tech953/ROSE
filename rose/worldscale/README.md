# World-scale layer prototype

Additive prototype for the design in `docs/WORLD_SCALE_LAYER.md`:
chunked, streamed terrain underneath Rose's existing isometric
renderer. Nothing here modifies the shipped game — no renderer
changes, no physics changes, no Field Guide core changes, no art,
no save-format changes. Demo terrain only.

## Files

- `projection.mjs` — the projection from `rose/static/scene.js`
  (constants mirrored verbatim) plus a camera translation that is
  exactly the renderer's `project()` at camera (0, 0).
- `chunk_manager.mjs` — the chunk lifecycle: seeded generation
  (a pure function of `(seed, q, r)`, like `world.py`'s sector
  rolls), ACTIVE/PREFETCH streaming window with grace-period
  eviction, and write-through mutations that survive eviction.
- `demo.html` / `demo.js` — pan a camera across a 128×128-sector
  world (16,384 sectors; the shipped atlas is 37×25 = 925) on the
  same 1000×620 canvas, painted with the renderer's projection and
  (r, q) tile order.
- `harness.mjs` — headless verification.

## Run the verification

```sh
node rose/worldscale/harness.mjs
```

It extracts the real `project` function from `rose/static/scene.js`
and asserts numeric parity, checks that chunked assembly reproduces
the renderer's draw order on a 217-hex field straddling eight chunks,
then drives a camera corner-to-corner across the demo world
asserting the active window stays complete, residency stays inside
its bound, evicted chunks regenerate byte-identical, and a mutation
survives eviction.

## Run the demo

Serve the repository root over HTTP (ES modules do not load from
`file://` in most browsers), then open the page:

```sh
python3 -m http.server --directory . 8000
# http://localhost:8000/rose/worldscale/demo.html
```

WASD / arrow keys pan. Bright hexes are ACTIVE chunks, dim hexes the
PREFETCH ring; the HUD reports resident chunks, loads, and evictions
live.
