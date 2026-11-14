// Ketta Orrow, walk 001: Asker road.
//
// A hillside seen across 500 m of lake, and lime lamps carried down it.
// In her world light is slow and each colour has its own speed (red 240 m/s,
// violet 6 m/s), so what the bench sees of a lamp at any instant is every
// place the lamp has been in the last minute or two, one colour per place.
//
// One file, no dependencies. Runs in a browser (piece/index.html) and under
// node (make.mjs writes the stills from the same code).
(function (G) {
'use strict';

// ------------------------------------------------------------------ noise
function h2(ix, iy, s) {
  let n = Math.imul(ix, 374761393) ^ Math.imul(iy, 668265263) ^ Math.imul(s, 1274126177);
  n = Math.imul(n ^ (n >>> 13), 1274126177); n ^= n >>> 16;
  return (n >>> 0) / 4294967296;
}
function vn(x, y, s) {
  const ix = Math.floor(x), iy = Math.floor(y);
  let fx = x - ix, fy = y - iy;
  fx = fx * fx * (3 - 2 * fx); fy = fy * fy * (3 - 2 * fy);
  const a = h2(ix, iy, s), b = h2(ix + 1, iy, s), c = h2(ix, iy + 1, s), d = h2(ix + 1, iy + 1, s);
  return a + (b - a) * fx + (c - a) * fy + (a - b - c + d) * fx * fy;
}
function fbm(x, y, o, s) {
  let a = 0.5, f = 1, sum = 0, n = 0;
  for (let i = 0; i < o; i++) { sum += a * vn(x * f, y * f, s + i * 17); n += a; a *= 0.5; f *= 2.03; }
  return sum / n;
}
const n1 = (t, s) => vn(t, 0.37, s) * 2 - 1;
const clamp = (x, a, b) => x < a ? a : x > b ? b : x;
const sst = (a, b, x) => { const t = clamp((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); };

// ------------------------------------------------------------------ the world's light
const C_RED = 240, C_VIOLET = 6;          // m/s
const SLOW0 = 1 / C_RED, DSLOW = 1 / C_VIOLET - 1 / C_RED;
const DISP = 1.45;                         // slowness = SLOW0 + DSLOW * s^DISP, s in 0..1 red..violet
// colour of each place in the spectrum, balanced so that the whole of it is white
const SPEC = (() => {
  const key = [
    [0.00, 0.80, 0.00, 0.00], [0.10, 1.00, 0.05, 0.00], [0.24, 1.00, 0.42, 0.00],
    [0.36, 0.92, 0.86, 0.04], [0.50, 0.12, 0.92, 0.18], [0.62, 0.00, 0.74, 0.86],
    [0.75, 0.08, 0.28, 1.00], [0.88, 0.40, 0.08, 1.00], [1.00, 0.26, 0.00, 0.55]];
  const N = 512, t = new Float32Array(N * 3), sum = [0, 0, 0];
  for (let i = 0; i < N; i++) {
    const s = (i + 0.5) / N; let k = 0;
    while (k < key.length - 2 && s > key[k + 1][0]) k++;
    const a = key[k], b = key[k + 1], w = sst(a[0], b[0], s);
    for (let c = 0; c < 3; c++) { t[i * 3 + c] = a[c + 1] + (b[c + 1] - a[c + 1]) * w; sum[c] += t[i * 3 + c] / N; }
  }
  for (let i = 0; i < N; i++) for (let c = 0; c < 3; c++) t[i * 3 + c] /= sum[c];
  return { t, N };
})();

// ------------------------------------------------------------------ the Asker side: ways
function chaikin(p, n) {
  for (let k = 0; k < n; k++) {
    const q = [p[0]];
    for (let i = 0; i < p.length - 1; i++) {
      const a = p[i], b = p[i + 1];
      q.push([a[0] * .75 + b[0] * .25, a[1] * .75 + b[1] * .25], [a[0] * .25 + b[0] * .75, a[1] * .25 + b[1] * .75]);
    }
    q.push(p[p.length - 1]); p = q;
  }
  return p;
}
function resample(p, step) {
  const out = [p[0].slice()]; let need = step;
  for (let i = 0; i < p.length - 1; i++) {
    let ax = p[i][0], ay = p[i][1]; const bx = p[i + 1][0], by = p[i + 1][1];
    let d = Math.hypot(bx - ax, by - ay);
    while (d >= need) {
      const t = need / d; ax += (bx - ax) * t; ay += (by - ay) * t; out.push([ax, ay]);
      d -= need; need = step;
    }
    need -= d;
  }
  return out;
}
// a way people walk: control points, a little wander, corners rounded
function way(ctrl, seed, wander) {
  const p = [];
  for (let i = 0; i < ctrl.length - 1; i++) {
    const a = ctrl[i], b = ctrl[i + 1], L = Math.hypot(b[0] - a[0], b[1] - a[1]);
    const m = Math.max(1, Math.round(L / 45));
    for (let j = 0; j < m; j++) {
      const t = j / m, x = a[0] + (b[0] - a[0]) * t, y = a[1] + (b[1] - a[1]) * t;
      const w = (j === 0 ? 0 : wander) * Math.sin(Math.PI * t);
      p.push([x - (b[1] - a[1]) / L * w * n1(i * 3.1 + j * 1.7, seed), y + (b[0] - a[0]) / L * w * n1(i * 3.1 + j * 1.7, seed)]);
    }
  }
  p.push(ctrl[ctrl.length - 1]);
  return resample(chaikin(p, 3), 1);
}
const beckU = v => 40 + 0.12 * v + 6 * Math.sin(v / 37);

const APEX = [[-215, 700], [-200, 646], [150, 440], [-150, 350], [140, 262], [-120, 180], [100, 105], [-70, 42], [-42, 6], [14, 3]];
function roadCtrl() {
  // tighten each hairpin with a point a little way down both legs
  const c = [APEX[0], APEX[1]];
  for (let i = 2; i < APEX.length; i++) {
    const a = APEX[i - 1], b = APEX[i], L = Math.hypot(b[0] - a[0], b[1] - a[1]);
    if (L > 80) { c.push([a[0] + (b[0] - a[0]) * 16 / L, a[1] + (b[1] - a[1]) * 16 / L]); c.push([b[0] - (b[0] - a[0]) * 16 / L, b[1] - (b[1] - a[1]) * 16 / L]); }
    c.push(b);
  }
  return c;
}
const ROAD = way(roadCtrl(), 5, 9);
function nearest(path, u, v) { let bi = 0, bd = 1e9; for (let i = 0; i < path.length; i++) { const d = (path[i][0] - u) ** 2 + (path[i][1] - v) ** 2; if (d < bd) { bd = d; bi = i; } } return bi; }

// the other ways she is allowed: trods that are already on the hill
const beckPts = []; for (let v = 4; v <= 232; v += 30) beckPts.push([beckU(v) - 7, v]);
const iBeck4 = nearest(ROAD.slice(940), beckU(236) - 7, 236) + 940;       // where the beck trod meets the road's fourth leg
beckPts.push(ROAD[iBeck4]);
const TROD = {
  ridge: way([[-215, 700], [-204, 652], [-160, 640], [-90, 634], [0, 636], [80, 633], [150, 637]], 11, 4),
  farm: way([ROAD[nearest(ROAD, -150, 350)], [-172, 326], [-168, 296], [-152, 272], [-127, 270]], 12, 2),
  beck: way(beckPts, 13, 3),
  shore: way([ROAD[nearest(ROAD, 100, 105)], [108, 80], [103, 44], [92, 16]], 14, 3),
};
const WALLS = [
  [[-205, 25], [-215, 180], [-225, 330], [-240, 440]],
  [[-118, 24], [-104, 120], [-122, 205], [-96, 300], [-110, 432]],
  [[-28, 22], [-20, 110], [-34, 236], [-12, 330], [-22, 436]],
  [[88, 24], [110, 118], [124, 250], [146, 300], [138, 438]],
  [[190, 150], [205, 300], [215, 440]],
  [[-250, 27], [-100, 22], [0, 24], [120, 22], [250, 28]],
  [[-245, 240], [-120, 232], [-30, 238], [70, 246], [124, 250], [230, 243]],
  [[-260, 441], [-110, 432], [-22, 436], [60, 446], [138, 438], [260, 447]],
  [[-156, 262], [-100, 264], [-98, 298], [-156, 296], [-156, 262]],
  (() => { const r = []; for (let a = 0.5; a < 6.4; a += 0.4) r.push([36 + 9 * Math.cos(a), 522 + 9 * Math.sin(a)]); return r; })(),
].map((c, i) => resample(way(c, 40 + i, 2.2), 2));
const BUILD = [   // u, v, width (u), depth (v), eaves, roof rise
  [-130, 278, 16, 7, 4.6, 2.6], [-110, 287, 9, 6, 3.2, 1.8], [168, 232, 12, 7, 4.2, 2.4],
  [30, 9, 10, 6, 3.6, 2.2], [92, 8, 8, 5, 2.8, 1.8]];

// segments binned on a grid so the hill can ask "how far is the nearest wall"
const CELL = 12, GU0 = -320, GV0 = -40, GNX = 54, GNY = 70;
const grid = Array.from({ length: GNX * GNY }, () => []);
const SEG = [];
function addWay(p, type) {
  for (let i = 0; i < p.length - 1; i++) {
    const a = p[i], b = p[i + 1], cx = Math.floor(((a[0] + b[0]) / 2 - GU0) / CELL), cy = Math.floor(((a[1] + b[1]) / 2 - GV0) / CELL);
    if (cx < 0 || cy < 0 || cx >= GNX || cy >= GNY) continue;
    grid[cy * GNX + cx].push(SEG.length / 5); SEG.push(a[0], a[1], b[0], b[1], type);
  }
}
addWay(resample(ROAD, 2), 0);
WALLS.forEach(w => addWay(w, 1));
Object.values(TROD).forEach(t => addWay(resample(t, 2), 2));
{ const b = []; for (let v = 0; v <= 610; v += 2) b.push([beckU(v), v]); addWay(b, 3); }
const D = new Float32Array(4);   // nearest road, wall, trod, beck
function ask(u, v) {
  D[0] = D[1] = D[2] = D[3] = 99;
  const cx = Math.floor((u - GU0) / CELL), cy = Math.floor((v - GV0) / CELL);
  for (let j = cy - 1; j <= cy + 1; j++) for (let i = cx - 1; i <= cx + 1; i++) {
    if (i < 0 || j < 0 || i >= GNX || j >= GNY) continue;
    const g = grid[j * GNX + i];
    for (let k = 0; k < g.length; k++) {
      const o = g[k] * 5, ax = SEG[o], ay = SEG[o + 1], bx = SEG[o + 2], by = SEG[o + 3];
      const dx = bx - ax, dy = by - ay; let t = ((u - ax) * dx + (v - ay) * dy) / (dx * dx + dy * dy + 1e-9);
      t = t < 0 ? 0 : t > 1 ? 1 : t;
      const d = Math.hypot(u - ax - dx * t, v - ay - dy * t), ty = SEG[o + 4];
      if (d < D[ty]) D[ty] = d;
    }
  }
}

// ------------------------------------------------------------------ the Asker side: ground
const shoreV = u => 9 * (fbm(u / 70, 3.3, 3, 7) - 0.5);
function bare(u, v0) {
  const v = v0 - shoreV(u);
  if (v <= 0) return 0;
  const t = v / 640;
  const prof = t < 1 ? 0.33 * t + 0.67 * t * t * (3 - 2 * t) : 1 - 2.2 * (t - 1) * (t - 1) - 0.4 * (t - 1);
  const crest = 124 + 30 * Math.exp(-(((u - 150) / 150) ** 2)) - 16 * sst(-40, -220, u) + 34 * sst(-235, -330, u);
  const tt = Math.min(t, 1.2);
  let z = crest * prof;
  z += 13 * Math.sin(u / 70 + 1.3 + v / 260) * tt * (1.25 - tt);
  z -= (4 + 7 * tt) * Math.exp(-(((u - beckU(v0)) / (12 + 18 * tt)) ** 2)) * sst(0, 60, v) * sst(640, 560, v);
  z += 17 * (fbm(u / 95, v / 95, 4, 21) - 0.5) * Math.min(1, v / 90);
  z += 0.7 * (fbm(u / 8, v / 8, 2, 33) - 0.5);
  return Math.max(0.12, z + 0.2);
}
let F_kind = 0;   // what the last ground() landed on: 0 grass 1 wall 3 house
// gorse and thorn scrub: low, dark, along the beck and in the corners nobody mows
function scrub(u, v) {
  const ub = beckU(v);
  return fbm(u / 30, v / 30, 4, 51)
    + 0.20 * Math.exp(-(((u - ub - 16) / 14) ** 2)) * sst(20, 60, v) * sst(450, 400, v)
    + 0.20 * Math.exp(-((u - 190) ** 2 + (v - 190) ** 2) / 1200)
    + 0.20 * Math.exp(-((u + 195) ** 2 + (v - 80) ** 2) / 1800)
    + 0.12 * sst(3, 0.8, D[1])
    - 0.5 * sst(12, 6, D[0]) - 0.4 * sst(6, 3, D[2]);
}
function ground(u, v) {
  const z = bare(u, v); F_kind = 0;
  if (z === 0) return 0;
  for (let i = 0; i < BUILD.length; i++) {
    const b = BUILD[i], du = Math.abs(u - b[0]), dv = Math.abs(v - b[1]);
    if (du < b[2] / 2 && dv < b[3] / 2) { F_kind = 3; return bare(b[0], b[1] - b[3] / 2) + b[4] + b[5] * (1 - dv / (b[3] / 2)); }
  }
  ask(u, v);
  if (D[1] < 0.38 && D[0] > 3 && D[2] > 1.5) { F_kind = 1; return z + 1.15; }
  return z;
}

// ------------------------------------------------------------------ the bench
const CAM_V = -500, CAM_Z = 4;

function build(W, H, opt) {
  opt = opt || {};
  const f = 3.55 * H, hy = 0.585 * H, cx = W / 2, sc = H / 1200;
  const N = W * H;
  const alb = new Float32Array(N * 3), shade = new Float32Array(N), haze = new Float32Array(N);
  const dvm = new Float32Array(N).fill(1e9), kind = new Uint8Array(N);   // 0 sky 1 land 2 water
  const L = [-0.72, 0.34, 0.5]; { const n = Math.hypot(...L); L[0] /= n; L[1] /= n; L[2] /= n; }

  // march each column out across the water and up the hill, front to back
  for (let x = 0; x < W; x++) {
    const du = (x + 0.5 - cx) / f;
    let ymin = H, started = false, dv = 486, zPrev = 0, dvPrev = dv;
    while (dv < 1260) {
      const step = (0.42 + (dv - 486) * 0.0011) / Math.max(sc, 0.5);
      dv += step;
      const u = du * dv, v = dv + CAM_V;
      const z = ground(u, v), fk = F_kind;
      if (z === 0) { continue; }
      const sy = hy - f * (z - CAM_Z) / dv;
      if (!started) { started = true; ymin = Math.min(H, Math.ceil(sy)); for (let y = ymin; y < H; y++) kind[y * W + x] = 2; zPrev = z; dvPrev = dv; }
      if (sy < ymin) {
        const y0 = Math.max(0, Math.ceil(sy)), span = ymin - y0;
        // what is here
        let r, g, b, sh;
        const zb = bare(u, v), e = 1.6;
        const nx = -(bare(u + e, v) - zb) / e, ny = -(bare(u, v + e) - zb) / e, nl = Math.hypot(nx, ny, 1);
        sh = 0.22 * (0.45 + 0.55 / nl) + 2.6 * Math.pow(Math.max(0, (nx * L[0] + ny * L[1] + L[2]) / nl), 2.2);
        const t = (v - shoreV(u)) / 640, p1 = fbm(u / 14, v / 14, 3, 71), p2 = fbm(u / 3, v / 1.5, 2, 73);
        if (fk === 3) {
          if (span > 2.2 * sc) { r = 0.5; g = 0.49; b = 0.45; sh = 0.5; } else { r = 0.2; g = 0.2; b = 0.25; sh *= 1.1; }
        } else if (fk === 1) { r = 0.56 + 0.1 * p2; g = 0.54 + 0.1 * p2; b = 0.5 + 0.1 * p2; sh = (0.3 + 0.45 * sh) * (0.75 + 0.5 * p1); }
                else {
          const fell = sst(0.64, 0.70, t + 0.05 * (p1 - 0.5));
          r = 0.27 + 0.13 * p1; g = 0.41 + 0.07 * p1; b = 0.15 + 0.04 * p1;
          const br = fell * sst(0.35, 0.6, fbm(u / 40, v / 40, 3, 81));
          r += (0.40 - r) * fell * 0.5 + (0.34 - r) * br; g += (0.36 - g) * fell * 0.5 + (0.22 - g) * br; b += (0.2 - b) * fell * 0.5 + (0.14 - b) * br;
          const scree = sst(0.55, 0.75, fbm(u / 22, v / 22, 3, 91)) * sst(0.8, 0.95, t);
          r += (0.5 - r) * scree; g += (0.5 - g) * scree; b += (0.5 - b) * scree;
          const sm = 0.75 * sst(0.62, 0.76, scrub(u, v) + 0.12 * (p2 - 0.5)) * (1 - fell);
          r += (0.13 - r) * sm; g += (0.19 - g) * sm; b += (0.09 - b) * sm;
          const rock = sst(0.62, 0.7, fbm(u / 11, v / 5, 3, 93)) * sst(0.3, 0.6, t) * (1 - sm);
          r += (0.46 - r) * rock * 0.7; g += (0.45 - g) * rock * 0.7; b += (0.43 - b) * rock * 0.7;
          const k = (0.85 + 0.3 * p2) * (0.72 + 0.56 * fbm(u / 75, v / 75, 2, 95)) * (1 - 0.35 * sm * vn(u / 1.2, v / 1.2, 63)); r *= k; g *= k; b *= k;
          if (D[0] < 1.6) { const w = sst(1.6, 1.0, D[0]); r += (0.74 - r) * w; g += (0.68 - g) * w; b += (0.54 - b) * w; }
          else if (D[2] < 0.6) { r += (0.6 - r) * 0.55; g += (0.56 - g) * 0.55; b += (0.42 - b) * 0.55; }
          if (D[3] < 0.9) { const w = sst(0.9, 0.3, D[3]) * sst(0.3, 0.6, vn(v / 9, 0.5, 99)); r += (0.10 - r) * w; g += (0.13 - g) * w; b += (0.2 - b) * w; sh += 0.5 * w * vn(u / 1.5, v / 1.5, 97); }
        }
        const hz = 1 - Math.exp(-(dv - 500) / 2400) + 0.5 * Math.exp(-z / 3.2);
        for (let y = y0; y < ymin; y++) {
          const i = y * W + x, down = span > 2 ? (y - y0) / span : 0;
          const s2 = (fk === 3 || fk === 1) ? sh * (1 - 0.5 * down) : sh;
          alb[i * 3] = r; alb[i * 3 + 1] = g; alb[i * 3 + 2] = b; shade[i] = s2; haze[i] = Math.min(0.9, hz); dvm[i] = dv; kind[i] = 1;
        }
        ymin = y0;
      }
    }
    if (!started) for (let y = Math.ceil(hy + f * CAM_Z / 500); y < H; y++) kind[y * W + x] = 2;
  }

  // sky and what the hill is lit by when no lamp is near
  function backdrop(day) {
    const back = new Float32Array(N * 3);
    const amb = day ? [0.36, 0.36, 0.33] : [0.026, 0.023, 0.085];
    const hzc = day ? [0.36, 0.40, 0.46] : [0.016, 0.012, 0.040];
    const sky = (x, y, o) => {
      const t = clamp(y / (0.34 * H), 0, 1), lx = 1 - x / W;
      const far = hy - H * (0.335 + 0.05 * fbm(x / W * 5, 1.7, 4, 101) + 0.03 * Math.sin(x / W * 2.2 + 0.4));
      const cl = fbm(x / (190 * sc), y / (22 * sc), 3, 111);
      let k = Math.pow(t, 1.7) * (0.55 + 0.7 * lx * lx) * (0.82 + 0.36 * cl);
      if (day) { o[0] = 0.26 + 0.3 * k; o[1] = 0.34 + 0.3 * k; o[2] = 0.50 + 0.26 * k; }
      else { o[0] = 0.004 + 0.050 * k; o[1] = 0.003 + 0.032 * k; o[2] = 0.014 + 0.125 * k; }
      if (y > far) { const m = day ? 0.8 : 0.5; o[0] *= m; o[1] *= m; o[2] *= m; }
    };
    const o = [0, 0, 0];
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      const i = y * W + x;
      if (kind[i] === 1) {
        const s = shade[i], h = haze[i];
        for (let c = 0; c < 3; c++) back[i * 3 + c] = alb[i * 3 + c] * amb[c] * s * (1 - h) + hzc[c] * h;
      } else if (kind[i] === 0) { sky(x, y, o); back[i * 3] = o[0]; back[i * 3 + 1] = o[1]; back[i * 3 + 2] = o[2]; }
    }
    if (!day) for (let k = 0; k < 46; k++) {      // stars: the only light older and stiller than a standing lamp
      const x = Math.floor(h2(k, 1, 131) * W), y = Math.floor(Math.pow(h2(k, 2, 131), 1.6) * 0.2 * H), i = y * W + x;
      if (kind[i] === 0) { const a = 0.05 + 0.3 * Math.pow(h2(k, 3, 131), 3); back[i * 3] += a; back[i * 3 + 1] += a; back[i * 3 + 2] += a; }
    }
    // the lake gives the hill back, upside down and combed by the wind
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      const i = y * W + x; if (kind[i] !== 2) continue;
      const dy = (y - hy) / sc, sp = 1.2 + 0.05 * dy;
      const wob = (vn(x / (26 * sc), y / ((1.3 + 0.012 * dy) * sc), 141) - 0.5);
      const xs = clamp(Math.round(x + wob * (2 + 0.07 * dy) * sc), 0, W - 1);
      let r = 0, g = 0, b = 0;
      for (let k = 0; k < 4; k++) {
        let yr = Math.round(2 * hy - y + (k - 1.5) * sp * sc + wob * 3 * sp * sc);
        let j = yr < 0 ? xs : yr * W + xs;
        if (yr >= 0 && kind[j] === 2) { r += hzc[0]; g += hzc[1]; b += hzc[2]; continue; }
        if (yr < 0) { sky(xs, 0, o); r += o[0]; g += o[1]; b += o[2]; continue; }
        r += back[j * 3]; g += back[j * 3 + 1]; b += back[j * 3 + 2];
      }
      const lane = sst(0.55, 0.75, fbm(x / (520 * sc), y / (26 * sc) + 0.0015 * x / sc, 3, 151)) * sst(0, 160, dy);
      const sheen = (0.2 + 1.3 * lane) * (day ? 0.5 : 1), near = 0.7;
      back[i * 3] = r / 4 * near + hzc[0] * 0.55 * sheen;
      back[i * 3 + 1] = g / 4 * near + hzc[1] * 0.55 * sheen;
      back[i * 3 + 2] = b / 4 * near + hzc[2] * 0.55 * sheen;
    }
    return back;
  }
  const backNight = backdrop(false);
  let backDay = null;

  // ---------------------------------------------------------------- the walk
  const SPEED = 1.3, GAP = 3.1, NFILE = 40;
  const paths = {};
  function mk(name, pts) {
    const n = pts.length, u = new Float32Array(n), v = new Float32Array(n), z = new Float32Array(n);
    for (let i = 0; i < n; i++) { u[i] = pts[i][0]; v[i] = pts[i][1]; z[i] = bare(u[i], v[i]); }
    paths[name] = { u, v, z, n }; return paths[name];
  }
  const iFarm = nearest(ROAD, -150, 350), iShore = nearest(ROAD, 100, 105), iGate = nearest(ROAD.slice(940), -30, 208) + 940;
  mk('road', ROAD);
  mk('ridge', TROD.ridge);
  mk('farm', ROAD.slice(0, iFarm).concat(TROD.farm));
  mk('shore', ROAD.slice(0, iShore).concat(TROD.shore));
  mk('beck', TROD.beck.concat(ROAD.slice(iBeck4)));
  const LEN = ROAD.length - 1;
  const lamps = [];
  let rank = 0;
  for (let k = 0; k < NFILE; k++) {
    const t0 = k * GAP + 1.4 * n1(k * 0.9, 201), side = (k % 2 ? 1 : -1) * (0.5 + 0.5 * h2(k, 5, 203));
    const l = { path: paths.road, t0, end: 0, side, k, amp: 0.8 + 0.4 * h2(k, 9, 203), pole: 1.3 + 2.3 * h2(k, 11, 203) };
    if (k === 11) { l.path = paths.farm; l.end = l.path.n - 1; }
    else if (k === 18) { l.end = iGate; l.side = 1.6; }
    else if (k === 31) { l.path = paths.shore; l.end = l.path.n - 1; }
    else { l.end = LEN - 1.15 * rank; l.side = (rank % 2 ? 1 : -1) * 0.9; rank++; }
    lamps.push(l);
  }
  const T_FILE_END = (NFILE - 1) * GAP + LEN / SPEED;
  // the late one, who comes over the pass after everyone and goes along the top
  lamps.push({ path: paths.ridge, t0: 575, end: paths.ridge.n - 1, side: 0, k: 50, amp: 1.25, pole: 2.4 });
  // the one who comes up the beck from the water to meet them, and goes down again with the last of the file
  { const p = paths.beck, join = TROD.beck.length - 1, tJoin = (NFILE - 1) * GAP + iBeck4 / SPEED + GAP;
    lamps.push({ path: p, t0: tJoin - join / SPEED, end: p.n - 1 - 1.15 * rank, side: 0.9, k: 51, amp: 1.15, pole: 2.2 }); }
  const T_VEIL = Math.max(T_FILE_END, lamps[lamps.length - 1].t0 + lamps[lamps.length - 1].end / SPEED) + 6;
  const T_END = T_VEIL + 200;
  const STAGE = { u: 21, v: 3.5, z: bare(21, 3.5) + 5.5 };

  const P = [0, 0, 0];
  function where(l, t) {
    let s = (t - l.t0) * SPEED;
    if (s > 0 && s < l.end) s += 1.3 * n1(t / 23 + l.k * 3.7, 211);
    s = clamp(s, 0, l.end);
    const p = l.path, i = Math.min(p.n - 2, Math.floor(s)), fr = s - i;
    const tu = p.u[i + 1] - p.u[i], tv = p.v[i + 1] - p.v[i], tl = Math.hypot(tu, tv) + 1e-6;
    const off = l.side + 0.55 * n1(s / 21 + l.k * 7.3, 213);
    P[0] = p.u[i] + tu * fr - tv / tl * off; P[1] = p.v[i] + tv * fr + tu / tl * off;
    P[2] = p.z[i] + (p.z[i + 1] - p.z[i]) * fr + l.pole + 0.22 * n1(s / 7 + l.k * 5.1, 215);
    return s <= 0 ? 0 : s >= l.end ? 2 : 1;
  }
  const flame = (l, t) => t >= T_VEIL ? 0 : l.amp * (0.72 + 0.45 * vn(t / 2.3 + l.k * 31.7, 0.5, 221)) * sst(T_VEIL, T_VEIL - 0.6, t);

  // ---------------------------------------------------------------- seeing it
  const Wl = Math.ceil(W / 4), Hl = Math.ceil(H / 4), Wg = Math.ceil(W / 2), Hg = Math.ceil(H / 2);
  const core = new Float32Array(N * 3), refl = new Float32Array(N * 3), tmp = new Float32Array(H * 3);
  const pool = new Float32Array(Wl * Hl * 3), glare = new Float32Array(Wg * Hg * 3);
  const colTouched = new Uint8Array(W), colNear = new Uint8Array(W);
  const I0 = 400 * sc * sc, SIG = 0.62 * sc;
  const LUTN = 8192, LUTMAX = 6, lut = new Float32Array(LUTN + 1);
  for (let i = 0; i <= LUTN; i++) { const v = i / LUTN * LUTMAX; lut[i] = 255 * Math.pow(1 - Math.exp(-2.1 * v), 1 / 2.2); }
  const dith = new Float32Array(N); for (let i = 0; i < N; i++) dith[i] = h2(i % W, (i / W) | 0, 301) * 1.6 - 0.3;
  const wx = new Float32Array(9), wy = new Float32Array(9);

  function gsplat(buf, bw, bh, x, y, sx, sy, r, g, b) {
    const rx = Math.min(40, Math.ceil(sx * 2.6)), ry = Math.min(40, Math.ceil(sy * 2.6));
    const ix = Math.round(x), iy = Math.round(y), nrm = 1 / (2 * Math.PI * sx * sy);
    for (let j = -ry; j <= ry; j++) {
      const yy = iy + j; if (yy < 0 || yy >= bh) continue;
      const wyy = Math.exp(-((yy - y) ** 2) / (2 * sy * sy)) * nrm;
      for (let i = -rx; i <= rx; i++) {
        const xx = ix + i; if (xx < 0 || xx >= bw) continue;
        const w = wyy * Math.exp(-((xx - x) ** 2) / (2 * sx * sx)), o = (yy * bw + xx) * 3;
        buf[o] += r * w; buf[o + 1] += g * w; buf[o + 2] += b * w;
      }
    }
  }
  function point(sx, sy, dv, zl, r, g, b) {
    const ix = Math.round(sx), iy = Math.round(sy);
    if (ix < 2 || iy < 2 || ix >= W - 2 || iy >= H - 2) return false;
    const pi = iy * W + ix;
    if (kind[pi] === 1 && dvm[pi] < dv - 5) return false;      // behind a fold, a wall, a wood
    const inv = 1 / (2 * SIG * SIG), nrm = inv / Math.PI;
    for (let k = -2; k <= 2; k++) { wx[k + 2] = Math.exp(-((ix + k - sx) ** 2) * inv); wy[k + 2] = Math.exp(-((iy + k - sy) ** 2) * inv) * nrm; }
    for (let j = -2; j <= 2; j++) for (let i = -2; i <= 2; i++) {
      const w = wx[i + 2] * wy[j + 2], o = ((iy + j) * W + ix + i) * 3;
      core[o] += r * w; core[o + 1] += g * w; core[o + 2] += b * w;
    }
    // and in the lake
    const ry = hy + f * (zl + CAM_Z) / dv, jy = Math.floor(ry);
    if (jy >= 0 && jy < H - 1 && kind[jy * W + ix] === 2) {
      const fy = ry - jy, fx0 = Math.floor(sx), fx = sx - fx0;
      for (let a = 0; a < 2; a++) for (let c = 0; c < 2; c++) {
        const w = (a ? fy : 1 - fy) * (c ? fx : 1 - fx) * 0.55, o = ((jy + a) * W + fx0 + c) * 3;
        refl[o] += r * w; refl[o + 1] += g * w; refl[o + 2] += b * w; colTouched[fx0 + c] = 1;
      }
    }
    return true;
  }

  function draw(T, opt2) {
    opt2 = opt2 || {};
    const extra = (opt2.seat === undefined ? 500 : opt2.seat) - 500;
    core.fill(0); refl.fill(0); pool.fill(0); glare.fill(0); colTouched.fill(0);
    const all = opt2.none ? [] : lamps;
    for (let li = 0; li <= all.length; li++) {
      const l = li < all.length ? all[li] : null;
      if (!l) {            // the stage lamp, which is not hers and is never veiled
        const dv = STAGE.v - CAM_V, sx = cx + f * STAGE.u / dv, sy = hy - f * (STAGE.z - CAM_Z) / dv;
        const a = I0 * 0.8 * Math.pow(700 / dv, 1.4) * (0.92 + 0.08 * vn(T / 1.7, 0.5, 401));
        point(sx, sy, dv, STAGE.z, a, a, a);
        gsplat(glare, Wg, Hg, sx / 2, sy / 2, 1.6 * sc, 1.6 * sc, a * 0.012, a * 0.012, a * 0.012);
        gsplat(pool, Wl, Hl, sx / 4, (sy + 5.5 * f / dv) / 4, 5 * f / dv / 4, 5 * f / dv / 4 * 0.34, a * 0.05, a * 0.05, a * 0.05);
        break;
      }
      // every moment this lamp was somewhere whose light is arriving now, in one colour or another
      let te = T - (1230 + extra) / C_VIOLET - 2;
      const teMax = T - (480 + extra) / C_RED;
      let ar = 0, ag = 0, ab = 0, ax = 0, ay = 0, aw = 0, adv = 800, lx = -1e9, ly = 0;
      while (te < teMax) {
        const st = where(l, te);
        const dvv = P[1] - CAM_V, d = Math.hypot(P[0], dvv) + extra;
        const dt = st === 1 ? clamp(0.75 * dvv / (SPEED * f), 0.04, 0.5) : (st === 0 ? 1.5 : Math.min(1.0, 0.012 * d * DSLOW));
        const lag = T - te, x = (lag / d - SLOW0) / DSLOW;
        te += dt;
        if (st === 0 || x <= 0 || x >= 1) continue;
        const fl = flame(l, te - dt); if (fl <= 0) continue;
        // the slice of the spectrum that left during this dt
        const xa = clamp(x - dt / (2 * d * DSLOW), 1e-5, 1), xb = clamp(x + dt / (2 * d * DSLOW), 1e-5, 1);
        const sa = Math.pow(xa, 1 / DISP), sb = Math.pow(xb, 1 / DISP), ds = sb - sa;
        const si = Math.min(SPEC.N - 1, Math.floor((sa + sb) * 0.5 * SPEC.N)) * 3;
        const e = fl * ds * Math.pow(700 / dvv, 1.4);
        const r = SPEC.t[si] * e, g = SPEC.t[si + 1] * e, b = SPEC.t[si + 2] * e;
        const sx = cx + f * P[0] / dvv, sy = hy - f * (P[2] - CAM_Z) / dvv;
        if (!point(sx, sy, dvv, P[2], r * I0, g * I0, b * I0)) continue;
        // ground light and glare, gathered and laid a few at a time
        ar += r; ag += g; ab += b; ax += sx * e; ay += sy * e; aw += e; adv = dvv;
        if (Math.abs(sx - lx) + Math.abs(sy - ly) > 5 * sc) {
          const px = ax / aw, py = ay / aw, ps = 2.8 * f / adv;
          gsplat(pool, Wl, Hl, px / 4, (py + 2.2 * f / adv) / 4, ps / 4, ps * 0.34 / 4, ar * I0 * 0.04, ag * I0 * 0.04, ab * I0 * 0.04);
          gsplat(glare, Wg, Hg, px / 2, py / 2, 1.5 * sc, 1.5 * sc, ar * I0 * 0.007, ag * I0 * 0.007, ab * I0 * 0.007);
          ar = ag = ab = ax = ay = aw = 0; lx = sx; ly = sy;
        }
      }
      if (aw > 0) {
        const px = ax / aw, py = ay / aw, ps = 2.8 * f / adv;
        gsplat(pool, Wl, Hl, px / 4, (py + 2.2 * f / adv) / 4, ps / 4, ps * 0.34 / 4, ar * I0 * 0.04, ag * I0 * 0.04, ab * I0 * 0.04);
        gsplat(glare, Wg, Hg, px / 2, py / 2, 1.5 * sc, 1.5 * sc, ar * I0 * 0.007, ag * I0 * 0.007, ab * I0 * 0.007);
      }
    }
    // comb the reflections down the water toward the bench
    for (let x = 0; x < W; x++) {
      if (!colTouched[x]) continue;
      let y0 = 0; while (y0 < H && kind[y0 * W + x] !== 2) y0++;
      for (let pass = 0; pass < 3; pass++) {
        for (let c = 0; c < 3; c++) {
          let acc = 0;
          for (let y = y0; y < H; y++) { acc += refl[(y * W + x) * 3 + c]; tmp[y] = acc; }
          for (let y = H - 1; y >= y0; y--) {
            const r = (2 + 0.075 * (y - hy) / sc) * sc;
            const a = Math.max(y0 - 1, Math.round(y - 1.6 * r) - 1), b = Math.min(H - 1, Math.round(y + 0.4 * r));
            refl[(y * W + x) * 3 + c] = (tmp[b] - (a < y0 ? 0 : tmp[a])) / (2 * r + 1);
          }
        }
      }
    }
    let run = 0; for (let x = 0; x < W; x++) { run = colTouched[x] ? 8 : run - 1; if (run > 0) colNear[x] = 1; else colNear[x] = 0; }
    run = 0; for (let x = W - 1; x >= 0; x--) { run = colTouched[x] ? 8 : run - 1; if (run > 0) colNear[x] = 1; }
  }

  function render(T, out, opt2) {
    opt2 = opt2 || {};
    draw(T, opt2);
    let back = backNight;
    if (opt2.day) { back = backDay || (backDay = backdrop(true)); }
    const gain = opt2.day ? 0 : 1;
    for (let y = 0; y < H; y++) {
      const yl = Math.min(Hl - 2, Math.max(0, (y - 1.5) / 4)), yl0 = Math.floor(yl), fyl = yl - yl0;
      const yg = Math.min(Hg - 2, Math.max(0, (y - 0.5) / 2)), yg0 = Math.floor(yg), fyg = yg - yg0;
      const dy = (y - hy) / sc;
      for (let x = 0; x < W; x++) {
        const i = y * W + x, o = i * 3, k = kind[i];
        let r = back[o], g = back[o + 1], b = back[o + 2];
        if (gain) {
          const xg = Math.min(Wg - 2, Math.max(0, (x - 0.5) / 2)), xg0 = Math.floor(xg), fxg = xg - xg0;
          const g0 = (yg0 * Wg + xg0) * 3, g1 = g0 + Wg * 3;
          const w00 = (1 - fxg) * (1 - fyg), w10 = fxg * (1 - fyg), w01 = (1 - fxg) * fyg, w11 = fxg * fyg;
          r += core[o] + glare[g0] * w00 + glare[g0 + 3] * w10 + glare[g1] * w01 + glare[g1 + 3] * w11;
          g += core[o + 1] + glare[g0 + 1] * w00 + glare[g0 + 4] * w10 + glare[g1 + 1] * w01 + glare[g1 + 4] * w11;
          b += core[o + 2] + glare[g0 + 2] * w00 + glare[g0 + 5] * w10 + glare[g1 + 2] * w01 + glare[g1 + 5] * w11;
          if (k === 1) {
            const xl = Math.min(Wl - 2, Math.max(0, (x - 1.5) / 4)), xl0 = Math.floor(xl), fxl = xl - xl0;
            const p0 = (yl0 * Wl + xl0) * 3, p1 = p0 + Wl * 3;
            const v00 = (1 - fxl) * (1 - fyl), v10 = fxl * (1 - fyl), v01 = (1 - fxl) * fyl, v11 = fxl * fyl;
            const s = (0.35 + 0.65 * shade[i]) * 0.9 * (1 - 0.5 * haze[i]);
            r += (pool[p0] * v00 + pool[p0 + 3] * v10 + pool[p1] * v01 + pool[p1 + 3] * v11) * alb[o] * s;
            g += (pool[p0 + 1] * v00 + pool[p0 + 4] * v10 + pool[p1 + 1] * v01 + pool[p1 + 4] * v11) * alb[o + 1] * s;
            b += (pool[p0 + 2] * v00 + pool[p0 + 5] * v10 + pool[p1 + 2] * v01 + pool[p1 + 5] * v11) * alb[o + 2] * s;
          } else if (k === 2 && colNear[x]) {
            // each row of water is pushed a little left or right of the one above it
            const wv = vn(x / ((30 + 0.06 * dy) * sc), y / ((1.5 + 0.012 * dy) * sc) + T * 0.8, 501);
            const xs = x + Math.round((wv - 0.5) * (2.5 + 0.016 * dy) * sc), q = (y * W + (xs < 0 ? 0 : xs >= W ? W - 1 : xs)) * 3;
            if (refl[q] + refl[q + 1] + refl[q + 2] > 1e-5) {
              const m = 0.1 + 2.6 * sst(0.52, 0.82, vn(x / (30 * sc) + T * 0.15, y / ((0.8 + 0.006 * dy) * sc) - T * 0.7, 503));
              r += refl[q] * m; g += refl[q + 1] * m; b += refl[q + 2] * m;
            }
          }
        }
        const d = dith[i];
        out[i * 4] = lut[Math.min(LUTN, (r > 0 ? r : 0) * (LUTN / LUTMAX) | 0)] + d;
        out[i * 4 + 1] = lut[Math.min(LUTN, (g > 0 ? g : 0) * (LUTN / LUTMAX) | 0)] + d;
        out[i * 4 + 2] = lut[Math.min(LUTN, (b > 0 ? b : 0) * (LUTN / LUTMAX) | 0)] + d;
        out[i * 4 + 3] = 255;
      }
    }
    if (opt2.ways) chalk(out);
  }

  // the ways drawn on the daylight hill, as she walks them off beforehand
  function chalk(out) {
    const dot = (u, v, r, g, b, a) => {
      const z = bare(u, v) + 0.3, dv = v - CAM_V, x = Math.round(cx + f * u / dv), y = Math.round(hy - f * (z - CAM_Z) / dv);
      if (x < 1 || y < 1 || x >= W - 1 || y >= H - 1) return;
      const pi = y * W + x; if (kind[pi] === 1 && dvm[pi] < dv - 5) return;
      for (let j = 0; j < 2; j++) for (let i = 0; i < 2; i++) { const o = ((y + j) * W + x + i) * 4; out[o] += (r - out[o]) * a; out[o + 1] += (g - out[o + 1]) * a; out[o + 2] += (b - out[o + 2]) * a; }
    };
    for (let i = 0; i < ROAD.length; i++) dot(ROAD[i][0], ROAD[i][1], 190, 30, 20, 0.85);
    for (const k in TROD) for (let i = 0; i < TROD[k].length; i += 3) dot(TROD[k][i][0], TROD[k][i][1], 60, 30, 150, 0.9);
  }

  return { W, H, render, lamps, T_VEIL, T_END, T_FILE_END, SPEED };
}

G.Walk = { build, C_RED, C_VIOLET };
})(typeof globalThis !== 'undefined' ? globalThis : this);
