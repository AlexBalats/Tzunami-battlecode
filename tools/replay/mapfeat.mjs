import fs from 'node:fs';
import path from 'node:path';
const enginePath = process.argv[2];
const dir = process.argv[3];
const CAMP = ['WOLF', 'ELK', 'GEM_CLUSTER', 'GOLD_CLUSTER', 'MONOLITH', 'GOLEM'];
// ---- engine -------------------------------------------------------------
let mem;
const dv = () => new DataView(mem.buffer);
const wasi = {
  random_get(p, n) { new Uint8Array(mem.buffer, p, n).fill(7); return 0; },
  environ_sizes_get(a, b) { dv().setUint32(a, 0, true); dv().setUint32(b, 0, true); return 0; },
  environ_get() { return 0; },
  fd_close() { return 0; },
  fd_fdstat_get(fd, p) { dv().setUint8(p, 2); return 0; },
  fd_prestat_get() { return 8; }, fd_prestat_dir_name() { return 8; },
  fd_read(fd, a, b, n) { dv().setUint32(n, 0, true); return 0; },
  fd_seek() { return 70; },
  fd_write(fd, iov, cnt, out) {
    let t = 0;
    for (let i = 0; i < cnt; i++) { const p = dv().getUint32(iov + i * 8, true), l = dv().getUint32(iov + i * 8 + 4, true); process.stderr.write(Buffer.from(mem.buffer, p, l)); t += l; }
    dv().setUint32(out, t, true); return 0;
  },
  proc_exit(c) { throw new Error('exit ' + c); },
};
const { instance } = await WebAssembly.instantiate(fs.readFileSync(enginePath), { wasi_snapshot_preview1: wasi });
const X = instance.exports; mem = X.memory;
if (X._initialize) X._initialize();
const cstr = (p) => { const u = new Uint8Array(mem.buffer); let e = p; while (u[e]) e++; return Buffer.from(u.subarray(p, e)).toString(); };
const check = (rc) => { if (rc !== 0) throw new Error('engine error ' + rc + ': ' + cstr(X.GetLastErrorMsg())); };
const outBuf = X.Engine_Malloc(64);
const args = X.Engine_Malloc(128);

function load(bytes, replay) {
  const p = X.Engine_Malloc(bytes.length);
  new Uint8Array(mem.buffer, p, bytes.length).set(bytes);
  check(replay ? X.Game_FromReplayFileBytes(p, bytes.length, outBuf) : X.Game_FromMapFileBytes(p, bytes.length, outBuf, 0));
  X.Engine_Free(p);
  return dv().getBigUint64(outBuf, true);
}
const u32 = (H, fn, ...a) => { check(X[fn](H, ...a, outBuf)); return dv().getUint32(outBuf, true); };

function layout(H) {
  check(X.Game_GetBitboardMetadata(H, outBuf));
  const w = dv().getInt32(outBuf, true), h = dv().getInt32(outBuf + 4, true);
  const nc = u32(H, 'Game_GetNumCamps');
  const camps = [];
  const handles = new Map();
  for (let i = 0; i < nc; i++) {
    check(X.Game_GetCampHandle(H, i, outBuf));
    const ch = dv().getBigUint64(outBuf, true);
    handles.set(ch, i);
    check(X.Game_GetCamp(H, ch, outBuf));
    camps.push({ i, type: dv().getInt32(outBuf, true), x: dv().getInt32(outBuf + 4, true), y: dv().getInt32(outBuf + 8, true), group: -1 });
  }
  const ng = u32(H, 'Game_GetNumCampGroups');
  const groups = [];
  for (let g = 0; g < ng; g++) {
    check(X.Game_GetCampGroupHandle(H, g, outBuf));
    const gh = dv().getBigUint64(outBuf, true);
    check(X.Game_GetCampGroup(H, gh, outBuf));
    const gr = { i: g, gem: dv().getUint32(outBuf, true), gold: dv().getUint32(outBuf + 4, true), cooldown: dv().getUint32(outBuf + 8, true), camps: [] };
    const n = dv().getUint32(outBuf + 12, true);
    for (let j = 0; j < n; j++) {
      check(X.Game_GetCampGroupCamp(H, gh, j, outBuf));
      const c = handles.get(dv().getBigUint64(outBuf, true)) ?? -1;
      gr.camps.push(c);
      if (camps[c]) camps[c].group = g;
    }
    groups.push(gr);
  }
  check(X.Game_GetTeamASpawnArea(H, outBuf));
  const spawnA = [0, 4, 8, 12].map((o) => dv().getInt32(outBuf + o, true));
  return { w, h, camps, groups, spawnA };
}


const out = {};
for (const f of fs.readdirSync(dir).filter((f) => f.endsWith('.map26a'))) {
  const H = load(fs.readFileSync(path.join(dir, f)), false); const L = layout(H);
  out[f.replace('.map26a', '')] = { w: L.w, h: L.h, camps: L.camps.map((c) => [CAMP[c.type] ?? c.type, c.x, c.y, c.group]), groups: L.groups.map((g) => ({ gem: g.gem, gold: g.gold, cd: g.cooldown, n: g.camps.length })) };
  X.Game_Destroy(H);
}
fs.writeFileSync(process.argv[4], JSON.stringify(out));
