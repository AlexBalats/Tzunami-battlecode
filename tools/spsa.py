"""SPSA over the bot's constants (LADDER_P12 §C2; Stockfish / OpenBench tune this way). Each iteration builds
theta + c_k * delta and theta - c_k * delta (delta = random +-1 per constant, in each constant's [lo, hi] scaled to
[0, 1]), plays both vs the bar on the 32 training maps from both sides at the same seed (common random numbers), and
steps on the paired `rate` gradient: theta += a_k * (rate+ - rate-) / (2 c_k delta). a_k = a / (k + 1 + A)^0.602,
c_k = c / (k + 1)^0.101 (Spall's schedules). The 8 held-out maps (tune.HOLDOUT) are never played. Every iteration is
checkpointed, so a stopped run resumes where it stopped.

    python3 -I tools/spsa.py run NAME --params FILE.json [--iters 60] [--a 0.25] [--c 0.15] [--opp cpp-p15] [--bot cpp]
    python3 -I tools/spsa.py show NAME            # theta now, its history, and the overrides to build it
    python3 -I tools/spsa.py clean NAME           # delete the iteration bots

FILE.json: [{"name": "KEEP_HP", "x0": 0.40, "lo": 0.30, "hi": 0.50}, {"name": "NEAR6", "x0": 6, "lo": 4, "hi": 10,
"int": true}, ...]; a name may be an array element (`ROLE_GOLD[0]`). The checkpoint is runs/spsa/NAME.json.
--jobs 2 (JOBS=1 while something else runs). One iteration = 2 x 64 games, ~1 min on the laptop; run in <= 1-hour
chunks (--iters) and resume.
"""
import argparse
import json
import os
import random
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import noise  # noqa: E402
import tune   # noqa: E402

CK = os.path.join(ROOT, 'runs', 'spsa')


def fmt_val(p, u):
    x = p['lo'] + u * (p['hi'] - p['lo'])
    return str(int(round(x))) if p.get('int') else ('%.4g' % x)


def overrides(params, u):
    return ['%s=%s' % (p['name'], fmt_val(p, ui)) for p, ui in zip(params, u)]


def play(name, ovs, seed, base, opp, maps):
    """Build bots/_t_<name> with the overrides, jitter it by `seed`, play it vs opp on maps; the per-cell measures."""
    tune.build(name, ovs, base, quiet=True)
    bot = tune.jittered('_t_' + name, seed)
    run = tune.arena(bot, opp, maps, fresh=True)
    cells = noise.load([run], set(maps))
    shutil.rmtree(run, ignore_errors=True)
    return cells


def run(a):
    os.makedirs(CK, exist_ok=True)
    path = os.path.join(CK, a.name + '.json')
    if os.path.isfile(path):
        st = json.load(open(path)); params = st['params']
        print('resume %s at iteration %d' % (a.name, st['k']))
    else:
        params = json.load(open(a.params))
        u0 = [(p['x0'] - p['lo']) / (p['hi'] - p['lo']) for p in params]
        st = {'params': params, 'u': u0, 'k': 0, 'hist': [], 'a': a.a, 'c': a.c, 'A': a.A, 'opp': a.opp, 'bot': a.bot,
              'seed': random.randrange(1 << 30)}
    tune.OPP = st['opp']
    maps = [m for m in tune.ALLMAPS if m not in tune.HOLDOUT]
    rng = random.Random(st['seed'] + st['k'])
    for _ in range(a.iters):
        k = st['k']
        ak = st['a'] / (k + 1 + st['A']) ** 0.602; ck = st['c'] / (k + 1) ** 0.101
        delta = [rng.choice((-1, 1)) for _ in params]
        up = [min(1, max(0, u + ck * d)) for u, d in zip(st['u'], delta)]
        um = [min(1, max(0, u - ck * d)) for u, d in zip(st['u'], delta)]
        seed = tune.JS8[k % len(tune.JS8)]
        P = play('spsa_%s_p' % a.name, overrides(params, up), seed, st['bot'], st['opp'], maps)
        M = play('spsa_%s_m' % a.name, overrides(params, um), seed, st['bot'], st['opp'], maps)
        keys = sorted(set(P) & set(M))
        dr = sum(P[x]['rate'] - M[x]['rate'] for x in keys) / max(len(keys), 1)
        dw = sum(P[x]['win'] - M[x]['win'] for x in keys) / max(len(keys), 1)
        # the realised perturbation (clamping at the bounds shrinks it): grad_i = dr / (up_i - um_i)
        g = [dr / (p_ - m_) if abs(p_ - m_) > 1e-9 else 0.0 for p_, m_ in zip(up, um)]
        st['u'] = [min(1, max(0, u + ak * gi)) for u, gi in zip(st['u'], g)]
        st['k'] = k + 1
        st['hist'].append({'k': k, 'seed': seed, 'ak': ak, 'ck': ck, 'delta': delta, 'drate': dr, 'dwin': dw,
                           'u': st['u'], 'n': len(keys)})
        json.dump(st, open(path, 'w'), indent=1)
        print('k %3d seed %d  rate+ - rate- %+.3f (win %+.2f, %d cells)  theta %s' % (
            k, seed, dr, dw, len(keys), ' '.join(overrides(params, st['u']))), flush=True)


def show(a):
    st = json.load(open(os.path.join(CK, a.name + '.json'))); params = st['params']
    print('%s: %d iterations' % (a.name, st['k']))
    for p, u in zip(params, st['u']):
        print('  %-18s %8s  (start %s, range %s-%s)' % (p['name'], fmt_val(p, u), p['x0'], p['lo'], p['hi']))
    # the mean theta over the last third (SPSA's iterate is noisy; the average is the estimate to judge)
    h = st['hist'][-max(1, st['k'] // 3):]
    if h:
        ub = [sum(x['u'][i] for x in h) / len(h) for i in range(len(params))]
        print('  averaged over the last %d iterations: %s' % (len(h), ' '.join(overrides(params, ub))))


def clean(a):
    for d in os.listdir(tune.BOTS):
        if d.startswith(('_t_spsa_%s_' % a.name, '__t_spsa_%s_' % a.name)): shutil.rmtree(os.path.join(tune.BOTS, d))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cmd', choices=['run', 'show', 'clean'])
    ap.add_argument('name')
    ap.add_argument('--params')
    ap.add_argument('--iters', type=int, default=60)
    ap.add_argument('--a', type=float, default=0.25)
    ap.add_argument('--c', type=float, default=0.15)
    ap.add_argument('--A', type=float, default=10)
    ap.add_argument('--opp', default='cpp-p15')
    ap.add_argument('--bot', default='cpp')
    a = ap.parse_args()
    {'run': run, 'show': show, 'clean': clean}[a.cmd](a)


if __name__ == '__main__':
    main()
