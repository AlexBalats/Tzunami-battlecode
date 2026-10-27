"""The tuning harness (docs/nav/RND_P11.md §3): build variants of the bot with constants overridden, screen them paired
against the base on all 40 maps with few jitters, promote the survivors to the full jitter run vs the bar (--opp).

    python3 -I tools/tune.py list [--bot cpp]                     every file-scope constant with its value and file:line
    python3 -I tools/tune.py build NAME KEY=VAL [KEY=VAL ...]    bots/_t_NAME = bots/cpp with the overrides
    python3 -I tools/tune.py screen NAME [--js 0,300] [--stop]    the screen (default J 0, 300: 160 games)
    python3 -I tools/tune.py full NAME [--js ...] [--fresh]       the 8-jitter run (640 games), paired; --fresh = the
                                                                  confirmation seeds JSF (never tuned on)
    python3 -I tools/tune.py full NAME --opp pool                 the same against every training opponent (POOL), per
                                                                  opponent, the mean and the worst; --opp holdout = the
                                                                  held-out opponents (HOLDOUT_OPP, judged last); --opp a,b
    python3 -I tools/tune.py base --opp pool [--fresh]            play the base's runs vs each opponent (missing ones only)
                                                                  and print its win % against each (the pool's ladder)
    python3 -I tools/tune.py clean                                delete the variants and the base's jittered copies
    python3 -I tools/tune.py slim runs/arena                      slim every finished run (replays out, stats.json cut)

KEY is a constant's name (`KEEP_HP`), an array element (`ROLE_GOLD[0]`), or `FILE:old=>new` for one exact text edit
in bots/<bot>/src/FILE (it must occur once). A float keeps its `f`. Every override must match exactly once. NAME may
also be a bot folder (e.g. a patched copy).

Both commands play the variant's jittered copies vs the bar (--opp, default cpp-p15) on all 40 maps from both sides and
pair each game with the base's game on the same cell (map, side, jitter). The base (--base, default cpp-p13: the frozen
copy of bots/cpp) is read from the newest finished runs on disk (tools/jitter.sh's) and played only if missing.
--opp may name several opponents (comma list, `pool`, `holdout`; LADDER_P13 §B): each is played and paired on its own,
then the pool's mean delta (equal weight, SE clustered by map over all opponents) and its worst opponent are printed.
They print the paired deltas of tools/noise.py's measures with their SE, then the same split by map stratum (`walled`, `highneed`, `open`,
`hot`: a report only; a subset is never the screen, RND_P11 §1.4). The screen's measure is `rate` (RND_P11 §1.3).
With --stop the screen ends after a jitter once the variant is 2 SE behind (a sequential test).
Replays are deleted and stats.json cut after each run. --jobs 2 (JOBS=1 while something else runs).
"""
import argparse
import glob
import json
import math
import os
import re
import shutil
import statistics as st
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import noise  # noqa: E402

BOTS = os.path.join(ROOT, 'bots')
OPP = 'cpp-p15'   # the bar (--opp); set from the command line in main()
# The opponent pool (LADDER_P13 §D): our frozen builds and our own style bots (spar-*: each pushes one way the ladder
# winners beat us). The climb and the screens use POOL; HOLDOUT_OPP is never climbed on and is judged last
# (validated 25 Oct, LADDER_P13 §D6: jittered p13 wins 50-58 % against the training four; p10 < p11 = p12 < p13 against the
# pool). spar-meta and cpp-port are out: p13 beats them 98 %, no signal
# 27 Oct cleanup (RND_DRAFTS §10): the bar is cpp-p15; the old frozen builds (p4-p12) were deleted (their zips are in
# submissions/). The pool = the previous ladder bot + three style bots; to be re-thought (NEXT_PROMPT_P15_LOSSES.md)
POOL = ['cpp-p13', 'spar-fight', 'spar-pack', 'spar-fish']
HOLDOUT_OPP = ['spar-steal', 'spar-order']
# Seeds (LADDER_P12 §B1): hashed per-turn jitters (J >= HASHED, `jitter_code`). The old fixed jitters were not
# independent: J 50 replayed J 0 in 63 of 80 cells and the old "fresh" set sat next to the default one (J 0 / J 50 shared
# 63 games). Hashed seeds share 4-7 of 80 games with each other and with every old jitter (the floor)
JS8 = [100000 + k for k in range(8)]      # the training seeds: screens, the climb
JSF = [100100 + k for k in range(8)]      # the confirmation seeds: never tuned on
JS_OLD = [0, 300, 700, 1500, 100, 500, 1000, 2500]   # RND_P11's default set (its runs: RND_P11 §1-3)
# strata by map feature, from the draft-time dump and earlier sessions (LOSSES_P10 §6b, TOP_P9 §10.5, TOP_P9 §1).
# Sets for judging only: the bot never reads a map name (CLAUDE.md rule 10)
SETS = {
    'walled': ['00road-of-riches', '01concentrated-wealth', '01gold-rush', '01shortcut', '00great-wall', '00gemfight',
               '01starvation', '00swirl', '00reverse-spiral', '00pilgrimage', '01big-world'],
    'highneed': ['00contest', '00fragment', '00great-wall', '00interlock', '00monolith', '00rows', '00stampede',
                 '00swirl', '01boss-battle', '01broken-curve', '01gold-rush', '01starvation', '01the-farm'],
    'open': ['00expanse', '01big-world', '00lanes', '01fracture', '00rows', '01yellow-brick-road', '01hooks',
             '00elkring'],
    'hot': ['00packs', '00lost-world', '01starfish', '00gem-fields', '00ambush', '00collision', '00corners',
            '00quadrants', '01elk-arena', '00rushbait-v2', '00eight', '00split'],
}
# The screen plays all 40 maps, never a subset: per-map effects differ so much that a random 16-map subset's delta
# wanders by +-0.043 on `rate` (p11's whole effect is +0.055), and a hand-picked 16-map set read p11 at +0.12 (RND_P11
# §1.4). The strata above are a reporting split of the all-map run
# The 8 held-out maps (LADDER_P12 §B1): 2 a stratum, drawn once (random.seed(20261025) over the maps in one stratum
# only). The climb (tools/spsa.py) never plays them; full runs report them on their own line, judged last
HOLDOUT = ['00road-of-riches', '01shortcut', '00monolith', '00fragment', '01yellow-brick-road', '01hooks', '00quadrants',
           '00collision']
# the sprint 2 maps by size (RND_DRAFTS: p13's line loses the 30x30 and the big open ones): the size is in the file name
_S2 = sorted(os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(ROOT, 'maps_sprint2', '*.map26a')))
def _area(m):
    w, h = re.match(r's2-(\d+)x(\d+)_', m).groups(); return int(w) * int(h)
SETS.update({'s2small': [m for m in _S2 if _area(m) <= 1300], 's2mid': [m for m in _S2 if 1300 < _area(m) < 3600],
             's2big': [m for m in _S2 if _area(m) >= 3600]})
MEASURE = 'rate'   # the screen's measure (RND_P11 §1): tributed gems a round, ours minus theirs


def srcs(bot):
    d = os.path.join(BOTS, bot, 'src')
    return [os.path.join(d, f) for f in sorted(os.listdir(d)) if f.endswith(('.h', '.cpp'))]


DECL = re.compile(r'^(?:static\s+)?(?:constexpr|const)\s+[\w:]+\s+(.*?);')   # file scope only (no indent)


def constants(bot):
    out = []
    for p in srcs(bot):
        for i, line in enumerate(open(p), 1):
            if not DECL.match(line): continue
            for body in re.findall(r'(?:constexpr|const)\s+[\w:]+\s+([^;]*);', line):   # every declaration on the line
                for k, v in re.findall(r'(\w+(?:\[\d*\])?)\s*=\s*(\{[^}]*\}|[^,;{]+)', body):
                    out.append((k, v.strip(), os.path.basename(p), i))
    return out


def override(text, key, val, path):
    """Replace KEY's value in a constexpr/const line; returns (text, n, old)."""
    arr = re.match(r'(\w+)\[(\d+)\]$', key)
    n, old = 0, None
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if not DECL.match(line): continue
        if arr:
            name, idx = arr.group(1), int(arr.group(2))
            m = re.search(r'\b%s\[\d*\]\s*=\s*\{([^}]*)\}' % name, line)
            if not m: continue
            items = [x.strip() for x in m.group(1).split(',')]
            old = items[idx]; items[idx] = fmt(old, val)
            lines[i] = line[:m.start(1)] + ' ' + ', '.join(items) + ' ' + line[m.end(1):]
            n += 1
        else:
            m = re.search(r'\b%s\s*=\s*([^,;{]+)' % re.escape(key), line)
            if not m: continue
            old = m.group(1).strip()
            lines[i] = line[:m.start(1)] + fmt(old, val) + line[m.end(1):]
            n += 1
    return '\n'.join(lines), n, old


def fmt(old, val):
    old = old.strip()
    if old.endswith('f') and re.match(r'^-?[\d.]+f$', old):
        v = val if '.' in val else val + '.0'
        return v + 'f'
    return val


def build(name, overrides, base='cpp', quiet=False):
    dest = os.path.join(BOTS, '_t_' + name)
    shutil.rmtree(dest, ignore_errors=True)
    shutil.copytree(os.path.join(BOTS, base), dest, ignore=shutil.ignore_patterns('.cambc', '__pycache__'))
    for ov in overrides:
        if '=>' in ov:   # FILE:old=>new
            f, rest = ov.split(':', 1); old, new = rest.split('=>', 1)
            p = os.path.join(dest, 'src', f); t = open(p).read()
            if t.count(old) != 1: sys.exit('%s: %r occurs %d times' % (f, old, t.count(old)))
            open(p, 'w').write(t.replace(old, new))
            if not quiet: print('  %s: %r -> %r' % (f, old, new))
            continue
        key, val = ov.split('=', 1)
        hits = []
        for p in srcs('_t_' + name):
            t = open(p).read(); t2, n, old = override(t, key, val, p)
            if n: open(p, 'w').write(t2); hits.append((os.path.basename(p), n, old))
        if sum(h[1] for h in hits) != 1: sys.exit('override %s matched %s' % (ov, hits or 'nothing'))
        if not quiet: print('  %s: %s -> %s (%s)' % (key, hits[0][2], val, hits[0][0]))
    return '_t_' + name


def jittered(bot, J):
    """bots/_<bot>_j<J> as tools/jitter.sh makes it (J 0 = the bot itself)."""
    if J == 0: return bot
    n = '_%s_j%d' % (bot, J)
    d = os.path.join(BOTS, n)
    src = os.path.join(BOTS, bot)
    stale = os.path.isdir(d) and os.path.getmtime(d) < max(os.path.getmtime(p) for p in srcs(bot))
    if not os.path.isdir(d) or stale:
        shutil.rmtree(d, ignore_errors=True)
        shutil.copytree(src, d, ignore=shutil.ignore_patterns('.cambc', '__pycache__'))
        p = os.path.join(d, 'src', 'main.cpp'); s = open(p).read()
        a = 'static void turn()\n{\n'
        assert s.count(a) == 1, 'turn() not found'
        open(p, 'w').write(s.replace(a, a + jitter_code(J)))
    return n


HASHED = 100000   # J >= HASHED: a hashed seed k = J - HASHED (LADDER_P12 §B1): each turn burns hash(round, k) mod 3000 steps


def jitter_code(J):
    """The line injected at the top of turn(). A fixed J burns J loop steps a turn; small fixed J replay J 0's game in most
    cells (J 50: 63 of 80, LADDER_P12 §B1), so the seed sets use hashed seeds: a per-turn burn that differs by seed."""
    if J >= HASHED:
        return ('    { unsigned jh = (unsigned)cambc::round_number() * 2654435761u ^ %du * 40503u; jh ^= jh >> 15; jh *= 2246822519u; jh ^= jh >> 13;\n'
                '      volatile unsigned jx = 0; for (unsigned ji = 0; ji < jh %% 3000u; ++ji) jx = jx + ji; }\n' % (J - HASHED + 1))
    return '    { volatile unsigned jx = 0; for (int ji = 0; ji < %d; ++ji) jx = jx + ji; }\n' % J


def arena(a, b, maps, fresh=False):
    cmd = [sys.executable, '-I', os.path.join(ROOT, 'tools', 'arena.py'), a, b, '--jobs', os.environ.get('JOBS', '2')]
    if maps: cmd += ['--maps', ','.join(maps)]
    if fresh: cmd += ['--fresh']   # a cached game writes no folder, so no stats.json to pair
    env = dict(os.environ); env['PATH'] = os.path.join(ROOT, '.venv', 'bin') + os.pathsep + env.get('PATH', '')
    out = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, env=env).stdout
    m = re.search(r'saved (\S+)/summary\.json', out)
    if not m: sys.exit('arena failed:\n' + out[-2000:])
    run = os.path.join(ROOT, m.group(1))
    slim(run)
    return run


def cells(bot, J, maps, opp=None):
    """The games of `bot` jittered by J vs opp (default OPP): from the newest finished runs on disk that hold them, else
    played."""
    opp = opp or OPP
    name = jittered(bot, J)
    want = {(J, mp, sd) for mp in (maps or ALLMAPS) for sd in 'AB'}
    got = {}
    # a run older than the jittered copy's sources played other code (P14: re-judging bots/cpp after an edit reused the
    # pre-edit runs and printed the old result)
    newest = max(os.path.getmtime(p) for p in srcs(name))
    for run in sorted(glob.glob(os.path.join(ROOT, 'runs', 'arena', '%s-vs-%s-*' % (name, opp))), reverse=True):
        if not os.path.isfile(os.path.join(run, 'summary.json')): continue
        if os.path.getmtime(os.path.join(run, 'summary.json')) < newest: continue
        for k, v in noise.load([run], set(maps) if maps else None).items():
            if k in want and k not in got: got[k] = v
        if len(got) == len(want): return got
    got.update(noise.load([arena(name, opp, maps, fresh=True)], set(maps) if maps else None))
    return got


# ARENA_MAPS=maps_sprint2 (as tools/arena.py): every command on that map set instead (RND_DRAFTS: the unseen-map check
# paired over hashed seeds; its runs never pair with the 70-map ones, the map names differ)
ALLMAPS = sorted(os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(ROOT, os.environ.get('ARENA_MAPS', 'maps'), '*.map26a')))


KEEP_TL = {'collectedGems', 'earnedGold', 'submittedGems', 'monsterDamageDone', 'monsterDamageTaken', 'deaths', 'gems'}


def slim(run):
    """Delete the replays and cut each stats.json to what the tools read (1.1 MB -> ~0.1 MB a game). Only a finished run
    (its summary.json written): the arena reads each stats.json after its game, and slimming under it crashed a run."""
    if not os.path.isfile(os.path.join(run, 'summary.json')): return
    for d, _, fs in os.walk(run):
        for f in fs:
            p = os.path.join(d, f)
            if f.endswith('.repl26a'): os.remove(p)
            elif f == 'stats.json':
                s = json.load(open(p))
                if 'events' not in s: continue
                s.pop('events', None); s.pop('heatmaps', None)
                s['championTimelines'] = [t for t in s['championTimelines'] if t['metric'] in KEEP_TL]
                json.dump(s, open(p, 'w'), separators=(',', ':'))


def paired(va, ba, keys, m):
    """The paired delta and its SE clustered by map (LADDER_P12 §B1): a map's cells (both sides, every seed) are one
    unit, so replayed games, the map's own effect and the A/B sides' partial cancelling are counted. It is the SE for
    unseen maps; the iid SE (paired_iid) is 1.1-1.2x smaller on a p11-sized change."""
    d = [va[k][m] - ba[k][m] for k in keys]
    if len(d) < 2: return (d[0] if d else 0.0), float('inf')
    mu = st.mean(d); g = {}
    for k, x in zip(keys, d): g.setdefault(k[-2], []).append(x - mu)   # k = (J, map, side) or (opp, J, map, side)
    G = len(g)
    if G < 2: return mu, st.stdev(d) / math.sqrt(len(d))
    return mu, math.sqrt(sum(sum(xs) ** 2 for xs in g.values()) * G / (G - 1)) / len(d)


def paired_iid(va, ba, keys, m):
    d = [va[k][m] - ba[k][m] for k in keys]
    return st.mean(d), (st.stdev(d) / math.sqrt(len(d)) if len(d) > 1 else float('inf'))


def tail(VA, BA, keys):
    """The left tail (LADDER_P12 §B2): a piece that lifts the mean but fattens the tail goes back for a look. The 10th
    percentile of the per-cell rate, crushed losses (margin <= -600) and the worst stratum's paired rate."""
    q = lambda xs, p: sorted(xs)[int(p * (len(xs) - 1))]
    va = [VA[k]['rate'] for k in keys]; ba = [BA[k]['rate'] for k in keys]
    cv = sum(VA[k]['margin'] <= -600 for k in keys); cb = sum(BA[k]['margin'] <= -600 for k in keys)
    worst = min([(paired(VA, BA, [k for k in keys if k[-2] in S], 'rate')[0], nm) for nm, S in SETS.items() if any(k[-2] in S for k in keys)] or [(0.0, '-')])
    print('  tail: rate p10 %+.3f vs base %+.3f | crushed (margin <= -600) %d vs %d of %d | worst stratum %s %+.3f' % (
        q(va, .1), q(ba, .1), cv, cb, len(keys), worst[1], worst[0]))


def screen(name, maps, js, stop, base='cpp-p15', opps=None):
    var = name if os.path.isdir(os.path.join(BOTS, name)) else '_t_' + name   # a bot folder, or a variant from `build`
    if opps and len(opps) > 1: return pool(var, maps, js, base, opps)
    if opps: global OPP; OPP = opps[0]
    VA, BA = {}, {}
    for J in js:
        VA.update(cells(var, J, maps)); BA.update(cells(base, J, maps))
        keys = sorted(set(VA) & set(BA))
        dm, se = paired(VA, BA, keys, MEASURE); dw, sw = paired(VA, BA, keys, 'win')
        print('  J%-5d %3d cells  %s %+.3f ± %.3f  win %+.1f ± %.1f pts' % (J, len(keys), MEASURE, dm, se, 100 * dw, 100 * sw), flush=True)
        if stop and len(keys) >= 32 and dm + 2 * se < 0:
            print('  stopped: 2 SE behind'); break
    keys = sorted(set(VA) & set(BA))
    noise.report(VA, BA, 2.0, label='%s vs %s, ' % (var, base))
    for m in (MEASURE, 'win'):
        dm, se = paired(VA, BA, keys, m); _, si = paired_iid(VA, BA, keys, m); f = 100 if m == 'win' else 1
        print('  %-5s %+.4g ± %.4g (map-clustered SE; iid %.4g)  = %.1f SE' % (m, f * dm, f * se, f * si, dm / se if se else 0))
    tail(VA, BA, keys)
    for nm, S in list(SETS.items()) + [('holdout', HOLDOUT)]:
        ks = [k for k in keys if k[1] in S]
        if len(ks) > 1:
            dm, se = paired(VA, BA, ks, MEASURE); dw, sw = paired(VA, BA, ks, 'win')
            print('  %-8s %3d cells  %s %+.3f ± %.3f  win %+.1f ± %.1f pts' % (nm, len(ks), MEASURE, dm, se, 100 * dw, 100 * sw))
    return VA, BA


def pool(var, maps, js, base, opps):
    """The variant and the base vs each opponent (LADDER_P13 §B): per opponent the paired deltas; then the pool's mean
    (equal cells per opponent, so the mean of the cells is the mean of the opponents; SE clustered by map over all of
    them: one map's cells against every opponent are one unit), the worst opponent, the tail, strata and held-out maps."""
    VA, BA, per = {}, {}, []
    for o in opps:
        va, ba = {}, {}
        for J in js:
            va.update(cells(var, J, maps, o)); ba.update(cells(base, J, maps, o))
        keys = sorted(set(va) & set(ba))
        dm, se = paired(va, ba, keys, MEASURE); dw, sw = paired(va, ba, keys, 'win')
        wv = 100 * st.mean(va[k]['win'] for k in keys); wb = 100 * st.mean(ba[k]['win'] for k in keys)
        cv = sum(va[k]['margin'] <= -600 for k in keys); cb = sum(ba[k]['margin'] <= -600 for k in keys)
        per.append((o, dm, se, dw, sw))
        print('  vs %-12s %3d cells  %s %+.3f ± %.3f  win %+.1f ± %.1f pts  (win %% %.1f vs base %.1f; crushed %d vs %d)' % (
            o, len(keys), MEASURE, dm, se, 100 * dw, 100 * sw, wv, wb, cv, cb), flush=True)
        VA.update({(o,) + k: va[k] for k in keys}); BA.update({(o,) + k: ba[k] for k in keys})
    keys = sorted(set(VA) & set(BA))
    print('%s vs %s over %d opponents (%s), %d paired cells' % (var, base, len(opps), ', '.join(opps), len(keys)))
    for m in (MEASURE, 'win', 'deaths'):
        dm, se = paired(VA, BA, keys, m); f = 100 if m == 'win' else 1
        print('  pool mean %-6s %+.4g ± %.4g (map-clustered over all opponents)  = %.1f SE' % (m, f * dm, f * se, dm / se if se else 0))
    w = min(per, key=lambda x: x[1])
    print('  worst opponent: %s  %s %+.3f ± %.3f  win %+.1f ± %.1f pts' % (w[0], MEASURE, w[1], w[2], 100 * w[3], 100 * w[4]))
    tail(VA, BA, keys)
    for nm, S in list(SETS.items()) + [('holdout', HOLDOUT)]:
        ks = [k for k in keys if k[-2] in S]
        if len(ks) > 1:
            dm, se = paired(VA, BA, ks, MEASURE); dw, sw = paired(VA, BA, ks, 'win')
            print('  %-8s %4d cells  %s %+.3f ± %.3f  win %+.1f ± %.1f pts' % (nm, len(ks), MEASURE, dm, se, 100 * dw, 100 * sw))
    return VA, BA


def opp_list(s):
    """--opp: a name, a comma list, `pool` (the training opponents) or `holdout` (the held-out ones)."""
    out = []
    for x in s.split(','):
        out += POOL if x == 'pool' else HOLDOUT_OPP if x == 'holdout' else [x]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cmd', choices=['list', 'build', 'screen', 'full', 'base', 'clean', 'slim'])
    ap.add_argument('name', nargs='?')
    ap.add_argument('kv', nargs='*')
    ap.add_argument('--bot', default='cpp')
    ap.add_argument('--base', default='cpp-p15', help='the paired base (a frozen copy of the bot the variants come from)')
    ap.add_argument('--opp', default='cpp-p15', help='the bar every game is played against: a name, a comma list, pool, holdout')
    ap.add_argument('--fresh', action='store_true', help='the fresh seeds JSF (confirmation) instead of JS8')
    ap.add_argument('--maps', default='all')
    ap.add_argument('--js', default=None)
    ap.add_argument('--stop', action='store_true')
    a = ap.parse_args()
    global OPP
    opps = opp_list(a.opp)
    OPP = opps[0]
    if a.cmd == 'list':
        for k, v, f, i in constants(a.bot): print('%-22s %-14s %s:%d' % (k, v, f, i))
    elif a.cmd == 'build':
        build(a.name, a.kv, a.bot)
    elif a.cmd in ('screen', 'full'):
        S8 = JSF if a.fresh else JS8
        js = [int(x) for x in a.js.split(',')] if a.js else (S8 if a.cmd == 'full' else S8[:2])
        maps = None if a.cmd == 'full' or a.maps == 'all' else (SETS[a.maps] if a.maps in SETS else a.maps.split(','))
        screen(a.name, maps, js, a.stop and a.cmd == 'screen', a.base, opps)
    elif a.cmd == 'base':   # the base's runs vs each opponent, and its win % against each
        S8 = JSF if a.fresh else JS8
        js = [int(x) for x in a.js.split(',')] if a.js else S8
        bot = a.name or a.base
        for o in opps:
            c = {}
            for J in js: c.update(cells(bot, J, None, o))
            ks = sorted(c); w = [c[k]['win'] for k in ks]
            g = {}
            for k in ks: g.setdefault(k[1], []).append(c[k]['win'])
            se = math.sqrt(sum((sum(x) - len(x) * st.mean(w)) ** 2 for x in g.values()) * len(g) / max(1, len(g) - 1)) / len(ks)
            print('  %s vs %-12s %3d games  win %.1f %% ± %.1f (map-clustered)  rate %+.3f  deaths %.1f' % (
                bot, o, len(ks), 100 * st.mean(w), 100 * se, st.mean(c[k]['rate'] for k in ks), st.mean(c[k]['deaths'] for k in ks)), flush=True)
    elif a.cmd == 'slim':   # name = a runs folder: slim every run in it
        for d in sorted(os.listdir(a.name)):
            if '-vs-' in d: slim(os.path.join(a.name, d))
    elif a.cmd == 'clean':
        for d in os.listdir(BOTS):
            if d.startswith(('_t_', '__t_')) or re.match(r'_%s_j\d+$' % re.escape(a.base), d): shutil.rmtree(os.path.join(BOTS, d))


if __name__ == '__main__':
    main()
