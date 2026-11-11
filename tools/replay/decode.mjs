// Decode a .repl26a replay into JSON lines, using the engine's own WASM build and the visualiser's snapshot parser
// (both served by `cambc view`; see tools/replay/README.md).
//
//   node tools/replay/decode.mjs VIS_DIR replay.repl26a > out.jsonl
//
// VIS_DIR holds assets/PanelChrome-*.js and assets/v3.wasm. The replay is the inner replay.repl26a of a bundle.
// Output: one {"t":"round", ...} line per round with every champion's state, and one {"t":"step", ...} line per
// engine step (moves, attacks, casts, end turns) with its actor, from/to and the actor's state after it.
import fs from 'fs';
import path from 'path';
import zlib from 'zlib';

const [VIS, REPLAY] = process.argv.slice(2);
const chrome = fs.readdirSync(path.join(VIS, 'assets')).find((f) => f.startsWith('PanelChrome-') && f.endsWith('.js'));
const P = await import(path.resolve(VIS, 'assets', chrome));
const parseState = P.F, parseHeader = P.P, OMNI = P.T;  // xr, yr and the spectator perspective {team: 2}

let mem;
const wasi = new Proxy({}, {
  get: (_, k) => (...a) => {
    const dv = new DataView(mem.buffer);
    if (k === 'fd_write') {
      let n = 0;
      for (let i = 0; i < a[2]; i++) n += dv.getUint32(a[1] + i * 8 + 4, true);
      dv.setUint32(a[3], n, true);
      return 0;
    }
    if (k === 'environ_sizes_get') { dv.setUint32(a[0], 0, true); dv.setUint32(a[1], 0, true); return 0; }
    if (k === 'random_get') { new Uint8Array(mem.buffer, a[0], a[1]).fill(7); return 0; }
    if (k === 'fd_prestat_get') return 8;
    if (k === 'proc_exit') throw new Error('proc_exit ' + a[0]);
    return 0;
  },
});
const wasmFile = fs.existsSync(path.join(VIS, 'assets', 'v3.wasm')) ? 'v3.wasm' : fs.readdirSync(path.join(VIS, 'assets')).find((f) => f.startsWith('v3_0_0-'));
const inst = new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(VIS, 'assets', wasmFile))),
  { wasi_snapshot_preview1: wasi, deep_wasm: { on_assert_fail_impl: () => 1 } });
const X = inst.exports;
mem = X.memory;
X._initialize();
const dv = () => new DataView(mem.buffer);
const outBuf = X.Engine_Malloc(32);
// A local judge replay is a zip bundle (replay.repl26a + stdout/fuel files): take the inner replay.
function innerReplay(buf) {
  if (buf.readUInt32LE(0) !== 0x04034b50) return buf;
  for (let o = 0; o + 30 < buf.length && buf.readUInt32LE(o) === 0x04034b50;) {
    const method = buf.readUInt16LE(o + 8), csize = buf.readUInt32LE(o + 18);
    const nlen = buf.readUInt16LE(o + 26), xlen = buf.readUInt16LE(o + 28);
    const name = buf.subarray(o + 30, o + 30 + nlen).toString();
    const data = buf.subarray(o + 30 + nlen + xlen, o + 30 + nlen + xlen + csize);
    if (name === 'replay.repl26a') return method === 8 ? zlib.inflateRawSync(data) : data;
    o += 30 + nlen + xlen + csize;
  }
  throw new Error('no replay.repl26a in the bundle');
}
const bytes = innerReplay(fs.readFileSync(REPLAY));
const p = X.Engine_Malloc(bytes.length);
new Uint8Array(mem.buffer, p, bytes.length).set(bytes);
function check(rc, what) {
  if (!rc) return;
  const c = X.GetLastErrorMsg();
  const msg = Buffer.from(new Uint8Array(mem.buffer, c, 400)).toString().split('\0')[0];
  throw new Error(`${what}: engine error ${rc} ${msg}`);
}
check(X.Game_FromReplayFileBytes(p, bytes.length, outBuf), 'load');
const h = dv().getBigUint64(outBuf, true);
const snap = X.Engine_Malloc(X.Game_Visualiser_SnapshotSize());
const args = X.Engine_Malloc(128);
check(X.Game_Visualiser_Timeline_GetMain(h, outBuf), 'timeline');
const tl = dv().getBigUint64(outBuf, true);
check(X.Game_Visualiser_Timeline_Info(h, tl, args, args + 8, args + 16), 'info');
const size = dv().getUint32(args, true);
const pp = args + 48;
dv().setUint32(pp, OMNI.team, true);
dv().setUint32(pp + 4, OMNI.champion, true);

const r1 = (x) => (x === undefined ? null : Math.round(x * 10) / 10);
function champ(c) {
  return {
    i: c.entity.index, tm: c.team, ty: c.type, x: c.position?.x ?? -1, y: c.position?.y ?? -1,
    hp: r1(c.health), mhp: r1(c.maxHealth), al: c.alive ? 1 : 0, gm: c.gems ?? null, gd: c.gold ?? null,
    st: r1(c.strength?.effective), fo: r1(c.focus?.effective), cd: c.cooldowns, bf: (c.buffs || []).map((b) => [b.type, b.timer, r1(b.magnitude)]),
    pr: c.priority ?? null, npr: c.nextPriority ?? null, dro: c.draftOrder ?? null, cht: c.channelTimer ?? null, chy: c.channelType ?? null,  // 10 Nov: scheduling priority (this round / next), draft order, channel
  };
}
const out = [];
let lastRound = -1;
// Seek once, then replay forward one input at a time (seeking each position replays from the start: quadratic).
// ReplayNext advances one substep; a state is emitted once per input position (what Seek(pos, 0) shows).
check(X.Game_Visualiser_Timeline_Seek(h, tl, 0, 0), 'seek');
let lastInput = -1;
for (let it = 0; it < 50 * size + 1000; it++) {
  if (it > 0 && X.Game_Visualiser_Timeline_ReplayNext(h, 1)) break;
  check(X.Game_Visualiser_ReadState(h, pp, snap), 'read');
  const hd = parseHeader(dv(), snap);
  if (hd.inputPosition === lastInput) continue;
  lastInput = hd.inputPosition;
  const st = hd.step;
  if (hd.round !== lastRound && hd.phase !== 12) {
    const s = parseState(dv(), snap);
    out.push(JSON.stringify({ t: 'round', r: hd.round, gems: hd.submittedGems.map(Number), ch: s.champions.map(champ),
      cp: s.camps.filter((c) => c.health > 0 && c.position).map((c) => [c.position.x, c.position.y, Math.round(c.health), c.type]) }));
    lastRound = hd.round;
  }
  if (st.actor.kind === 1) {
    const s = parseState(dv(), snap);
    const a = s.champions.find((c) => c.entity.index === st.actor.index);
    out.push(JSON.stringify({ t: 'step', r: hd.round, k: st.kind, ph: st.phase, a: st.actor.index, f: [st.from.x, st.from.y], to: [st.to.x, st.to.y],
      sub: st.substep, slot: st.abilitySlot ?? null, at: st.abilityType ?? null, pv: st.kind === 9 ? st.priority : undefined, hp: a ? r1(a.health) : null, pos: a?.position ? [a.position.x, a.position.y] : null }));
  }
  if (out.length > 4000) { process.stdout.write(out.join('\n') + '\n'); out.length = 0; }
}
process.stdout.write(out.join('\n') + '\n');
