// Proof of concept (14 Oct): decode a replay with the visualiser's own engine.wasm
// (the same file tools/mapgen/fetch.mjs caches). A downloaded .repl26a is a zip;
// unzip it first and pass the inner replay.repl26a.
// usage: node tools/replay/poc.mjs tools/mapgen/.cache/engine.wasm DIR/replay.repl26a
// Layout copied from the visualiser bundle (timeline snapshot, 40152 bytes).
// Checked against --statistics on a starter game: picks, gems, end round, winner match.
import fs from 'node:fs';

const [wasmPath, replayPath] = process.argv.slice(2);
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
const { instance } = await WebAssembly.instantiate(fs.readFileSync(wasmPath), { wasi_snapshot_preview1: wasi });
const X = instance.exports; mem = X.memory;
if (X._initialize) X._initialize();
const cstr = (p) => { const u = new Uint8Array(mem.buffer); let e = p; while (u[e]) e++; return Buffer.from(u.subarray(p, e)).toString(); };
const check = (rc) => { if (rc !== 0) throw new Error('engine error ' + rc + ': ' + cstr(X.GetLastErrorMsg())); };
const outBuf = X.Engine_Malloc(64);
const bytes = fs.readFileSync(replayPath);
const p = X.Engine_Malloc(bytes.length);
new Uint8Array(mem.buffer, p, bytes.length).set(bytes);
check(X.Game_FromReplayFileBytes(p, bytes.length, outBuf));
const H = dv().getBigUint64(outBuf, true);
check(X.Game_Visualiser_Timeline_GetMain(H, outBuf));
const main = dv().getBigUint64(outBuf, true);
const args = X.Engine_Malloc(128);
check(X.Game_Visualiser_Timeline_Info(H, main, args, args + 8, args + 16));
const size = dv().getUint32(args, true);
console.error('timeline size', size, 'snapshot', X.Game_Visualiser_TimelineSnapshotSize());
const SNAP = 40152, R = 120;
const tp = X.Engine_Malloc(SNAP);
check(X.Game_Visualiser_Timeline_Seek(H, main, 0, 0));

function decode() {
  check(X.Game_Visualiser_ReadTimelineState(H, tp));
  const e = dv(), t = tp, u = (n) => e.getUint32(t + n, true), i = (n) => e.getInt32(t + n, true), f = (n) => e.getFloat32(t + n, true);
  const drafts = [[], []];
  for (let a = 0; a < 2; a++) for (let b = 0; b < 5; b++) drafts[a].push(i(R + 12 + a * 20 + b * 4));
  const arr = (co, d, stride, cap, fn) => { const n = u(co); const r = []; for (let k = 0; k < Math.min(n, cap); k++) r.push(fn(d + k * stride)); return r; };
  return {
    round: u(8), team: u(16), awaitingInput: !!u(20), phase: u(24), outcome: u(28),
    gemsA: Number(e.getBigUint64(t + 32, true)), gemsB: Number(e.getBigUint64(t + 40, true)),
    inputPosition: u(56), substep: u(104), stepKind: u(68), actor: [u(72), u(76)],
    from: [i(80), i(84)], to: [i(88), i(92)], stepRound: u(96), drafts,
    champions: arr(172, 196, 252, 16, (n) => ({ idx: u(n + 4), team: u(n + 8), type: u(n + 12), x: i(n + 16), y: i(n + 20), hp: f(n + 24), maxHp: f(n + 28), alive: !!u(n + 32), gold: u(n + 36), gems: u(n + 40), kills: u(n + 44), items: Array.from({ length: 42 }, (_, k) => u(n + 48 + k * 4)) })),
    camps: arr(176, 4228, 28, 500, (n) => ({ idx: u(n + 4), team: u(n + 8), type: u(n + 12), x: i(n + 16), y: i(n + 20), hp: f(n + 24) })),
    groups: arr(180, 18228, 8, 500, (n) => ({ reward: !!u(n), capture: u(n + 4) })),
    wards: arr(184, 22228, 8, 128, (n) => ({ team: u(n) })),
  };
}

let s = decode(), steps = 0, last = -1;
const kinds = {};
for (;;) {
  kinds[s.stepKind] = (kinds[s.stepKind] || 0) + 1;
  if (s.round !== last && s.round % 250 === 0) {
    console.log(`r${s.round} gems A ${s.gemsA} B ${s.gemsB} draft ${JSON.stringify(s.drafts)} champs ${s.champions.map((c) => `${c.team}:${c.type}@${c.x},${c.y} hp${c.hp.toFixed(0)} g${c.gems} $${c.gold}`).join(' | ')}`);
  }
  last = s.round;
  if (s.outcome || (s.awaitingInput && s.inputPosition >= size)) break;
  check(X.Game_Visualiser_Timeline_ReplayNext(H, 1));
  s = decode(); steps++;
}
console.log('end round', s.round, 'outcome', s.outcome, 'gems', s.gemsA, s.gemsB, 'steps', steps, 'stepKinds', JSON.stringify(kinds));
console.log('camps', s.camps.length, 'groups', s.groups.length, 'wards', s.wards.length);
