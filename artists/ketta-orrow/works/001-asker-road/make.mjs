// Writes the stills for walk 001 from the same code the live piece runs.
//   node make.mjs            final.png, stages/, work.json
//   node make.mjs sheet DIR  small frames through the whole walk, for looking
import { createRequire } from 'node:module';
import { deflateSync } from 'node:zlib';
import { writeFileSync, mkdirSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
const here = path.dirname(fileURLToPath(import.meta.url));
createRequire(import.meta.url)('./piece/walk.js');
const Walk = globalThis.Walk;

const crcT = new Uint32Array(256).map((_, n) => { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; return c >>> 0; });
const crc = b => { let c = ~0; for (let i = 0; i < b.length; i++) c = crcT[(c ^ b[i]) & 255] ^ (c >>> 8); return ~c >>> 0; };
function png(file, rgba, W, H) {
  const raw = Buffer.alloc((W * 3 + 1) * H);
  for (let y = 0; y < H; y++) { raw[y * (W * 3 + 1)] = 0; for (let x = 0; x < W; x++) { const o = y * (W * 3 + 1) + 1 + x * 3, i = (y * W + x) * 4; raw[o] = rgba[i]; raw[o + 1] = rgba[i + 1]; raw[o + 2] = rgba[i + 2]; } }
  const chunk = (t, d) => { const b = Buffer.alloc(12 + d.length); b.writeUInt32BE(d.length, 0); b.write(t, 4, 'ascii'); d.copy(b, 8); b.writeUInt32BE(crc(b.subarray(4, 8 + d.length)), 8 + d.length); return b; };
  const ih = Buffer.alloc(13); ih.writeUInt32BE(W, 0); ih.writeUInt32BE(H, 4); ih[8] = 8; ih[9] = 2;
  writeFileSync(file, Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', ih), chunk('IDAT', deflateSync(raw, { level: 9 })), chunk('IEND', Buffer.alloc(0))]));
}

if (process.argv[2] === 'sheet') {
  const dir = process.argv[3], W = +(process.env.SW || 900), H = W / 1.5, s = Walk.build(W, H), out = new Uint8ClampedArray(W * H * 4);
  const ts = process.argv.slice(4).map(Number);
  console.log('veil', s.T_VEIL, 'end', s.T_END);
  for (const t of (ts.length ? ts : [200, 450, 700, 900, 1100, 1400, s.T_VEIL + 40])) { s.render(t, out); png(path.join(dir, `t${Math.round(t)}.png`), out, W, H); }
} else {
  const W = 1800, H = 1200, t0 = Date.now(), s = Walk.build(W, H), out = new Uint8ClampedArray(W * H * 4);
  console.log('hill built', Date.now() - t0, 'ms; veil at', s.T_VEIL);
  mkdirSync(path.join(here, 'stages'), { recursive: true });
  const FINAL = 945;
  const stages = [
    ['The Asker side in the white hour, with the ways she is allowed walked off on it', { day: true, none: true, ways: true }, 0],
    ['The violet hour, before anyone is over the pass. The stage lamp is not hers', { none: true }, 0],
    ['First red over the pass', {}, 75],
    ['The file on the first leg, its violet still coming over the top', {}, 300],
    ['Hask farm: one leaves the file and has her colours to herself', {}, 730],
    ['The late one along the top, the one up the beck, the file between them', {}, FINAL],
    ['The same count from a boat close in under the Asker stage: the file has pulled nearly all its colours in', { seat: 40 }, FINAL],
    ['The same count from the top bench, 1,300 paces off: the file has no white left in it', { seat: 1300 }, FINAL],
    ['The quay: the file standing, each with all their colours back', {}, s.T_VEIL - 4],
    ['After the shutter. Every lamp is dark; the bench is still owed the slow colours, the far lamps most', {}, s.T_VEIL + 66],
  ];
  const list = [];
  stages.forEach(([name, opt, t], i) => {
    s.render(t, out, opt); const file = `stages/${String(i).padStart(2, '0')}.png`;
    png(path.join(here, file), out, W, H); list.push({ name, file: file.replace('.png', '.jpg') }); console.log(file, name);
  });
  s.render(FINAL, out); png(path.join(here, 'final.png'), out, W, H);
  list.push({ name: 'From the shore bench, count 945', file: 'final.png' });
  // stills of the phases are kept as jpg, like everyone else's
  execFileSync('uv', ['run', 'python', '-c', `
import glob, os
from PIL import Image
for f in glob.glob(${JSON.stringify(path.join(here, 'stages', '*.png'))}):
    Image.open(f).convert('RGB').save(f[:-4] + '.jpg', quality=90); os.remove(f)
`], { stdio: 'inherit' });
  writeFileSync(path.join(here, 'work.json'), JSON.stringify({
    title: 'Asker road, forty down and one along the top', artist: 'ketta-orrow', year: '259',
    medium: 'Walk for forty-two lime lamps on the Asker side, seen across the Long Water from the shore bench. Half an hour; the live piece runs at eight times walking pace',
    made: '2026-11-14', program: 'piece/walk.js', live: 'piece/index.html', strokes: s.lamps.length, marks: 'lamps', size: [W, H], stages: list,
  }, null, 2) + '\n');
}
