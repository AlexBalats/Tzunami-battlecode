// count camps by type per pool map (half file x2), max group camps (file group; self-mirrored groups merge in game)
import fs from 'node:fs'; import path from 'node:path';
const ROOT = '/Users/jacobchau/Desktop/Tzunami-battlecode';
let mem; const dv = () => new DataView(mem.buffer);
const wasi = { random_get(p, n) { new Uint8Array(mem.buffer, p, n).fill(7); return 0; }, environ_sizes_get(a, b) { dv().setUint32(a, 0, true); dv().setUint32(b, 0, true); return 0; }, environ_get() { return 0; }, fd_close() { return 0; }, fd_fdstat_get(fd, p) { dv().setUint8(p, 2); return 0; }, fd_prestat_get() { return 8; }, fd_prestat_dir_name() { return 8; }, fd_read(fd, a, b, n) { dv().setUint32(n, 0, true); return 0; }, fd_seek() { return 70; }, fd_write(fd, iov, cnt, out) { dv().setUint32(out, 0, true); return 0; }, proc_exit(c) { throw new Error('exit ' + c); } };
const { instance } = await WebAssembly.instantiate(fs.readFileSync(ROOT + '/tools/mapgen/.cache/engine-v1_0_3.wasm'), { wasi_snapshot_preview1: wasi });
const X = instance.exports; mem = X.memory; if (X._initialize) X._initialize();
const out = X.Engine_Malloc(64);
const T = ['W', 'E', 'gc', 'Gc', 'M', 'G'];
const tot = {};
for (const f of fs.readdirSync(ROOT + '/maps').filter((f) => f.endsWith('.map26a')).sort()) {
  const b = fs.readFileSync(ROOT + '/maps/' + f); const p = X.Engine_Malloc(b.length); new Uint8Array(mem.buffer, p, b.length).set(b);
  if (X.Game_FromMapFileBytes(p, b.length, out, 0) !== 0) continue; const H = dv().getBigUint64(out, true);
  X.Game_GetBitboardMetadata(H, out); const w = dv().getInt32(out, true), h = dv().getInt32(out + 4, true);
  X.Game_GetNumCamps(H, out); const nc = dv().getUint32(out, true); const c = {};
  for (let i = 0; i < nc; i++) { X.Game_GetCampHandle(H, i, out); const ch = dv().getBigUint64(out, true); X.Game_GetCamp(H, ch, out); const t = T[dv().getInt32(out, true)]; c[t] = (c[t] || 0) + 2; tot[t] = (tot[t] || 0) + 2; }
  X.Game_GetNumCampGroups(H, out); const ng = dv().getUint32(out, true); let mx = 0;
  for (let g = 0; g < ng; g++) { X.Game_GetCampGroupHandle(H, g, out); const gh = dv().getBigUint64(out, true); X.Game_GetCampGroup(H, gh, out); const n = dv().getUint32(out + 12, true); if (n > mx) mx = n; }
  console.log(f.replace('.map26a', '').padEnd(24), `${w}x${h}`.padEnd(8), 'maxFileGroup', String(mx).padEnd(3), JSON.stringify(c));
}
console.log('TOTAL', JSON.stringify(tot));
