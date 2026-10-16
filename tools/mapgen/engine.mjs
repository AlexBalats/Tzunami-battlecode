// The official engine's MapBuilder (engine.wasm from the cambc map editor), driven from Node.
// Signatures come from the editor's own JS (cambc 2.1.6). Every call returns 0 on success; else
// GetLastErrorMsg() holds the reason. Get engine.wasm with `node tools/mapgen/fetch.mjs`.
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

export const HERE = path.dirname(fileURLToPath(import.meta.url));
export const WASM = path.join(HERE, '.cache', 'engine.wasm');
export const SYM = { HORIZONTAL: 0, VERTICAL: 1, ROTATIONAL180: 2 };
export const SYM_NAMES = ['HORIZONTAL', 'VERTICAL', 'ROTATIONAL180'];
export const CAMP = { WOLF: 0, ELK: 1, GEM_CLUSTER: 2, GOLD_CLUSTER: 3, MONOLITH: 4 };
export const CAMP_NAMES = ['WOLF', 'ELK', 'GEM_CLUSTER', 'GOLD_CLUSTER', 'MONOLITH'];

export async function load() {
  if (!fs.existsSync(WASM)) throw new Error(`no ${WASM}: run node tools/mapgen/fetch.mjs first`);
  let mem = null;
  const view = () => new DataView(mem.buffer);
  // Minimal WASI: no files, no environment, no randomness (deterministic output).
  const wasi = {
    environ_get: () => 0,
    environ_sizes_get: (c, s) => { view().setUint32(c, 0, true); view().setUint32(s, 0, true); return 0; },
    fd_close: () => 0,
    fd_fdstat_get: () => 8,
    fd_prestat_get: () => 8,
    fd_prestat_dir_name: () => 8,
    fd_read: () => 8,
    fd_seek: () => 8,
    fd_write: (fd, iovs, n, out) => {
      let total = 0;
      for (let i = 0; i < n; i++) {
        const p = view().getUint32(iovs + 8 * i, true), l = view().getUint32(iovs + 8 * i + 4, true);
        process.stderr.write(Buffer.from(mem.buffer, p, l));
        total += l;
      }
      view().setUint32(out, total, true);
      return 0;
    },
    proc_exit: (c) => { throw new Error(`engine exit ${c}`); },
    random_get: (p, n) => { new Uint8Array(mem.buffer, p, n).fill(0); return 0; },
  };
  const cstr = (p) => { const b = new Uint8Array(mem.buffer); let e = p; while (b[e]) e++; return Buffer.from(b.subarray(p, e)).toString(); };
  const imports = {
    wasi_snapshot_preview1: wasi,
    deep_wasm: { on_assert_fail_impl(e, f, l, m) { console.error(`${cstr(f)}:${l}: assertion failed: ${cstr(e)} ${cstr(m)}`); return 1; } },
  };
  const { instance } = await WebAssembly.instantiate(fs.readFileSync(WASM), imports);
  const ex = instance.exports;
  mem = ex.memory;
  ex._initialize();
  const out = ex.Engine_Malloc(32);
  const check = (code, what) => { if (code !== 0) throw new Error(`${what}: engine error ${code}: ${cstr(ex.GetLastErrorMsg())}`); };
  return { ex, view, out, check, mem: () => mem };
}

export class Map26 {
  constructor(E, handle) { this.E = E; this.h = handle; this.meta(); }

  static create(E, w, h, sym) {
    E.check(E.ex.MapBuilder_Create(w, h, SYM[sym] ?? sym, E.out), 'Create');
    return new Map26(E, E.view().getBigUint64(E.out, true));
  }

  static fromBytes(E, bytes) {
    const p = E.ex.Engine_Malloc(bytes.length);
    try {
      new Uint8Array(E.mem().buffer, p, bytes.length).set(bytes);
      E.check(E.ex.MapBuilder_FromFileBytes(p, bytes.length, E.out), 'FromFileBytes');
      return new Map26(E, E.view().getBigUint64(E.out, true));
    } finally { E.ex.Engine_Free(p); }
  }

  meta() {
    const { ex, view, out, check } = this.E;
    check(ex.MapBuilder_GetBitboardMetadata(this.h, out), 'Metadata');
    const v = view();
    this.w = v.getInt32(out, true); this.hgt = v.getInt32(out + 4, true);
    this.stride = v.getUint32(out + 16, true);
    const buf = (f) => { check(ex[f](this.h, out), f); return view().getUint32(out, true); };
    this.bufs = { WALL: buf('MapBuilder_GetWallBuffer'), HOLE: buf('MapBuilder_GetHoleBuffer'),
      ALTAR: buf('MapBuilder_GetAltarBuffer'), BUSH: buf('MapBuilder_GetBushBuffer') };
  }

  is(kind, x, y) {
    const a = (y >> 3) * this.stride + (x >> 3), o = ((y & 7) << 3) + (x & 7);
    return (this.E.view().getBigUint64(this.bufs[kind] + a * 8, true) & (1n << BigInt(o))) !== 0n;
  }

  add(kind, x, y) {
    const f = { WALL: 'MapBuilder_AddWall', HOLE: 'MapBuilder_AddHole', ALTAR: 'MapBuilder_AddAltar', BUSH: 'MapBuilder_AddBush' }[kind];
    this.E.check(this.E.ex[f](this.h, x, y), `${f}(${x},${y})`);
  }

  addCamp(type, x, y) {
    this.E.check(this.E.ex.MapBuilder_AddCamp(this.h, CAMP[type] ?? type, x, y, this.E.out), `AddCamp(${type},${x},${y})`);
  }

  int(f) { this.E.check(this.E.ex[f](this.h, this.E.out), f); return this.E.view().getInt32(this.E.out, true); }
  get symmetry() { return SYM_NAMES[this.int('MapBuilder_GetSymmetry')]; }
  get champs() { return this.int('MapBuilder_GetNumChampsPerTeam'); }
  set champs(n) { this.E.check(this.E.ex.MapBuilder_SetNumChampsPerTeam(this.h, n), 'SetNumChamps'); }

  get spawn() {
    const { ex, view, out, check } = this.E;
    check(ex.MapBuilder_GetTeamASpawnArea(this.h, out), 'GetSpawn');
    const v = view();
    return { minX: v.getInt32(out, true), minY: v.getInt32(out + 4, true), maxX: v.getInt32(out + 8, true), maxY: v.getInt32(out + 12, true) };
  }

  setSpawn(minX, minY, maxX, maxY) {     // max exclusive [measured: editor]
    const { ex, view, out, check } = this.E;
    const v = view();
    v.setInt32(out, minX, true); v.setInt32(out + 4, minY, true); v.setInt32(out + 8, maxX, true); v.setInt32(out + 12, maxY, true);
    check(ex.MapBuilder_SetTeamASpawnArea(this.h, out), `SetSpawn(${minX},${minY},${maxX},${maxY})`);
  }

  camps() {
    const { ex, view, out, check } = this.E;
    check(ex.MapBuilder_GetNumCamps(this.h, out), 'NumCamps');
    const n = view().getUint32(out, true), res = [];
    for (let i = 0; i < n; i++) {
      check(ex.MapBuilder_GetCamp(this.h, i, out), 'GetCamp');
      const v = view();
      res.push({ type: CAMP_NAMES[v.getInt32(out, true)], x: v.getInt32(out + 4, true), y: v.getInt32(out + 8, true) });
    }
    return res;
  }

  groups() {
    const { ex, view, out, check } = this.E;
    check(ex.MapBuilder_GetNumCampGroups(this.h, out), 'NumGroups');
    const n = view().getUint32(out, true), res = [];
    for (let i = 0; i < n; i++) {
      check(ex.MapBuilder_GetCampGroup(this.h, i, out), 'GetCampGroup');
      const v = view();
      res.push({ gems: v.getUint32(out, true), gold: v.getUint32(out + 4, true), cooldown: v.getUint32(out + 8, true), camps: v.getUint32(out + 12, true) });
    }
    return res;
  }

  encode() {
    const { ex, view, out, check } = this.E;
    check(ex.MapBuilder_VerifyIntegrity(this.h), 'VerifyIntegrity');
    check(ex.MapBuilder_Encode(this.h, out, out + 4), 'Encode');
    const p = view().getUint32(out, true), n = view().getUint32(out + 4, true);
    return Buffer.from(new Uint8Array(this.E.mem().buffer, p, n));
  }

  destroy() { this.E.check(this.E.ex.MapBuilder_Destroy(this.h), 'Destroy'); }
}
