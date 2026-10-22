# World-Scale Layer: Chunked, Streamed Terrain Under the Existing Isometric Renderer

Status: design + prototype (branch `proto/world-scale-layer`). Additive only.
Nothing in this document proposes modifying `rose/static/scene.js`,
`rose/hexgrid.py`, `rose/world.py`, `rose/physics.py`, or the frozen
Field Guide 1.0 core (`generation.py`, `field_rules.py`,
`creature_catalog.json`).

## 1. Where Rose stands today (measured, not assumed)

| Fact | Source | Value |
| --- | --- | --- |
| Overworld extent | `rose/geography.py` (`MIN_X..MAX_X`, `MIN_Y..MAX_Y`) | 37 × 25 sectors = 925, 28 authored landmarks |
| Recorded-site cap | `rose/world.py` (`MAX_CELLS`) | 2,048 visited sectors per save |
| Sector generation | `rose/world.py` (`rng(seed, *parts)`, `terrain(seed, x, y)`) | Pure function of `(seed, x, y)`; sha256-seeded; order-independent |
| Sector persistence | `rose/world.py` (`visit()` → `w['cells']`) | Only *visited* sectors persist, each with a `changes` list |
| Local field size | `rose/scene.py` (`hx.disk(scene_radius)`), `docs/reference-data/rules.json` | radius 5–9 (default 6) → 91–271 hexes |
| Scene projection | `rose/static/scene.js` (`project`) | `[500 + √3·34·(q + r/2), 341 + 34·1.5·r·0.52 − elevation·2]` — pointy-top axial, 0.52 dimetric compression, 2 px elevation lift, fixed 1000×620 canvas, **no camera** |
| Tile draw order | `rose/static/scene.js` (`draw`) | Tiles: sort by `(r, q)`. Props: sort by `(projected y, projected x)` (Y-sorted painter) |
| Overworld map view | `rose/static/overworld.js` (`project`) | Flat `[56 + (x+18)·24, 66 + (y+12)·21]` — constants hard-code the 37×25 atlas; the view cannot leave it |

The gap to a FULL_REZZ-scale world is therefore not the renderer — the
isometric projection and painter's sort are already correct and general —
it is *residency*: today the whole world must fit in one interpreted
rectangle (925 sectors) and one fixed camera. This layer adds residency
(chunking + streaming) and a camera underneath the unchanged renderer.

## 2. Coordinate model

- One **sector** = one overworld cell, addressed by integer axial-style
  coordinates `(q, r)` (the atlas's offset `(x, y)` maps 1:1 to `(q, r)`).
  Sector metadata remains exactly what `world.terrain()` produces today:
  region, terrain, elevation 1–9, moisture, etc.
- One **chunk** = an 8 × 8 block of sectors (64 sectors), addressed by
  `(cx, cy) = (⌊q / 8⌋, ⌊r / 8⌋)` (floor division, so negative
  coordinates chunk correctly).
- The **world** is any rectangle of sectors. The authored atlas becomes
  the starting region of a larger seeded world instead of its boundary.
  The prototype world is **128 × 128 sectors = 16,384 sectors in
  16 × 16 = 256 chunks** — 17.7× the atlas's 925 sectors.

### Why 8 × 8

- A chunk is a *residency unit, not a generation unit*: sector metadata
  is a pure function of `(seed, q, r)`, so "generating a chunk" is 64
  deterministic rolls — cheap, order-independent, and identical on
  regeneration. That property is what makes eviction safe (§4).
- 64 sectors per chunk keeps the full streaming window (§3) at
  25 chunks × 64 = 1,600 sector records — small next to the existing
  2,048-cell save bookkeeping, and local fields stay the real memory
  consumers: a field is 91–271 hexes, fields materialize only for
  occupied sectors, and even 7 simultaneous max-size fields
  (7 × 271 = 1,897 tiles) stay under the spirit of the `MAX_CELLS`
  bound the save format already enforces.
- 8 is a power of two, so chunk addressing is a shift, and a chunk is
  large enough that border crossings are infrequent relative to
  movement, small enough that prefetch waste stays bounded.

## 3. Streaming radii and the camera

The camera is a free-panning position in sector space (float `(cq, cr)`);
the *camera chunk* is the chunk containing it. All distances below are
Chebyshev distances in chunk space from the camera chunk.

| Ring | Distance | State | Contents |
| --- | --- | --- | --- |
| Active | ≤ 1 (3×3 = 9 chunks) | `ACTIVE` | Sector metadata resident; local fields may materialize; fully drawable |
| Prefetch / dormant | ≤ 2 (5×5 = 25 chunks) | `PREFETCH` | Sector metadata resident (seeded generation only); no fields built |
| Beyond | ≥ 3 | — | Eviction candidates |

- **Load**: a chunk entering distance ≤ 2 is generated (metadata only).
  A chunk entering distance ≤ 1 is promoted to `ACTIVE`.
- **Evict**: a resident chunk is evicted only after it has stayed at
  distance ≥ 3 for **2 consecutive camera updates** (grace period).
  Load-at-≤2 plus grace-2 eviction is the hysteresis band: a camera
  jittering across a chunk border cannot thrash the window.
- **Hard bound**: resident chunks never exceed 25 (the 5×5 window) plus
  any chunks still inside their eviction grace — enforced by the
  manager; the prototype harness asserts the bound over a full
  cross-world camera path.
- Multiplayer: the window is the union over connected players' camera
  chunks (host computes it; §6). The prototype is single-camera.

## 4. Chunk lifecycle

```
UNGENERATED ──generate──▶ PREFETCHED ──promote──▶ ACTIVE
     ▲                        │  ▲                    │
     │                        │  └────── demote ──────┘
     └──────── evict ─────────┘   (after grace, distance ≥ 3)
```

- **Generate** is deterministic: `sector(seed, q, r)` is the same pure
  function style as `world.rng(seed, 'terrain', x, y)` (sha256 of
  `seed|terrain|q|r` seeding a PRNG). Regenerating an evicted chunk
  reproduces byte-identical metadata. The harness proves this with a
  chunk checksum taken before and after an evict/regenerate cycle.
- **Mutations never live only in a chunk.** Visited-sector state is
  what `world.cells` already is: a persistent record with a `changes`
  list. The chunk layer writes mutations *through* to that store at
  the moment they happen (prototype: a `persisted` map standing in for
  the save). Eviction therefore only ever drops regenerable metadata —
  never player state — and regeneration re-applies the persisted
  changes on top of the seeded sector. The harness proves a mutation
  survives an evict/regenerate cycle.
- **Dormant is not a stored state**, it is simply `PREFETCH`: metadata
  resident, fields dropped. Dropping a field on demote is free because
  fields are rebuilt from sector + rules by `scene.py`'s existing
  `ensure()` path.
- The save format does not change: a save still stores the world seed
  plus visited cells with changes, exactly as today. Chunks are a
  runtime residency cache and are never persisted.

## 5. Feeding the existing renderer — unchanged

The prototype reuses `scene.js`'s projection verbatim
(`rose/worldscale/projection.mjs` mirrors the constants; the harness
extracts the actual `project` function from `rose/static/scene.js`
and asserts numeric parity, so the mirror cannot silently drift):

```js
// scene.js, today (size = 34, canvas 1000×620)
project(p, elevation = 0) =>
  [1000/2 + Math.sqrt(3) * 34 * (p[0] + p[1] / 2),
   620 * .55 + 34 * 1.5 * p[1] * .52 - elevation * 2]
```

A camera is a pure translation of that anchor — the one-line change a
future integration makes *in the layer*, not in the renderer:

```js
projectWithCamera(q, r, elevation, camQ, camR) =>
  [1000/2 + Math.sqrt(3) * 34 * ((q - camQ) + (r - camR) / 2),
   620 * .55 + 34 * 1.5 * (r - camR) * .52 - elevation * 2]
```

At `cam = (0, 0)` this is exactly `scene.js`'s `project`. Because the
camera term is a translation, relative geometry — and therefore draw
order — is camera-independent.

**Draw order across chunks.** The existing comparators are total orders
over world coordinates and projected coordinates respectively:

- tiles: `(r, q)` ascending;
- props: `(projected y, projected x)` ascending.

Neither references which field or chunk an item came from, so the
painter's order for a streamed world is: *gather draw items from all
resident chunks, sort once with the existing comparator, paint.* The
result is identical to rendering the same hexes as one un-chunked
field. The harness proves this on a 217-hex sample field (a radius-8
disk — inside the real 91–271 field-size range) that straddles chunk
boundaries: chunked assembly sorted with the existing comparator
equals the un-chunked order, for both comparators, including under a
camera offset.

Elevation lift (`− elevation · 2`) is per-hex and unaffected by
chunking; the Blender bake camera already shares this transform, so
baked sprites remain registered at any world size.

## 6. Authority and networking (design position, unchanged model)

Rose is host-authoritative and stays that way. The host owns the seed,
the persisted cell store, and the streaming window (union of player
cameras). Because sector metadata is a deterministic function of the
seed, clients may regenerate *metadata* locally for rendering; all
state (visits, changes, actors) continues to flow from the host
exactly as it does today. No new backend, service, or protocol is
introduced by this layer.

## 7. Memory bounds (prototype-measured)

- Sector metadata record: `{q, r, terrain, elevation, moisture,
  changes}` — a few hundred bytes; the full 5×5 window is
  1,600 records, on the order of 0.5 MB.
- Fields are the bounded heavyweight, as today: one per occupied
  sector, 91–271 tiles each, rebuilt on demand by the existing
  `scene.ensure()` logic.
- The harness prints the observed maxima (resident chunks, records,
  load/evict counts) over a corner-to-corner camera path.

## 8. Explicit non-goals

- **No renderer rewrite.** `scene.js`'s projection, sort, and canvas
  model are untouched; the layer translates the anchor, nothing else.
- **No physics changes.** `physics.py` (rose-planar-1) is untouched;
  physics bodies remain per-field concerns.
- **No Field Guide changes.** The frozen shared core
  (`generation.py`, `field_rules.py`, `creature_catalog.json`) is not
  modified; chunk generation consumes the same seeded-RNG discipline
  the core already uses.
- **No new content generation.** The prototype generates *demo
  terrain classes only* (a five-class palette with elevation/moisture)
  to exercise streaming. It does not add landmarks, regions, or lore;
  the authored atlas remains `geography.py`'s.
- **No art or save-format changes.** No assets are added or altered;
  saves remain seed + visited cells.
- **No networking changes in the prototype.** Single-camera demo;
  the multi-camera union is a design position (§6), not code.

## 9. Prototype map

`rose/worldscale/` (all additive):

| File | What it is |
| --- | --- |
| `projection.mjs` | The scene projection + camera translation, constants mirrored from `scene.js` |
| `chunk_manager.mjs` | Chunk lifecycle, streaming window, write-through mutation store, stats |
| `demo.html` / `demo.js` | Canvas demo on the same 1000×620 stage: pan a camera across a 128×128-sector world, watch chunks stream |
| `harness.mjs` | Headless verification (Node): projection parity vs `scene.js`, draw-order parity, streaming/eviction/determinism/mutation assertions over a camera path |
| `README.md` | How to run the demo and the harness |

## 10. Integration path (future, not in this prototype)

1. `world.py`: expose sector metadata through a chunk-windowed view
   keyed to player positions; `visit()` already writes through to the
   persistent store, so the write-through contract (§4) is met by
   construction.
2. `overworld.js`: replace the atlas-hard-coded flat projection with
   the sector window + `projectWithCamera`, letting the map pan
   beyond the authored rectangle; the authored atlas remains the
   spawn region.
3. `scene.py` / `scene.js`: no changes needed for fields; a field
   already renders from a tile dictionary, wherever the tiles came
   from.
