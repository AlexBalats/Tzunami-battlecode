// Decode a replay into a JSON timeline, using the visualiser's own engine.wasm.
//
//   node tools/replay/decode.mjs REPLAY [OUT.json] [--engine PATH] [--maps DIR]
//
// REPLAY is the inner replay.repl26a (raw, starts with "a62per"). OUT defaults to stdout.
// The engine is picked from the replay's version byte: tools/mapgen/.cache/engine.wasm for cambc 2.1.x replays
// (tools/mapgen/fetch.mjs), engine-v0_0_2.wasm for 2.2.0-2.2.2, engine-v0_0_3.wasm for 2.2.4 (ladder, 16 Oct);
// tools/replay/fetch-engine.sh saves every engine the installed cambc's visualiser ships.
// The map is matched against maps/*.map26a by size and camp layout (else "unknown").
//
// Layouts are copied from the visualiser bundle (cambc 2.1.6, timeline snapshot 40152 bytes).
// Output:
//   meta:    map, size, picks per team, winner, end round, banked gems
//   camps:   [{i, type, x, y, group}], groups: [{i, gem, gold, camps}]  (the map file: one HALF of the map)
//   scamps:  the full map's camps [idx, type, x, y] as the engine numbers them (idx = file camp * 2 + k,
//            k = 1 the mirror); groups are their cardinally connected sets (report.py full_groups)
//   rounds:  per round (state at the end of the round): r, banked [A,B], champs [[idx,x,y,hp,alive,gold,gems,kills]],
//            campHp (by scamps idx), cap (per group: reward + 2 * capture; capture 0 = A, 1 = B, 2 = none), wards
//   champs:  [{i, team, type, name, items (final)}]
//   events:  [round, kind, actor, extra...] for attacks, casts, recalls, submits, shop, wards,
//            consumables, deaths, captures, banked gems, fuel rollovers
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..', '..');
const argv = process.argv.slice(2);
const opt = (k, d) => { const i = argv.indexOf(k); if (i < 0) return d; const v = argv[i + 1]; argv.splice(i, 2); return v; };
const engineOpt = opt('--engine', null);
const mapsDir = opt('--maps', path.join(ROOT, 'maps'));
const [replayPath, outPath] = argv;
// Byte 10 of a raw replay is the engine's minor version: 1 = cambc 2.1.x (engine 0.0.1, tools/mapgen/fetch.mjs
// saves it as engine.wasm), 2 = cambc 2.2.x (engine 0.0.2, engine-v0_0_2.wasm from the 2.2.2 visualiser).
// Bytes 8-10 are the engine version major.minor.patch: cambc 3.0.1 replays are engine 1.0.0 (engine-v1_0_0.wasm).
const ev = fs.readFileSync(replayPath).subarray(8, 11);
const engineMinor = ev[2];
const engineName = ev.join('_') === '0_0_1' ? 'engine.wasm' : `engine-v${ev.join('_')}.wasm`;
const enginePath = engineOpt || path.join(ROOT, 'tools/mapgen/.cache', engineName);
if (!fs.existsSync(enginePath)) throw new Error(`no ${enginePath} for engine ${ev.join('.')}: run sh tools/replay/fetch-engine.sh`);
if (!replayPath) { console.error('usage: node tools/replay/decode.mjs REPLAY [OUT.json]'); process.exit(2); }

export const CHAMP = ['Ryth', 'VesperVale', 'Vendetta', 'Cassi', 'Issac', 'Stellar', 'Prism', 'Marcella', 'Willow', 'Ren', 'Varg', 'Tavi', 'HeartOfRuin'];
export const DRAFT = ['Ryth', 'VesperVale', 'Vendetta', 'CassiAndIssac', 'Stellar', 'Prism', 'Marcella', 'Willow', 'Ren', 'Varg', 'Tavi', 'HeartOfRuin'];
export const CAMP = ['WOLF', 'ELK', 'GEM_CLUSTER', 'GOLD_CLUSTER', 'MONOLITH'];
export const STEP = 'Phase.Respawn.Capture.Tick.Move.Attack.Cast ability.Input.End turn.Set priority..Recall.Submit gems.Shop.Place ward.Consumable.Cancel channel.Sandbox.Gems submitted.Draft champion.Place altar lock.Teleport channel.Teleport complete.Movement blocked.Resign.Sell item.Turn rollover'.split('.');
export const ITEMS = 'Monster Shard of Strength.Monster Emblem of Strength.Monster Shard of Focus.Monster Emblem of Focus.Monster Shard of Health.Monster Emblem of Health.Power Shard of Strength.Power Emblem of Strength.Power Shard of Focus.Power Emblem of Focus.Power Shard of Health.Power Emblem of Health.Durability Shard of Strength.Durability Emblem of Strength.Durability Shard of Focus.Durability Emblem of Focus.Durability Shard of Health.Durability Emblem of Health.Treasure Shard of Strength.Treasure Emblem of Strength.Treasure Shard of Focus.Treasure Emblem of Focus.Treasure Shard of Health.Treasure Emblem of Health.Jungle Shard of Strength.Jungle Emblem of Strength.Jungle Shard of Focus.Jungle Emblem of Focus.Jungle Shard of Health.Jungle Emblem of Health.Home Shard of Strength.Home Emblem of Strength.Home Shard of Focus.Home Emblem of Focus.Home Shard of Health.Home Emblem of Health.Bruiser Shard of Strength.Bruiser Emblem of Strength.Bruiser Shard of Focus.Bruiser Emblem of Focus.Bruiser Shard of Health.Bruiser Emblem of Health'.split('.');
export const CONSUMABLES = ['Teleport crystal', 'Control ward', 'Altar lock', 'TP scroll'];

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

function sig(l) { return `${l.w}x${l.h}:` + l.camps.map((c) => `${c.type}@${c.x},${c.y}`).sort().join(';'); }
function matchMap(l) {
  const want = sig(l);
  let best = 'unknown';
  if (!fs.existsSync(mapsDir)) return best;
  for (const f of fs.readdirSync(mapsDir).filter((f) => f.endsWith('.map26a'))) {
    try {
      const H = load(fs.readFileSync(path.join(mapsDir, f)), false);
      if (sig(layout(H)) === want) best = f.replace(/\.map26a$/, '');
      X.Game_Destroy(H);
    } catch (e) { /* not a loadable map */ }
  }
  return best;
}

// ---- replay ---------------------------------------------------------------
const H = load(fs.readFileSync(replayPath), true);
const L = layout(H);
const mapName = matchMap(L);
check(X.Game_Visualiser_Timeline_GetMain(H, outBuf));
const main = dv().getBigUint64(outBuf, true);
check(X.Game_Visualiser_Timeline_Info(H, main, args, args + 8, args + 16));
const size = dv().getUint32(args, true);
if (X.Game_Visualiser_TimelineSnapshotSize() !== 40152) throw new Error('unsupported snapshot layout');
const SNAP = 40152, R = 120;
const tp = X.Engine_Malloc(SNAP);
check(X.Game_Visualiser_Timeline_Seek(H, main, 0, 0));

function decode() {
  check(X.Game_Visualiser_ReadTimelineState(H, tp));
  const e = dv(), t = tp, u = (n) => e.getUint32(t + n, true), i = (n) => e.getInt32(t + n, true), f = (n) => e.getFloat32(t + n, true);
  const drafts = [[], []];
  for (let a = 0; a < 2; a++) for (let b = 0; b < 5; b++) drafts[a].push(i(R + 12 + a * 20 + b * 4));
  const arr = (co, d, stride, cap, fn) => { const n = u(co); const r = []; for (let k = 0; k < Math.min(n, cap); k++) r.push(fn(d + k * stride)); return r; };
  const slot = u(108);
  return {
    round: u(8), awaitingInput: !!u(20), phase: u(24), outcome: u(28),
    banked: [Number(e.getBigUint64(t + 32, true)), Number(e.getBigUint64(t + 40, true))],
    inputPosition: u(56),
    step: { phase: u(64), kind: u(68), actorKind: u(72), actor: u(76), from: [i(80), i(84)], to: [i(88), i(92)], round: u(96), substep: u(104), slot: slot === 4294967295 ? -1 : slot },
    drafts,
    champions: arr(172, 196, 252, 16, (n) => ({ idx: u(n + 4), team: u(n + 8), type: u(n + 12), x: i(n + 16), y: i(n + 20), hp: f(n + 24), maxHp: f(n + 28), alive: !!u(n + 32), gold: u(n + 36), gems: u(n + 40), kills: u(n + 44), items: Array.from({ length: ITEMS.length }, (_, k) => u(n + 48 + k * 4)), cons: Array.from({ length: 4 }, (_, k) => u(n + 216 + k * 4)) })),
    camps: arr(176, 4228, 28, 500, (n) => ({ idx: u(n + 4), team: u(n + 8), type: u(n + 12), x: i(n + 16), y: i(n + 20), hp: f(n + 24) })),
    groups: arr(180, 18228, 8, 500, (n) => ({ reward: !!u(n), capture: u(n + 4) })),
    wards: arr(184, 22228, 8, 128, (n) => ({ team: u(n) })),
  };
}

const r1 = (v) => Math.round(v);
const events = [];
const rounds = [];
let prev = decode();
let steps = 0;
let scamps = null; // full-map camps [idx, type, x, y] (the map file holds one half)
const champMeta = new Map();
const ACT = new Set([5, 6, 11, 12, 13, 14, 15, 16, 18, 20, 21, 22, 24, 25, 26]);

function targetAt(s, x, y) {
  const c = s.champions.find((c) => c.alive && c.x === x && c.y === y);
  if (c) return ['C', c.idx];
  const m = s.camps.find((m) => m.x === x && m.y === y);
  if (m) return ['M', m.idx];
  return ['T', x, y];
}

for (;;) {
  if (prev.outcome || (prev.awaitingInput && prev.inputPosition >= size)) break;
  check(X.Game_Visualiser_Timeline_ReplayNext(H, 1));
  const s = decode(); steps++;
  const st = s.step, rd = s.phase === 12 ? 0 : s.round;
  for (const c of s.champions) if (!champMeta.has(c.idx)) champMeta.set(c.idx, { i: c.idx, team: c.team, type: c.type, name: CHAMP[c.type] });

  if (ACT.has(st.kind) && (st.substep === 0 || (st.kind === 18 && (s.banked[0] !== prev.banked[0] || s.banked[1] !== prev.banked[1])))) {
    const ev = [rd, STEP[st.kind], st.actorKind === 1 ? st.actor : `${st.actorKind}:${st.actor}`];
    if (st.kind === 5 || st.kind === 6) { ev.push(...targetAt(s, st.to[0], st.to[1])); if (st.kind === 6) ev.push('slot' + st.slot); }
    if (st.kind === 13 || st.kind === 25) {
      const a = prev.champions.find((c) => c.idx === st.actor), b = s.champions.find((c) => c.idx === st.actor);
      if (a && b) {
        const sign = st.kind === 13 ? 1 : -1;
        const k = b.items.findIndex((v, j) => (v - a.items[j]) * sign > 0);
        const q = b.cons.findIndex((v, j) => (v - a.cons[j]) * sign > 0);
        ev.push(k >= 0 ? ITEMS[k] : q >= 0 ? CONSUMABLES[q] : '?', b.gold);
      }
    }
    if (st.kind === 18) ev.push(s.banked[0] - prev.banked[0], s.banked[1] - prev.banked[1]);
    if (st.kind === 12 || st.kind === 11) { const c = s.champions.find((c) => c.idx === st.actor); if (c) ev.push(c.gems, c.x, c.y); }
    if (st.kind === 14) ev.push(st.to[0], st.to[1]);
    events.push(ev);
  }
  // deaths and kills from state diffs
  const pm = new Map(prev.champions.map((c) => [c.idx, c]));
  for (const c of s.champions) {
    const p = pm.get(c.idx);
    if (!p) continue;
    if (p.alive && !c.alive) {
      const killers = s.champions.filter((k) => k.kills > (pm.get(k.idx)?.kills ?? 0)).map((k) => k.idx);
      events.push([rd, 'Death', c.idx, p.gems, p.x, p.y, killers, `${STEP[st.kind]}:${st.actorKind}:${st.actor}`]);
    }
  }
  for (let g = 0; g < s.groups.length; g++) {
    const a = prev.groups[g], b = s.groups[g];
    if (a && (a.capture !== b.capture || a.reward !== b.reward)) events.push([rd, 'Group', g, a.reward, b.reward, a.capture, b.capture]);
  }
  if (!scamps && s.camps.length && s.camps.every((m) => m.x >= 0)) scamps = s.camps.map((m) => [m.idx, CAMP[m.type] ?? m.type, m.x, m.y]);
  if (s.round !== prev.round && prev.phase !== 12) {
    rounds.push({
      r: prev.round, banked: prev.banked,
      champs: prev.champions.map((c) => [c.idx, c.x, c.y, r1(c.hp), c.alive ? 1 : 0, c.gold, c.gems, c.kills]),
      campHp: prev.camps.map((m) => r1(m.hp)),
      cap: prev.groups.map((g) => (g.reward ? 1 : 0) + 2 * g.capture),
      wards: prev.wards.length,
    });
  }
  prev = s;
}
const fin = prev;
rounds.push({ r: fin.round, banked: fin.banked, champs: fin.champions.map((c) => [c.idx, c.x, c.y, r1(c.hp), c.alive ? 1 : 0, c.gold, c.gems, c.kills]), campHp: fin.camps.map((m) => r1(m.hp)), cap: fin.groups.map((g) => (g.reward ? 1 : 0) + 2 * g.capture), wards: fin.wards.length });

const out = {
  meta: {
    file: replayPath, map: mapName, w: L.w, h: L.h, spawnA: L.spawnA, steps,
    picks: fin.drafts.map((d) => d.filter((x) => x >= 0).map((x) => DRAFT[x])),
    outcome: fin.outcome, endRound: fin.round, banked: fin.banked,
  },
  camps: L.camps.map((c) => ({ ...c, type: CAMP[c.type] ?? c.type })),
  groups: L.groups,
  champs: [...champMeta.values()].map((m) => { const c = fin.champions.find((c) => c.idx === m.i); return { ...m, items: c ? Object.fromEntries(c.items.map((v, k) => [ITEMS[k], v]).filter(([, v]) => v)) : {}, cons: c?.cons }; }),
  scamps,
  rounds, events,
};
const json = JSON.stringify(out);
if (outPath) fs.writeFileSync(outPath, json); else process.stdout.write(json);
console.error(`${path.basename(path.dirname(replayPath))}/${path.basename(replayPath)}: map ${mapName} ${L.w}x${L.h}, picks ${JSON.stringify(out.meta.picks)}, outcome ${fin.outcome}, round ${fin.round}, banked ${fin.banked}, ${steps} steps, ${events.length} events`);
