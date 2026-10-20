import fs from 'fs';
import path from 'path';
const ROOT = process.argv[2];
const { load, Map26, HERE } = await import(path.join(ROOT, 'tools/mapgen/engine.mjs'));
// cambc 3.0.1 maps (golem camps) need the 3.0.1 engine (sh tools/replay/fetch-engine.sh); older maps load in either
const V1 = path.join(HERE, '.cache', 'engine-v1_0_0.wasm');
const E = await load(fs.existsSync(V1) ? V1 : undefined);
for (const f of process.argv.slice(4)) {
  const m = Map26.fromBytes(E, fs.readFileSync(f));
  const rows = [];
  for (let y = 0; y < m.hgt; y++) { let s = ''; for (let x = 0; x < m.w; x++) s += m.is('WALL', x, y) ? '#' : m.is('HOLE', x, y) ? 'o' : m.is('ALTAR', x, y) ? 'A' : m.is('BUSH', x, y) ? '"' : '.'; rows.push(s); }
  fs.writeFileSync(path.join(process.argv[3], path.basename(f, '.map26a') + '.json'), JSON.stringify({ w: m.w, h: m.hgt, sym: m.symmetry, spawn: m.spawn, rows }));
  m.destroy();
}
