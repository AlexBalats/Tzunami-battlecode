// rebuild each unseen tournament map from a decoded replay (dec2.mjs: grid, camps, spawnA, sym, picks) as .map26a,
// then reload it with the replay engine and check size + camp layout + tiles match. Scratch only.
import fs from 'node:fs'; import path from 'node:path';
import { load, Map26 } from '/Users/jacobchau/Desktop/Tzunami-battlecode/tools/mapgen/engine.mjs';
const [DEC, OUT] = process.argv.slice(2);
const E = await load('/Users/jacobchau/Desktop/Tzunami-battlecode/tools/mapgen/.cache/engine-v1_0_3.wasm');
const KIND = { WOLF: 0, ELK: 1, GEM_CLUSTER: 2, GOLD_CLUSTER: 3, MONOLITH: 4, GOLEM: 5 };
const done = new Set();
for (const f of fs.readdirSync(DEC).filter((f) => f.endsWith('.json')).sort()) {
  const d = JSON.parse(fs.readFileSync(path.join(DEC, f))); const m = d.meta;
  if (done.has(m.map)) continue; done.add(m.map);
  const M = Map26.create(E, m.w, m.h, m.sym);
  M.champs = m.picks[0].length;
  const [x0, y0, x1, y1] = m.spawnA; M.setSpawn(x0, y0, x1, y1);
  const K = { '#': 'WALL', 'o': 'HOLE', 'A': 'ALTAR', 'b': 'BUSH' };
  let err = 0;
  for (let y = 0; y < m.h; y++) for (let x = 0; x < m.w; x++) { const k = K[m.grid[y][x]]; if (k && !M.is(k, x, y)) { try { M.add(k, x, y); } catch (e) { err++; } } }
  for (const c of d.camps) { try { M.addCamp(KIND[c.type], c.x, c.y); } catch (e) { err++; } }
  const bytes = M.encode(); M.destroy();
  const name = 's2-' + m.map.slice(1);
  fs.writeFileSync(path.join(OUT, name + '.map26a'), bytes);
  // verify: reload as a map, compare tiles and full-map camps
  const B = Map26.fromBytes(E, bytes);
  let bad = 0;
  for (let y = 0; y < m.h; y++) for (let x = 0; x < m.w; x++) { const ch = B.is('WALL', x, y) ? '#' : B.is('HOLE', x, y) ? 'o' : B.is('ALTAR', x, y) ? 'A' : B.is('BUSH', x, y) ? 'b' : '.'; if (ch !== m.grid[y][x]) bad++; }
  const sp = B.spawn; B.destroy();
  console.log(name, `${m.w}x${m.h}`, 'champs', m.picks[0].length, 'sym', m.sym, 'add errors', err, 'tile mismatches', bad, 'spawn', JSON.stringify(sp), 'bytes', bytes.length);
}
