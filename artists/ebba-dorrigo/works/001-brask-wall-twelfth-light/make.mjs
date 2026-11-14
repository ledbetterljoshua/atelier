// Stills for the gallery, taken from the piece itself in headless Chrome, and work.json.
//   node make.mjs
import { execFileSync } from 'node:child_process';
import { writeFileSync, mkdirSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const chrome = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const W = 1500, H = 1875, TAU = 5.0;
const page = 'file://' + join(here, 'live/index.html');

function shot(file, query) {
  execFileSync(chrome, ['--headless=new', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=1',
    `--window-size=${W},${H}`, '--virtual-time-budget=120000', `--screenshot=${join(here, file)}`,
    `${page}?w=${W}&tau=${TAU}&${query}`], { stdio: 'ignore' });
}

mkdirSync(join(here, 'stages'), { recursive: true });
const stages = [
  ['the ground under one sway, before anyone rammed a wall on it', 'still=0', 0],
  ['the Brask wall up, and the keep it holds: hoar wherever the sun never comes', 'still=1', 0],
  ['eleven lights standing, each eye open', 'still=2', 11],
  ['the twelfth bored: first sway, the sun lying on clean hoar', 'still=3', 12],
];
stages.forEach(([name, q], i) => shot(`stages/${String(i).padStart(2, '0')}.jpg`, q));
shot('final.png', 'still=3');
// six sways on, for the journal only: the eye open
shot('stages/later-open.jpg', 'still=3&open=1');

const lines = readFileSync(join(here, 'live/light.js'), 'utf8');
writeFileSync(join(here, 'work.json'), JSON.stringify({
  title: 'Brask wall, east run. Twelfth light, for Ione Brask, breast-high',
  artist: 'ebba-dorrigo',
  year: 'sway 32,771',
  medium: 'Twelve bored lights in a rammed-gravel shade wall, hoar, and one sway of the sun. Seen from the ward mast.',
  made: new Date().toISOString().slice(0, 10),
  program: 'live/light.js',
  live: 'live/index.html',
  marks: 'lights',
  strokes: 12,
  size: [W, H],
  stages: [
    ...stages.map(([name, , n], i) => ({ name, strokes: n, file: `stages/${String(i).padStart(2, "0")}.jpg` })),
    { name: 'finished: the piece goes on from here, and the eye opens over six sways', strokes: 12, file: 'final.png' },
  ],
}, null, 2) + '\n');
console.log('made', stages.length + 1, 'stills;', lines.split('\n').length, 'lines');
