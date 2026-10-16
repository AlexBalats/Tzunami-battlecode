// Describe .map26a files and check they round-trip byte for byte through MapBuilder.
// Usage: node tools/mapgen/dump.mjs maps/*.map26a
import fs from 'fs';
import path from 'path';
import { load, Map26 } from './engine.mjs';

const E = await load();
for (const f of process.argv.slice(2)) {
  const bytes = fs.readFileSync(f);
  const m = Map26.fromBytes(E, bytes);
  const n = { WALL: 0, HOLE: 0, ALTAR: 0, BUSH: 0 }, altars = [];
  for (let y = 0; y < m.hgt; y++) for (let x = 0; x < m.w; x++) for (const k in n) if (m.is(k, x, y)) { n[k]++; if (k === 'ALTAR') altars.push([x, y]); }
  const kinds = {};
  for (const c of m.camps()) kinds[c.type] = (kinds[c.type] || 0) + 1;
  const g = m.groups();
  const same = Buffer.compare(m.encode(), bytes) === 0;
  console.log(`${path.basename(f)} ${m.w}x${m.hgt} ${m.symmetry} champs=${m.champs} spawnA=${JSON.stringify(m.spawn)} ` +
    `tiles=${JSON.stringify(n)} altars=${JSON.stringify(altars)} camps=${JSON.stringify(kinds)} groups=${g.length} ` +
    `group0=${JSON.stringify(g[0])} roundtrip=${same ? 'OK' : 'DIFF'}`);
  m.destroy();
}
