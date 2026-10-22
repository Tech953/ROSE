// World-scale layer: headless verification harness.
//
// Run:  node rose/worldscale/harness.mjs
// (reads the real renderer at rose/static/scene.js, relative to
// this file, so the parity checks run against the shipped code).
//
// Asserts, with observed output:
//   1. projection.mjs is numerically identical to scene.js's project
//   2. the draw-order comparators used here are the ones in scene.js,
//      and chunked assembly reproduces the un-chunked draw order
//   3. a camera crossing the 128x128 demo world streams chunks in
//      and out inside the design's bounds, with the active window
//      always complete
//   4. border jitter does not thrash the window (grace hysteresis)
//   5. an evicted chunk regenerates byte-identical (checksum)
//   6. a mutation survives eviction via the write-through store

import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { project, projectWithCamera, tileComparator, propComparator } from './projection.mjs';
import { ChunkManager, sectorKey } from './chunk_manager.mjs';

let failures = 0;
function check(name, ok, detail = '') {
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${detail ? ` — ${detail}` : ''}`);
  if (!ok) failures++;
}

// ---------- 1. Projection parity against the real scene.js ----------
const here = dirname(fileURLToPath(import.meta.url));
const sceneSrc = readFileSync(join(here, '..', 'static', 'scene.js'), 'utf8');
const match = sceneSrc.match(/const project=\(p,elevation=0\)=>\[[\s\S]*?\];/);
check('scene.js project function located', !!match);
const sceneProject = new Function('width', 'height', 'size', `${match[0]}\nreturn project;`)(1000, 620, 34);

let paritySamples = 0, parityBad = 0;
let rngState = 123456789;
const rand = () => (rngState = (Math.imul(rngState, 1103515245) + 12345) & 0x7fffffff) / 0x7fffffff;
for (let i = 0; i < 1000; i++) {
  const q = Math.floor(rand() * 401) - 200, r = Math.floor(rand() * 401) - 200, e = Math.floor(rand() * 10);
  const a = sceneProject([q, r], e), b = project([q, r], e);
  paritySamples++;
  if (a[0] !== b[0] || a[1] !== b[1]) parityBad++;
}
check('projection parity vs scene.js (1000 samples)', parityBad === 0, `${paritySamples} samples, ${parityBad} mismatches`);

const camZeroBad = [];
for (let i = 0; i < 100; i++) {
  const q = Math.floor(rand() * 257) - 128, r = Math.floor(rand() * 257) - 128, e = Math.floor(rand() * 10);
  const a = project([q, r], e), b = projectWithCamera(q, r, e, 0, 0);
  if (a[0] !== b[0] || a[1] !== b[1]) camZeroBad.push([q, r]);
}
check('projectWithCamera at cam (0,0) is exactly project()', camZeroBad.length === 0);

// ---------- 2. Draw-order parity ----------
check('scene.js tile comparator present in source',
  sceneSrc.includes('a.pos[1]-b.pos[1]||a.pos[0]-b.pos[0]'));
check('scene.js prop comparator present in source',
  sceneSrc.includes('project(a.pos)[1]-project(b.pos)[1]') && sceneSrc.includes('project(a.pos)[0]-project(b.pos)[0]'));

function disk(radius) {
  const out = [];
  for (let q = -radius; q <= radius; q++)
    for (let r = Math.max(-radius, -q - radius); r <= Math.min(radius, -q + radius); r++) out.push([q, r]);
  return out;
}
// A radius-8 field (217 hexes, inside the real 91..271 range),
// centred on a chunk corner so it straddles four chunks.
const mgr0 = new ChunkManager({});
const items = disk(8).map(([dq, dr]) => ({ pos: [8 + dq, 8 + dr] }));
check('sample field size', items.length === 217, `${items.length} hexes (disk radius 8)`);
const chunksSpanned = new Set(items.map(it => mgr0.chunkOf(it.pos[0], it.pos[1]).join(',')));
check('sample field straddles multiple chunks', chunksSpanned.size >= 4, `${chunksSpanned.size} chunks spanned`);

const keyOf = it => it.pos.join(',');
const unchunkedTiles = [...items].sort(tileComparator).map(keyOf).join(' ');
const byChunk = new Map();
for (const it of items) {
  const id = mgr0.chunkOf(it.pos[0], it.pos[1]).join(',');
  if (!byChunk.has(id)) byChunk.set(id, []);
  byChunk.get(id).push(it);
}
const chunkedConcat = [...byChunk.keys()].reverse().flatMap(id => byChunk.get(id)); // worst-case chunk order
const chunkedTiles = [...chunkedConcat].sort(tileComparator).map(keyOf).join(' ');
check('tile draw order: chunked assembly == un-chunked', chunkedTiles === unchunkedTiles);

const propCmpScene = propComparator(p => sceneProject(p, 0));
const propCmpCam = propComparator(p => projectWithCamera(p[0], p[1], 0, 23, -11));
const unchunkedProps = [...items].sort(propCmpScene).map(keyOf).join(' ');
const chunkedProps = [...chunkedConcat].sort(propCmpScene).map(keyOf).join(' ');
const camProps = [...items].sort(propCmpCam).map(keyOf).join(' ');
check('prop draw order: chunked assembly == un-chunked', chunkedProps === unchunkedProps);
check('prop draw order: unchanged under camera translation', camProps === unchunkedProps);

// ---------- 3. Streaming across the demo world ----------
const mgr = new ChunkManager({});
check('demo world is larger than the 37x25 atlas',
  mgr.worldSectors === 16384 && mgr.worldSectors > 925 && mgr.worldChunks === 256,
  `${mgr.worldQ}x${mgr.worldR} = ${mgr.worldSectors} sectors in ${mgr.worldChunks} chunks (atlas: 925)`);

let activeComplete = true, residentBoundOk = true;
const path = [];
for (let s = -60; s <= 60; s += 4) path.push([s, s]);
path.push([63, 63]);
for (const [cq, cr] of path) {
  const { cameraChunk } = mgr.update(cq, cr);
  for (let cx = cameraChunk[0] - 1; cx <= cameraChunk[0] + 1; cx++)
    for (let cy = cameraChunk[1] - 1; cy <= cameraChunk[1] + 1; cy++) {
      if (!mgr.chunkInWorld(cx, cy)) continue;
      const chunk = mgr.chunks.get(`${cx},${cy}`);
      if (!chunk || chunk.state !== 'ACTIVE') activeComplete = false;
    }
  if (mgr.chunks.size > 49) residentBoundOk = false; // 25 window + one aging ring of 24
}
check('active window complete at every path step', activeComplete);
check('resident chunks stayed inside bound (<=49 incl. grace ring)', residentBoundOk,
  `observed max resident: ${mgr.stats.maxResident} chunks / ${mgr.stats.maxResidentSectors} sector records`);
check('chunks loaded and evicted along the path', mgr.stats.loads > 100 && mgr.stats.evictions > 50,
  `loads=${mgr.stats.loads}, evictions=${mgr.stats.evictions}`);

// ---------- 4. Border jitter does not thrash ----------
const jm = new ChunkManager({});
jm.update(0, 0); jm.update(0, 0); jm.update(0, 0);
jm.update(8.1, 0); // one genuine crossing: the window's leading edge loads once
const loadsBefore = jm.stats.loads, evictBefore = jm.stats.evictions;
for (let i = 0; i < 12; i++) jm.update(i % 2 === 0 ? 7.9 : 8.1, 0);
check('jitter across a chunk border: no repeated loads, no evictions',
  jm.stats.loads === loadsBefore && jm.stats.evictions === evictBefore,
  `after first crossing loads=${loadsBefore}; 12 more crossings -> loads ${jm.stats.loads}, evictions ${jm.stats.evictions}`);

// ---------- 5+6. Determinism + mutation persistence ----------
const dm = new ChunkManager({});
dm.update(-60, -60); dm.update(-60, -60);
const homeChunk = dm.chunks.get('-8,-8');
check('home chunk resident at start', !!homeChunk);
const checksumBefore = ChunkManager.checksum(homeChunk);
dm.mutate(-57, -57, 'surveyed-by-harness');
dm.update(60, 60); dm.update(60, 60); dm.update(60, 60);
check('home chunk evicted after travelling away', !dm.chunks.has('-8,-8'),
  `evictions so far: ${dm.stats.evictions}`);
dm.update(-60, -60); dm.update(-60, -60);
const regen = dm.chunks.get('-8,-8');
check('home chunk regenerated on return', !!regen);
check('regenerated chunk is byte-identical (checksum)',
  !!regen && ChunkManager.checksum(regen) === checksumBefore,
  `checksum ${checksumBefore}`);
const sector = dm.sectorAt(-57, -57);
check('mutation survived eviction via write-through store',
  !!sector && sector.changes.includes('surveyed-by-harness'),
  sector ? `sector -57,-57 changes: ${JSON.stringify(sector.changes)}` : 'sector missing');
check('persisted store holds the change', (dm.persisted.get(sectorKey(-57, -57)) || []).includes('surveyed-by-harness'));

console.log('---');
console.log(`world: ${mgr.worldQ}x${mgr.worldR} sectors (${mgr.worldSectors}) in ${mgr.worldChunks} chunks of ${mgr.chunkSize}x${mgr.chunkSize}`);
console.log(`camera path: ${path.length} updates, loads=${mgr.stats.loads}, evictions=${mgr.stats.evictions}, max resident=${mgr.stats.maxResident} chunks / ${mgr.stats.maxResidentSectors} sector records`);
console.log(failures === 0 ? 'ALL CHECKS PASSED' : `${failures} CHECK(S) FAILED`);
process.exit(failures === 0 ? 0 : 1);
