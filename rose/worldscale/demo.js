'use strict';
// World-scale layer demo: stream terrain chunks under scene.js's
// own projection. Rendering only — no game state, art, or saves.
import { ChunkManager } from './chunk_manager.mjs';
import { projectWithCamera, tileComparator, HEX_SIZE, Y_COMPRESSION } from './projection.mjs';

const canvas = document.getElementById('field-canvas');
const ctx = canvas.getContext('2d');
const hud = document.getElementById('hud');
const mgr = new ChunkManager({});
const COLORS = { grassland: '#3b4b3d', woodland: '#2e4634', wetland: '#33505a', highland: '#61553d', barren: '#584859' };

let camQ = 0, camR = 0;
const keys = new Set();
addEventListener('keydown', e => { keys.add(e.key.toLowerCase()); });
addEventListener('keyup', e => { keys.delete(e.key.toLowerCase()); });

function hexPath(cx, cy) {
  // Center already carries the elevation lift from the projection;
  // corners squash by the same 0.52 dimetric compression.
  ctx.beginPath();
  for (let k = 0; k < 6; k++) {
    const ang = Math.PI / 180 * (60 * k - 30);
    const x = cx + HEX_SIZE * Math.cos(ang);
    const y = cy + HEX_SIZE * Math.sin(ang) * Y_COMPRESSION;
    if (k === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  }
  ctx.closePath();
}

function frame() {
  const speed = 0.35;
  if (keys.has('a') || keys.has('arrowleft')) camQ -= speed;
  if (keys.has('d') || keys.has('arrowright')) camQ += speed;
  if (keys.has('w') || keys.has('arrowup')) camR -= speed;
  if (keys.has('s') || keys.has('arrowdown')) camR += speed;
  camQ = Math.max(mgr.minQ, Math.min(mgr.minQ + mgr.worldQ - 1, camQ));
  camR = Math.max(mgr.minR, Math.min(mgr.minR + mgr.worldR - 1, camR));

  const { cameraChunk } = mgr.update(camQ, camR);

  // Gather draw items from resident chunks and paint in the
  // renderer's own tile order: sort by (r, q), as scene.js does.
  const items = [];
  for (const chunk of mgr.residentChunks())
    for (const s of chunk.sectors.values())
      items.push({ pos: [s.q, s.r], sector: s, active: chunk.state === 'ACTIVE' });
  items.sort(tileComparator);

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  for (const it of items) {
    const s = it.sector;
    const [x, y] = projectWithCamera(s.q, s.r, s.elevation, camQ, camR);
    if (x < -80 || x > canvas.width + 80 || y < -80 || y > canvas.height + 80) continue;
    const shade = 0.75 + s.elevation * 0.05;
    ctx.fillStyle = COLORS[s.terrain];
    ctx.globalAlpha = (it.active ? 1 : 0.45) * shade;
    hexPath(x, y);
    ctx.fill();
    ctx.globalAlpha = 0.25;
    ctx.strokeStyle = '#000';
    ctx.stroke();
    ctx.globalAlpha = 1;
  }
  // Camera marker at the anchor hex.
  const [mx, my] = projectWithCamera(Math.floor(camQ), Math.floor(camR), 0, camQ, camR);
  ctx.fillStyle = '#ffcc66';
  ctx.beginPath(); ctx.arc(mx, my, 4, 0, Math.PI * 2); ctx.fill();

  hud.textContent =
    `world ${mgr.worldQ}x${mgr.worldR} sectors (${mgr.worldSectors}) · camera sector [${Math.floor(camQ)},${Math.floor(camR)}] chunk [${cameraChunk}] · ` +
    `resident ${mgr.chunks.size} chunks (active ${mgr.activeChunks().length}) · loads ${mgr.stats.loads} · evictions ${mgr.stats.evictions}`;
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
