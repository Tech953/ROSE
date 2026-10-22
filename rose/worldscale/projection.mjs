// World-scale layer: projection.
//
// These functions mirror rose/static/scene.js exactly. The shipped
// renderer (an IIFE bound to the DOM) cannot be imported headlessly,
// so the constants are copied verbatim and harness.mjs extracts the
// real `project` from scene.js and asserts numeric parity — the
// mirror cannot silently drift from the renderer.
//
// scene.js today:
//   const canvas=..., width=1000, height=620;
//   let size=34;
//   const project=(p,elevation=0)=>[width/2+Math.sqrt(3)*size*(p[0]+p[1]/2),
//                                   height*.55+size*1.5*p[1]*.52-elevation*2];

export const CANVAS_WIDTH = 1000;
export const CANVAS_HEIGHT = 620;
export const HEX_SIZE = 34;
export const Y_COMPRESSION = 0.52;   // dimetric squash applied to r in scene.js
export const ELEVATION_LIFT = 2;     // px per elevation unit in scene.js

// Identical expression order to scene.js so results are bit-identical.
export function project(p, elevation = 0, size = HEX_SIZE) {
  return [
    CANVAS_WIDTH / 2 + Math.sqrt(3) * size * (p[0] + p[1] / 2),
    CANVAS_HEIGHT * .55 + size * 1.5 * p[1] * Y_COMPRESSION - elevation * ELEVATION_LIFT,
  ];
}

// A camera is a pure translation of the renderer's anchor: at
// cam = (0, 0) this is exactly scene.js's project(). Relative
// geometry (and therefore the Y-sort draw order) is unchanged.
export function projectWithCamera(q, r, elevation = 0, camQ = 0, camR = 0, size = HEX_SIZE) {
  return [
    CANVAS_WIDTH / 2 + Math.sqrt(3) * size * ((q - camQ) + (r - camR) / 2),
    CANVAS_HEIGHT * .55 + size * 1.5 * (r - camR) * Y_COMPRESSION - elevation * ELEVATION_LIFT,
  ];
}

// Draw-order comparators, copied from scene.js's draw():
//   tiles: Object.values(f.tiles).sort((a,b)=>a.pos[1]-b.pos[1]||a.pos[0]-b.pos[0])
//   props: props.sort((a,b)=>project(a.pos)[1]-project(b.pos)[1]
//                          ||project(a.pos)[0]-project(b.pos)[0])
// Items are {pos:[q,r]} here, the same shape scene.js sorts.
export function tileComparator(a, b) {
  return a.pos[1] - b.pos[1] || a.pos[0] - b.pos[0];
}

export function propComparator(projectFn) {
  return (a, b) => projectFn(a.pos)[1] - projectFn(b.pos)[1] || projectFn(a.pos)[0] - projectFn(b.pos)[0];
}
