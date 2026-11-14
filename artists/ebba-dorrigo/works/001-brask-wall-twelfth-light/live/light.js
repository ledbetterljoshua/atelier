'use strict';
// Brask wall, east run. Twelfth light.
// The reckoning: where a round bore in a shade wall puts the sun over one sway,
// what that costs the hoar behind it, and how it looks from the scrape-house roof.
// Lengths in metres, angles in radians. x runs along the wall, y is up, z is nightward.

const RAD = Math.PI / 180;

// ---- the sway: the sun's whole year, a small leaning loop above the sunward horizon
const SWAY = { e0: 6.2 * RAD, ae: 2.6 * RAD, aa: 6.0 * RAD, lag: 0.45, rho: 1.1 * RAD };

function sunAt(tau) {
  const e = SWAY.e0 + SWAY.ae * Math.sin(tau);
  const a = SWAY.aa * Math.cos(tau - SWAY.lag);
  const ce = Math.cos(e);
  return { a, e, x: Math.sin(a) * ce, y: Math.sin(e), z: -Math.cos(a) * ce,
           tane: Math.tan(e), tana: Math.tan(a), cosa: Math.cos(a) };
}

// ---- the wall: rammed gravel, 2.2 thick, shade face at z = 0
const WALL = { x0: -46, x1: 18.5, T: 2.2, H: 6.8 };
function h2(x, y) {
  let n = (Math.imul(x | 0, 374761393) + Math.imul(y | 0, 668265263)) | 0;
  n = Math.imul(n ^ (n >>> 13), 1274126177);
  return ((n ^ (n >>> 16)) >>> 0) / 4294967296;
}
function vnoise(x, y) {
  const ix = Math.floor(x), iy = Math.floor(y);
  let fx = x - ix, fy = y - iy;
  fx = fx * fx * (3 - 2 * fx); fy = fy * fy * (3 - 2 * fy);
  const a = h2(ix, iy), b = h2(ix + 1, iy), c = h2(ix, iy + 1), d = h2(ix + 1, iy + 1);
  return a + (b - a) * fx + (c - a) * fy + (a - b - c + d) * fx * fy;
}
const HSTEP = 0.25, HN = Math.ceil((WALL.x1 - WALL.x0) / HSTEP) + 2;
const HTOP = new Float32Array(HN);
for (let i = 0; i < HN; i++) {
  const x = WALL.x0 + i * HSTEP;
  // rammed a lift at a time; the top sags between the old shutter posts
  HTOP[i] = WALL.H + 0.32 * (vnoise(x / 7.3 + 11, 3.5) - 0.5) + 0.05 * (vnoise(x / 0.9, 9.5) - 0.5);
}
function wallH(x) {
  const f = (x - WALL.x0) / HSTEP;
  const i = f < 0 ? 0 : f > HN - 2 ? HN - 2 : f | 0;
  const t = f - i;
  return HTOP[i] + (HTOP[i + 1] - HTOP[i]) * (t < 0 ? 0 : t > 1 ? 1 : t);
}

// ---- the lights. x along the wall, y above the keep floor, r the bore.
// aim: where in the sway the bore looks (azimuth, elevation). A bore is 2.2 long:
// a narrow one sees only the part of the sway it is pointed at.
const E0 = SWAY.e0, D = RAD;
const LIGHTS = [
  { x: -22.5, y: 1.00, r: 0.26, aim: [0, E0] },
  { x: -16.5, y: 2.05, r: 0.30, aim: [0, E0] },
  { x: -12.4, y: 0.55, r: 0.20, aim: [0, E0] },
  { x: -8.3,  y: 1.45, r: 0.28, aim: [0, E0] },             // the two Brasks who shared a bed:
  { x: -6.5,  y: 1.45, r: 0.28, aim: [0, E0] },             //   the only eyes allowed to touch
  { x: -2.4,  y: 0.80, r: 0.22, aim: [0, E0] },
  { x: 6.3,   y: 1.10, r: 0.13, aim: [1.5 * D, 8.2 * D] },  // narrow, aimed high: an arc, not an eye
  { x: 8.8,   y: 0.45, r: 0.20, aim: [0, E0] },
  { x: 12.2,  y: 2.95, r: 0.33, aim: [0, E0] },             // thrown past the keep: it bites the edge
  { x: 15.9,  y: 1.15, r: 0.26, aim: [0, E0] },
  { x: -28.5, y: 0.75, r: 0.22, aim: [0, E0] },
  { x: 1.9,   y: 1.30, r: 0.29, aim: [0, E0] },             // the twelfth: Ione Brask, breast-high
];
for (const L of LIGHTS) {
  const ce = Math.cos(L.aim[1]);
  const bx = Math.sin(L.aim[0]) * ce, by = Math.sin(L.aim[1]), bz = -Math.cos(L.aim[0]) * ce;
  const k = WALL.T / -bz;
  L.bx = L.x + bx * k; L.by = L.y + by * k;   // centre of the sunward mouth
  L.ax = bx; L.ay = by; L.az = bz;            // bore axis
}
const TWELFTH = LIGHTS.length - 1;

function sm(t) { return t <= 0 ? 0 : t >= 1 ? 1 : t * t * (3 - 2 * t); }

// How much of the sun's disc a point on the keep floor sees through one bore.
function throughBore(px, pz, L, s) {
  let vx = L.x - px, vy = L.y, vz = -pz;
  const l1 = Math.sqrt(vx * vx + vy * vy + vz * vz); vx /= l1; vy /= l1; vz /= l1;
  let wx = L.bx - px, wy = L.by, wz = -WALL.T - pz;
  const l2 = Math.sqrt(wx * wx + wy * wy + wz * wz); wx /= l2; wy /= l2; wz /= l2;
  const dx = vx - wx, dy = vy - wy, dz = vz - wz;
  const reff = 0.5 * (L.r / l1 + L.r / l2) - 0.5 * Math.sqrt(dx * dx + dy * dy + dz * dz);
  if (reff <= 0) return 0;
  let cx = vx + wx, cy = vy + wy, cz = vz + wz;
  const cl = Math.sqrt(cx * cx + cy * cy + cz * cz); cx /= cl; cy /= cl; cz /= cl;
  const ex = cx - s.x, ey = cy - s.y, ez = cz - s.z;
  const del = Math.sqrt(ex * ex + ey * ey + ez * ez), rho = SWAY.rho;
  if (del >= rho + reff) return 0;
  const k = reff >= rho ? 1 : (reff * reff) / (rho * rho);
  const lo = Math.abs(rho - reff);
  return del <= lo ? k : k * sm((rho + reff - del) / (rho + reff - lo));
}

// How much of the disc clears the top of the wall, or comes round its east end.
function overWall(px, pz, s, wallUp) {
  if (!wallUp) return 1;
  const xc = px + pz * s.tana;
  const w = SWAY.rho * pz + 0.02;
  const round = sm(0.5 + 0.5 * (xc - WALL.x1) / w);
  if (round >= 1) return 1;
  const u = (s.tane - wallH(xc) * s.cosa / pz) / (SWAY.rho * (1 + s.tane * s.tane));
  const top = sm(0.5 + 0.5 * u);
  return 1 - (1 - round) * (1 - top);
}

// ---- the dose: the share of the sway that each patch of floor spends in the sun
const GX0 = -52, GX1 = 40, GZ1 = 62, GDX = 0.1, GDZ = 0.12;
const GW = Math.round((GX1 - GX0) / GDX), GH = Math.round(GZ1 / GDZ);
const NT = 96;
const SUNS = []; for (let i = 0; i < NT; i++) SUNS.push(sunAt((i + 0.5) / NT * 2 * Math.PI));
const S0 = sunAt(0); { const c = Math.cos(E0); S0.x = 0; S0.y = Math.sin(E0); S0.z = -c; }

function reckon(which, wallUp) {
  // which: array of light indices, or null for the wall alone
  const out = new Float32Array(GW * GH);
  for (let j = 0; j < GH; j++) {
    const pz = (j + 0.5) * GDZ;
    for (let i = 0; i < GW; i++) {
      const px = GX0 + (i + 0.5) * GDX;
      let d = 0;
      if (which === null) {
        for (let t = 0; t < NT; t++) d += overWall(px, pz, SUNS[t], wallUp);
      } else {
        for (const li of which) {
          const L = LIGHTS[li];
          const vx = L.x - px, vy = L.y, vz = -pz, l = Math.sqrt(vx * vx + vy * vy + vz * vz);
          const ex = vx / l - S0.x, ey = vy / l - S0.y, ez = vz / l - S0.z;
          if (ex * ex + ey * ey + ez * ez > (0.19 + L.r / l) * (0.19 + L.r / l)) continue;
          for (let t = 0; t < NT; t++) d += throughBore(px, pz, L, SUNS[t]);
        }
      }
      out[j * GW + i] = d / NT;
    }
  }
  return out;
}
function sample(tex, x, z) {
  const fx = (x - GX0) / GDX - 0.5, fz = z / GDZ - 0.5;
  if (fx < 0 || fz < 0 || fx >= GW - 1 || fz >= GH - 1) return -1;
  const i = fx | 0, j = fz | 0, tx = fx - i, tz = fz - j, o = j * GW + i;
  return (tex[o] * (1 - tx) + tex[o + 1] * tx) * (1 - tz) + (tex[o + GW] * (1 - tx) + tex[o + GW + 1] * tx) * tz;
}

// ---- her own way in and out. Nobody walks a keep: she went along the foot of the wall from the east end.
const WAYS = [
  [[20.5, 3.4], [18.2, 1.5], [10, 1.15], [2.7, 1.05]],
  [[1.4, 0.75], [10, 0.8], [18.6, 1.1], [21.5, 2.6]],
];
function trodden(x, z) {
  if (x < 0 || x > 22 || z > 4) return 0;
  let best = 0;
  for (let w = 0; w < WAYS.length; w++) {
    const way = WAYS[w];
    let run = 0;
    for (let i = 0; i < way.length - 1; i++) {
      const ax = way[i][0], az = way[i][1], bx = way[i + 1][0] - ax, bz = way[i + 1][1] - az;
      const len = Math.sqrt(bx * bx + bz * bz), ux = bx / len, uz = bz / len;
      const along = (x - ax) * ux + (z - az) * uz, off = (x - ax) * uz - (z - az) * ux;
      if (along > -0.3 && along < len + 0.3 && off > -0.5 && off < 0.5) {
        const st = run + along, k = Math.round(st / 0.74), side = (k & 1 ? 0.17 : -0.17) + 0.06 * (h2(k, w + 5) - 0.5);
        const da = (st - k * 0.74) / 0.19, dd = (off - side) / 0.085;
        const q = da * da + dd * dd;
        if (q < 1.6) best = Math.max(best, sm((1.6 - q) / 0.9));
      }
      run += len;
    }
  }
  // where she stood to bore, and the core she drew out of the wall, tipped at its foot
  const sx = x - 1.9, stood = Math.exp(-(sx * sx / 1.1 + (z - 0.7) * (z - 0.7) / 0.55));
  return Math.max(best, Math.min(1, stood * 1.5));
}

// ---- the town sunward of us: other houses' walls, each with its keep behind it
const TOWN = [
  { z: -64, x0: -70, x1: 4, H: 5.0 },
  { z: -64, x0: 13, x1: 90, H: 5.4 },
  { z: -139, x0: -40, x1: 62, H: 6.0 },
  { z: -236, x0: -150, x1: -8, H: 5.5 },
  { z: -236, x0: 30, x1: 170, H: 5.0 },
  { z: -370, x0: -90, x1: 120, H: 6.5 },
  { z: -560, x0: -300, x1: 60, H: 6.0 },
];

// ---- the view from the ward mast, where the keep-wardens count
function makeCamera(W, H) {
  const c = { x: 2.5, y: 26, z: 70 };
  const vfov = 54 * RAD, top = 11.3 * RAD;         // the top edge sits this far above the horizon
  const pitch = top - vfov / 2, yaw = -0.035;
  const f = { x: Math.sin(yaw) * Math.cos(pitch), y: Math.sin(pitch), z: -Math.cos(yaw) * Math.cos(pitch) };
  const r = { x: Math.cos(yaw), y: 0, z: Math.sin(yaw) };
  const u = { x: r.y * f.z - r.z * f.y, y: r.z * f.x - r.x * f.z, z: r.x * f.y - r.y * f.x };
  if (u.y < 0) { u.x = -u.x; u.y = -u.y; u.z = -u.z; }
  const tv = Math.tan(vfov / 2), th = tv * W / H;
  return { c, f, r, u, tv, th, W, H };
}
function project(cam, x, y, z) {
  const dx = x - cam.c.x, dy = y - cam.c.y, dz = z - cam.c.z;
  const zf = dx * cam.f.x + dy * cam.f.y + dz * cam.f.z;
  const xr = dx * cam.r.x + dy * cam.r.y + dz * cam.r.z, yu = dx * cam.u.x + dy * cam.u.y + dz * cam.u.z;
  return { x: (xr / zf / cam.th * 0.5 + 0.5) * cam.W, y: (0.5 - yu / zf / cam.tv * 0.5) * cam.H, zf };
}

// ---- colour. Everything lit is the sun's orange; everything else is what the dark sky gives back.
const SUNC = [1.0, 0.47, 0.19];
const COOL = [0.105, 0.150, 0.215];      // the nightward sky, on a level floor
const WARMSKY = [0.42, 0.20, 0.115];     // the low sunward sky, where the wall does not hide it
const GRAVEL = [0.105, 0.082, 0.07];
const HOAR = [0.80, 0.87, 0.94];

const col = [0, 0, 0];
function sky(dx, dy, dz, s, into) {
  const el = Math.asin(dy < -1 ? -1 : dy > 1 ? 1 : dy);
  const ex = dx - s.x, ey = dy - s.y, ez = dz - s.z;
  const g = Math.sqrt(ex * ex + ey * ey + ez * ez);
  const hz = Math.exp(-Math.max(el, 0) / 0.085), mid = Math.exp(-Math.max(el, 0) / 0.30);
  let r = 0.018 + 0.032 * mid + 0.24 * hz, gr = 0.010 + 0.008 * mid + 0.066 * hz, b = 0.026 + 0.022 * mid + 0.020 * hz;
  const glow = 0.085 * Math.exp(-g / 0.24) + 0.42 * Math.exp(-g / 0.07) + 1.3 * Math.exp(-g / 0.028);
  r += glow; gr += glow * 0.42; b += glow * 0.13;
  // ice haze lying in bars along the horizon, dark against the light
  const az = Math.atan2(dx, -dz);
  const bars = vnoise(az * 3.1 + 3, el * 150 + 7) * 0.6 + vnoise(az * 9, el * 420) * 0.4;
  const bar = sm((bars - 0.52) / 0.10) * Math.exp(-Math.max(el, 0) / 0.09) * 0.55;
  let disc = 0;
  if (g < SWAY.rho * 1.04) {
    const q = g / SWAY.rho, mu = Math.sqrt(Math.max(0, 1 - q * q));
    const edge = sm((1.04 - q) / 0.05);
    // two old spots it has carried for as long as the count has been kept
    const ux = (dx - s.x) / SWAY.rho, uy = (dy - s.y) / SWAY.rho;
    const sp = 1 - 0.45 * Math.exp(-((ux + 0.32) * (ux + 0.32) + (uy - 0.22) * (uy - 0.22)) / 0.012)
                 - 0.35 * Math.exp(-((ux - 0.41) * (ux - 0.41) + (uy + 0.30) * (uy + 0.30)) / 0.006);
    const I = (0.30 + 0.70 * Math.pow(mu, 0.7)) * sp;
    disc = edge;
    r = r * (1 - edge) + edge * 3.6 * I; gr = gr * (1 - edge) + edge * 1.9 * I * (0.5 + 0.5 * mu);
    b = b * (1 - edge) + edge * 0.75 * I * (0.3 + 0.7 * mu);
  }
  const k = 1 - bar * (disc ? 0.55 : 1);
  into[0] = r * k + 0.03 * bar; into[1] = gr * k + 0.018 * bar; into[2] = b * k + 0.03 * bar;
}

function Piece(W, H) {
  const cam = makeCamera(W, H);
  const baseDose = { none: null, wall: null, eleven: null };
  let twelfth = null;
  const others = []; for (let i = 0; i < TWELFTH; i++) others.push(i);

  function prepare(stage) {
    if (stage >= 1 && !baseDose.wall) baseDose.wall = reckon(null, true);
    if (stage >= 2 && !baseDose.eleven) {
      const e = reckon(others, true), w = baseDose.wall;
      for (let i = 0; i < e.length; i++) e[i] += w[i];
      baseDose.eleven = e;
      twelfth = reckon([TWELFTH], true);
    }
  }

  const tmp = [0, 0, 0];
  // stage 0 bare ground, 1 wall and keep, 2 eleven lights, 3 the twelfth bored. open: how far its eye has opened.
  function render(data, tau, stage, open) {
    prepare(stage);
    const s = sunAt(tau);
    const wallUp = stage >= 1;
    const nLights = stage >= 3 ? LIGHTS.length : stage >= 2 ? TWELFTH : 0;
    const dose = stage >= 2 ? baseDose.eleven : baseDose.wall;
    const { c, f, r, u, tv, th } = cam;
    // where each light's patch of sun lies on the floor just now
    const spots = [];
    for (let i = 0; i < nLights; i++) {
      const L = LIGHTS[i], k = L.y / s.y;
      const slant = k, rad = (slant * SWAY.rho + L.r) / s.y + 0.6;
      const sx = L.x - s.x * k, sz = -s.z * k, peak = sz > 0.5 ? throughBore(sx, sz, L, s) : 0;
      const a = slant * SWAY.rho + L.r + 0.5, b = a / s.y * 0.75;
      spots.push({ L, x: sx, z: sz, r2: Math.max(rad * rad, 9 * b * b), peak, a2: a * a, b2: b * b });
    }
    const exposure = 1.55;
    let o = 0;
    for (let py = 0; py < H; py++) {
      const v = (0.5 - (py + 0.5) / H) * 2 * tv;
      for (let px = 0; px < W; px++) {
        const uu = ((px + 0.5) / W - 0.5) * 2 * th;
        let dx = f.x + r.x * uu + u.x * v, dy = f.y + r.y * uu + u.y * v, dz = f.z + r.z * uu + u.z * v;
        const dl = Math.sqrt(dx * dx + dy * dy + dz * dz); dx /= dl; dy /= dl; dz /= dl;
        let R = 0, G = 0, B = 0, done = false;

        // the keep floor and the open ground this side of the wall
        if (dy < 0) {
          const tg = -c.y / dy, gx = c.x + dx * tg, gz = c.z + dz * tg;
          if (gz > 0) {
            done = true;
            {
              // hoar: keeps only where the sun's share of the sway is next to nothing
              let hoar = 0, wet = 0;
              const lumpy = vnoise(gx / 2.7 + 40, gz / 3.4 + 9), grit = vnoise(gx / 0.21, gz / 0.27);
              const fine = h2(Math.floor(gx / 0.07), Math.floor(gz / 0.09));
              if (wallUp) {
                let d = sample(dose, gx, gz);
                if (d >= 0) {
                  if (stage >= 3 && open > 0) d += open * sample(twelfth, gx, gz);
                  d *= Math.exp(1.5 * (lumpy - 0.5));
                  const keep = 1 - sm((d - 0.0015) / 0.013);
                  hoar = sm((keep + (grit - 0.5) * 0.75 + (fine - 0.5) * 0.3 - 0.30) / 0.42);
                  if (stage >= 3 && open < 1) hoar *= 1 - trodden(gx, gz) * (1 - open) * 0.93;
                  wet = keep * (1 - keep) * 4;
                }
              }
              // light now
              const top = overWall(gx, gz, s, wallUp);
              let bore = 0, bleed = 0;
              for (let i = 0; i < spots.length; i++) {
                const sp = spots[i], ex = gx - sp.x, ez = gz - sp.z;
                if (ex * ex + ez * ez < sp.r2) bore += throughBore(gx, gz, sp.L, s);
                // the needles pass a little of it on sideways, and the ice in the air does the rest
                if (sp.peak > 0) bleed += sp.peak * Math.exp(-(ex * ex / sp.a2 + ez * ez / sp.b2));
              }
              if (bore > 1) bore = 1;
              // how much of the low bright sky this patch sees over the wall
              let open2 = 1;
              if (wallUp && gx < WALL.x1 + gz * 0.3) open2 = 1 - sm((Math.atan(WALL.H / gz) - 0.06) / 0.62);
              const ar = COOL[0] + WARMSKY[0] * open2, ag = COOL[1] + WARMSKY[1] * open2, ab = COOL[2] + WARMSKY[2] * open2;
              const gv = 0.72 + 0.56 * grit;
              const spark = Math.pow(fine, 22);
              const lit = top + bore;
              // bare gravel seen toward the sun shows mostly its own shadows; where a light is taking hoar it is wet and shines
              const gl = lit * (0.55 + 5.0 * spark) + bore * (2.2 + wet * 3.0) * (0.45 + 0.9 * grit + 9 * spark);
              const gR = GRAVEL[0] * gv * (ar + SUNC[0] * gl), gG = GRAVEL[1] * gv * (ag + SUNC[1] * gl), gB = GRAVEL[2] * gv * (ab + SUNC[2] * gl);
              // hoar stands up in needles and passes the light on toward us
              const hl = top * (1.25 + 0.5 * grit + 14 * spark), hb = bore * (2.3 + 1.2 * grit + 30 * spark) + bleed * (0.34 + 0.2 * grit);
              const hv = 0.80 + 0.2 * grit + 0.1 * (lumpy - 0.5);
              const hR = HOAR[0] * hv * (ar + SUNC[0] * hl + hb), hG = HOAR[1] * hv * (ag + SUNC[1] * hl + 0.40 * hb), hB = HOAR[2] * hv * (ab + SUNC[2] * hl + 0.12 * hb);
              R = gR + (hR - gR) * hoar; G = gG + (hG - gG) * hoar; B = gB + (hB - gB) * hoar;
            }
          }
        }
        if (!done && wallUp && dz < 0) {
          // the shade face
          const tw = -c.z / dz, wx = c.x + dx * tw, wy = c.y + dy * tw;
          if (wx > WALL.x0 && wx < WALL.x1 && wy > 0) {
            const top = wallH(wx);
            if (wy < top) {
              done = true;
              const lifts = vnoise(wx / 1.9, wy / 0.11) * 0.5 + vnoise(wx / 0.35, wy / 0.6 + 5) * 0.5;
              const lift = 0.5 + 0.5 * Math.cos(wy / 0.62 * 2 * Math.PI);
              let k = 0.72 + 0.32 * lifts - 0.10 * Math.pow(lift, 6);
              const up = Math.exp(-wy / 1.6);     // what the hoar throws back onto the foot of the wall
              R = 0.060 * k * (COOL[0] * 1.2 + 0.10 * up); G = 0.056 * k * (COOL[1] * 1.2 + 0.13 * up); B = 0.064 * k * (COOL[2] * 1.2 + 0.17 * up);
              const rime = sm((0.55 + 0.5 * vnoise(wx / 0.8, 2.2) - wy) / 0.5) * (0.35 + 0.65 * vnoise(wx / 0.13, wy / 0.2));
              R += rime * 0.060; G += rime * 0.085; B += rime * 0.125;
              R *= 3.4; G *= 3.1; B *= 3.0;
              for (let i = 0; i < nLights; i++) {
                const L = LIGHTS[i], ox = wx - L.x, oy = wy - L.y, q = Math.sqrt(ox * ox + oy * oy) / L.r;
                if (q < 1.0) { bore(L, ox, oy, dx, dy, dz, s, tmp); const e = sm((1.0 - q) / 0.18); R += (tmp[0] - R) * e; G += (tmp[1] - G) * e; B += (tmp[2] - B) * e; }
                else if (q < 2.2 && oy < 0) {     // the lip weeps and rimes under each bore
                  const wp = sm((2.2 - q) / 1.2) * 0.5; R += wp * 0.05; G += wp * 0.07; B += wp * 0.10;
                }
              }
            } else {
              // the top of the wall, the only part of it the sun is on
              const tt = (top - c.y) / dy, tz = c.z + dz * tt, tx = c.x + dx * tt;
              if (tz > -WALL.T && tz <= 0.05 && tx > WALL.x0 && tx < WALL.x1) {
                done = true;
                const gv = 0.5 + vnoise(tx / 0.3, tz / 0.3 + 3);
                const edge = sm((tz + WALL.T) / 0.5);
                R = 0.30 * gv * SUNC[0] * (0.9 + 0.6 * edge); G = 0.30 * gv * SUNC[1] * (0.8 + 0.5 * edge); B = 0.30 * gv * SUNC[2] * 0.9;
              }
            }
          }
        }
        if (!done) {
          // sunward: the town, the plain, the sky
          let hit = false;
          if (dz < 0) {
            for (let j = 0; j < TOWN.length && !hit; j++) {
              const w = TOWN[j], tw = (w.z - c.z) / dz, wx = c.x + dx * tw, wy = c.y + dy * tw;
              if (wy > 0 && wy < w.H + 0.25 * (vnoise(wx / 9, j * 7.1) - 0.5) && wx > w.x0 && wx < w.x1) {
                hit = true;
                const haze = Math.exp(-tw / 520);
                sky(dx, 0.004, dz, s, tmp);
                const k = 0.9 + 0.4 * vnoise(wx / 2.5, wy / 0.4 + j);
                R = 0.022 * k * haze + tmp[0] * 0.36 * (1 - haze); G = 0.021 * k * haze + tmp[1] * 0.36 * (1 - haze); B = 0.030 * k * haze + tmp[2] * 0.36 * (1 - haze);
                if (wy > w.H - 0.22) { R += 0.30 * haze; G += 0.13 * haze; B += 0.05 * haze; }
                // other houses' lights, where the roof happens to stand in one
                const cell = Math.floor(wx / 3.1), lx = (cell + 0.2 + 0.6 * h2(cell, j * 13 + 1)) * 3.1, ly = 0.5 + 2.2 * h2(cell, j * 13 + 2);
                if (h2(cell, j * 13 + 3) < 0.34) {
                  const q = Math.sqrt((wx - lx) * (wx - lx) + (wy - ly) * (wy - ly)) / (0.2 + 0.12 * h2(cell, j * 13 + 4));
                  const on = sm(1.6 * (h2(cell, j * 13 + 5) + 0.35 * Math.sin(tau + cell)) - 0.5);
                  if (q < 1.3) { const e = sm((1.3 - q) / 0.5) * on * haze; R += 1.5 * e; G += 0.62 * e; B += 0.2 * e; }
                }
              }
            }
          }
          if (!hit) {
            if (dy < 0) { const tg = -c.y / dy; townGround(c.x + dx * tg, c.z + dz * tg, dx, dy, dz, tg, s, tmp); }
            else sky(dx, dy, dz, s, tmp);
            R = tmp[0]; G = tmp[1]; B = tmp[2];
          }
        }
        // one small tooth, so the dark holds together
        const n = (h2(px + 7, py + 13) - 0.5) * 0.012;
        R = 1 - Math.exp(-R * exposure); G = 1 - Math.exp(-G * exposure); B = 1 - Math.exp(-B * exposure);
        data[o++] = 255 * Math.pow(R, 0.4545) + 255 * n + 0.5; data[o++] = 255 * Math.pow(G, 0.4545) + 255 * n + 0.5;
        data[o++] = 255 * Math.pow(B, 0.4545) + 255 * n + 0.5; data[o++] = 255;
      }
    }
  }

  // looking down into a bore from the roof: its floor, lit or not, and what glows in its throat
  function bore(L, ox, oy, dx, dy, dz, s, into) {
    // the ray runs on inside the bore until it meets the side
    const ax = L.ax, ay = L.ay, az = L.az;
    const da = dx * ax + dy * ay + dz * az;
    const qx = dx - da * ax, qy = dy - da * ay, qz = dz - da * az;      // ray across the axis
    const pa = ox * ax + oy * ay;
    const px = ox - pa * ax, py = oy - pa * ay, pz = -pa * az;
    const A = qx * qx + qy * qy + qz * qz, Bq = px * qx + py * qy + pz * qz, C = px * px + py * py + pz * pz - L.r * L.r;
    const disc = Bq * Bq - A * C;
    const t = disc > 0 && A > 1e-9 ? (-Bq + Math.sqrt(disc)) / A : 1e9;
    const depth = pa + t * da, len = WALL.T / -az;
    if (depth >= len) { sky(dx, Math.max(dy, 0.01), dz, s, into); return; }
    // the side of the bore where the ray lands, and whether the sun reaches that far in from the other mouth
    const nx = (px + t * qx) / L.r, ny = (py + t * qy) / L.r, nz = (pz + t * qz) / L.r;
    const sa = s.x * ax + s.y * ay + s.z * az;
    const sx = s.x - sa * ax, sy = s.y - sa * ay, sz = s.z - sa * az;
    const sl = Math.sqrt(sx * sx + sy * sy + sz * sz) + 1e-9;
    const facing = -(sx * nx + sy * ny + sz * nz) / sl;                 // 1 when the sun's lean points into this side
    const reach = (len - depth) * sl / sa;                              // how far the sun has to cross to get here
    const lit = facing > 0 ? sm((2 * L.r * facing - reach) / (0.7 * L.r) + 0.5) * sm(facing * 2.5) : 0;
    const throat = Math.exp(-(len - depth) / 0.9);                      // the sunward mouth glowing down the bore
    const g = 0.5 + vnoise(depth / 0.05, nx * 3 + ny * 5);
    into[0] = 0.05 + 0.16 * throat + 1.9 * lit * g; into[1] = 0.03 + 0.06 * throat + 0.86 * lit * g; into[2] = 0.035 + 0.025 * throat + 0.33 * lit * g;
  }

  function townGround(gx, gz, dx, dy, dz, tg, s, into) {
    // open plain seen toward the sun: the stones' dark sides, haze, and the sun's road on anything that shines
    let shade = 0, keep = 0;
    for (let j = 0; j < TOWN.length; j++) {
      const w = TOWN[j], back = gz - w.z;
      if (back <= 0) continue;
      const xc = gx + back * s.tana;
      if (xc < w.x0 || xc > w.x1) continue;
      const now = (w.H / back - s.tane) / (SWAY.rho * 1.2);
      shade = Math.max(shade, sm(0.5 + 0.5 * now));
      const always = w.H / Math.tan(SWAY.e0 + SWAY.ae + SWAY.rho) * (0.88 + 0.2 * vnoise(gx / 6, j * 3.3));
      const side = Math.min(gx - w.x0, w.x1 - gx) - back * 0.11;
      if (side > 0) keep = Math.max(keep, sm((always - back) / 2.5) * sm(side / 1.5) * sm(back / 0.6));
    }
    const haze = Math.exp(-tg / 520);
    const n = vnoise(gx / 0.5, gz / 1.6), n2 = vnoise(gx / 14, gz / 30);
    const ex = dx - s.x, ez = dz - s.z, road = Math.exp(-Math.sqrt(ex * ex + ez * ez) / 0.07);
    const lit = 1 - shade;
    let R = 0.105 * (0.6 + 0.5 * n + 0.4 * n2) * (0.26 + SUNC[0] * lit * (0.55 + 4.5 * road * n));
    let G = 0.082 * (0.6 + 0.5 * n + 0.4 * n2) * (0.22 + SUNC[1] * lit * (0.55 + 4.5 * road * n));
    let B = 0.070 * (0.6 + 0.5 * n + 0.4 * n2) * (0.26 + SUNC[2] * lit * (0.55 + 4.5 * road * n));
    if (keep > 0) {
      const k = keep * (0.6 + 0.4 * n);
      R += (HOAR[0] * 0.36 - R) * k; G += (HOAR[1] * 0.37 - G) * k; B += (HOAR[2] * 0.42 - B) * k;
    }
    sky(dx, 0.004, dz, s, tmp);
    into[0] = R * haze + tmp[0] * 0.42 * (1 - haze); into[1] = G * haze + tmp[1] * 0.42 * (1 - haze); into[2] = B * haze + tmp[2] * 0.42 * (1 - haze);
  }

  // what the twelfth costs: the share of the keep's hoar it takes, once its eye is open
  function cost() {
    prepare(3);
    let before = 0, after = 0;
    for (let i = 0; i < twelfth.length; i++) {
      const a = baseDose.eleven[i];
      before += 1 - sm((a - 0.0015) / 0.013); after += 1 - sm((a + twelfth[i] - 0.0015) / 0.013);
    }
    return { keepArea: before * GDX * GDZ, taken: (before - after) * GDX * GDZ };
  }
  return { render, cam, cost, project: (x, y, z) => project(cam, x, y, z) };
}

if (typeof module !== 'undefined') module.exports = { Piece, LIGHTS, SWAY, sunAt, WALL };
