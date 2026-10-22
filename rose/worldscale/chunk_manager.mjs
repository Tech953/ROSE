// World-scale layer: chunk manager (prototype).
//
// A residency window over a seeded sector world, per
// docs/WORLD_SCALE_LAYER.md. Sector metadata is a pure function of
// (seed, q, r) — the same discipline as rose/world.py's
// rng(seed, 'terrain', x, y) (sha256 of "seed|terrain|x|y" there;
// a small FNV-1a + mulberry32 here so the module also runs in a
// browser with no imports). Regenerating an evicted chunk therefore
// reproduces identical metadata, which is what makes eviction safe.
//
// Mutations never live only in a chunk: they write through to
// `persisted` (standing in for the save's visited-cell store, cf.
// world.py's w['cells'][key]['changes']) at the moment they happen,
// and are re-applied on regeneration.

export const TERRAIN_CLASSES = ['grassland', 'woodland', 'wetland', 'highland', 'barren'];

function hashString(str) {
  // FNV-1a 32-bit.
  let h = 0x811c9dc5;
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  return h >>> 0;
}

function mulberry32(seedInt) {
  let a = seedInt >>> 0;
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// Pure function of (seed, q, r): demo terrain only (five classes,
// elevation 1..9, moisture 25..70 — the ranges world.py rolls).
export function sectorFor(seed, q, r) {
  const rand = mulberry32(hashString(`${seed}|terrain|${q}|${r}`));
  const roll = rand();
  const terrain = TERRAIN_CLASSES[Math.min(TERRAIN_CLASSES.length - 1, Math.floor(roll * TERRAIN_CLASSES.length))];
  const elevation = 1 + Math.floor(rand() * 9);
  const moisture = 25 + Math.floor(rand() * 46);
  return { q, r, terrain, elevation, moisture, changes: [] };
}

export function chunkKey(cx, cy) { return `${cx},${cy}`; }
export function sectorKey(q, r) { return `${q},${r}`; }

export class ChunkManager {
  constructor({
    seed = 'rose-worldscale-demo',
    worldQ = 128,          // demo world: 128 x 128 sectors
    worldR = 128,
    chunkSize = 8,         // 8x8 sectors per chunk
    activeRadius = 1,      // chunks (Chebyshev) -> ACTIVE
    prefetchRadius = 2,    // chunks (Chebyshev) -> metadata resident
    evictGrace = 2,        // consecutive far updates before eviction
  } = {}) {
    this.seed = seed;
    this.worldQ = worldQ;
    this.worldR = worldR;
    this.chunkSize = chunkSize;
    this.activeRadius = activeRadius;
    this.prefetchRadius = prefetchRadius;
    this.evictGrace = evictGrace;
    // World sector bounds: q in [-worldQ/2, worldQ/2), r likewise.
    this.minQ = -Math.floor(worldQ / 2);
    this.minR = -Math.floor(worldR / 2);
    this.chunks = new Map();      // chunkKey -> chunk record
    this.persisted = new Map();   // sectorKey -> changes[] (the "save")
    this.stats = { loads: 0, evictions: 0, promotions: 0, maxResident: 0, maxResidentSectors: 0 };
  }

  get worldSectors() { return this.worldQ * this.worldR; }
  get worldChunks() { return (this.worldQ / this.chunkSize) * (this.worldR / this.chunkSize); }

  inWorld(q, r) {
    return q >= this.minQ && q < this.minQ + this.worldQ && r >= this.minR && r < this.minR + this.worldR;
  }

  chunkOf(q, r) {
    return [Math.floor(q / this.chunkSize), Math.floor(r / this.chunkSize)];
  }

  chunkInWorld(cx, cy) {
    const q0 = cx * this.chunkSize, r0 = cy * this.chunkSize;
    return this.inWorld(q0, r0) || this.inWorld(q0 + this.chunkSize - 1, r0 + this.chunkSize - 1);
  }

  generateChunk(cx, cy) {
    const sectors = new Map();
    for (let dq = 0; dq < this.chunkSize; dq++) {
      for (let dr = 0; dr < this.chunkSize; dr++) {
        const q = cx * this.chunkSize + dq, r = cy * this.chunkSize + dr;
        if (!this.inWorld(q, r)) continue;
        const sector = sectorFor(this.seed, q, r);
        const saved = this.persisted.get(sectorKey(q, r));
        if (saved) sector.changes = [...saved];
        sectors.set(sectorKey(q, r), sector);
      }
    }
    return { cx, cy, state: 'PREFETCH', sectors, farUpdates: 0 };
  }

  // Stable checksum of a chunk's seeded content (changes excluded):
  // identical before eviction and after regeneration.
  static checksum(chunk) {
    let h = 0x811c9dc5;
    const parts = [...chunk.sectors.values()]
      .sort((a, b) => a.q - b.q || a.r - b.r)
      .map(s => `${s.q},${s.r},${s.terrain},${s.elevation},${s.moisture}`);
    const str = parts.join('|');
    for (let i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 0x01000193); }
    return (h >>> 0).toString(16);
  }

  // Move the camera (sector-space floats). Loads, promotes, demotes
  // and evicts per the design's radii + grace hysteresis.
  update(camQ, camR) {
    const [ccx, ccy] = this.chunkOf(Math.floor(camQ), Math.floor(camR));
    const pr = this.prefetchRadius;
    // Load + promote/demote everything inside the prefetch window.
    for (let cx = ccx - pr; cx <= ccx + pr; cx++) {
      for (let cy = ccy - pr; cy <= ccy + pr; cy++) {
        if (!this.chunkInWorld(cx, cy)) continue;
        const dist = Math.max(Math.abs(cx - ccx), Math.abs(cy - ccy));
        const id = chunkKey(cx, cy);
        let chunk = this.chunks.get(id);
        if (!chunk) {
          chunk = this.generateChunk(cx, cy);
          this.chunks.set(id, chunk);
          this.stats.loads++;
        }
        chunk.farUpdates = 0;
        const want = dist <= this.activeRadius ? 'ACTIVE' : 'PREFETCH';
        if (want === 'ACTIVE' && chunk.state !== 'ACTIVE') this.stats.promotions++;
        chunk.state = want;
      }
    }
    // Eviction pass: resident chunks outside the window age out.
    for (const [id, chunk] of this.chunks) {
      const dist = Math.max(Math.abs(chunk.cx - ccx), Math.abs(chunk.cy - ccy));
      if (dist > this.prefetchRadius) {
        chunk.farUpdates++;
        if (chunk.farUpdates >= this.evictGrace) {
          this.chunks.delete(id);
          this.stats.evictions++;
        }
      }
    }
    let residentSectors = 0;
    for (const chunk of this.chunks.values()) residentSectors += chunk.sectors.size;
    this.stats.maxResident = Math.max(this.stats.maxResident, this.chunks.size);
    this.stats.maxResidentSectors = Math.max(this.stats.maxResidentSectors, residentSectors);
    return { cameraChunk: [ccx, ccy], resident: this.chunks.size, residentSectors };
  }

  sectorAt(q, r) {
    const [cx, cy] = this.chunkOf(q, r);
    const chunk = this.chunks.get(chunkKey(cx, cy));
    return chunk ? chunk.sectors.get(sectorKey(q, r)) || null : null;
  }

  // Write-through mutation: applied to the resident sector if any,
  // and always recorded in the persisted store so it survives
  // eviction (mirrors world.py's per-cell 'changes' list).
  mutate(q, r, change) {
    const key = sectorKey(q, r);
    const saved = this.persisted.get(key) || [];
    saved.push(change);
    this.persisted.set(key, saved);
    const sector = this.sectorAt(q, r);
    if (sector) sector.changes = [...saved];
    return saved.length;
  }

  residentChunks() { return [...this.chunks.values()]; }
  activeChunks() { return this.residentChunks().filter(c => c.state === 'ACTIVE'); }
}
