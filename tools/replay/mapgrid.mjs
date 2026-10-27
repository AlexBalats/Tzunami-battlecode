// Map grids for offline study (27 Oct, the opening simulator): every maps/*.map26a -> one JSON
//   node tools/replay/mapgrid.mjs OUT.json [MAPS_DIR]
// {map: {W, H, S (champions a team), spawnA [x0,y0,x1,y1] as the engine gives it, rows: ["#.oA..", ...]}}
// '#' wall, 'o' hole, 'A' altar, '.' open. Camps and both spawns come from a decoded game on the map (decode.mjs).
import fs from 'node:fs';
import path from 'node:path';
let mem; const dv = () => new DataView(mem.buffer);
const wasi = new Proxy({ fd_write(fd, iov, cnt, out) { dv().setUint32(out, 0, true); return 0; }, proc_exit(c) { throw new Error('exit ' + c); } }, { get: (t, k) => t[k] || (() => 0) });
const { instance } = await WebAssembly.instantiate(fs.readFileSync('tools/mapgen/.cache/engine-v2_0_0.wasm'), { wasi_snapshot_preview1: wasi });
const X = instance.exports; mem = X.memory; if (X._initialize) X._initialize();
const out = X.Engine_Malloc(64);
const dir = process.argv[3] || 'maps'; const res = {};
for (const f of fs.readdirSync(dir).filter((f) => f.endsWith('.map26a'))) {
  const bytes = fs.readFileSync(path.join(dir, f));
  const p = X.Engine_Malloc(bytes.length); new Uint8Array(mem.buffer, p, bytes.length).set(bytes);
  if (X.MapBuilder_FromFileBytes(p, bytes.length, out) !== 0) { console.error('fail', f); continue; }
  const M = dv().getBigUint64(out, true);
  X.MapBuilder_GetBitboardMetadata(M, out); const W = dv().getInt32(out, true), H = dv().getInt32(out + 4, true);
  const get = (fn, x, y) => { X[fn](M, x, y, out); return dv().getUint8(out); };
  const rows = [];
  for (let y = 0; y < H; y++) { let s = ''; for (let x = 0; x < W; x++) s += get('MapBuilder_GetWall', x, y) ? '#' : get('MapBuilder_GetHole', x, y) ? 'o' : get('MapBuilder_GetAltar', x, y) ? 'A' : '.'; rows.push(s); }
  X.MapBuilder_GetTeamASpawnArea(M, out); const spawnA = [0, 4, 8, 12].map((o) => dv().getInt32(out + o, true));
  X.MapBuilder_GetNumChampsPerTeam(M, out); const S = dv().getUint32(out, true);
  res[f.replace(/\.map26a$/, '')] = { W, H, S, spawnA, rows };
}
fs.writeFileSync(process.argv[2], JSON.stringify(res));
console.log(Object.keys(res).length, 'maps');
