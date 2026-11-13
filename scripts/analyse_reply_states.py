"""Exploratory post-coding analyses on the deposited labels: four states, A->B transitions,
2x2 interaction on complete cells, reply length. Exploratory, no new labels."""
import csv, re, json, sys
from pathlib import Path
import numpy as np
import argparse
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--input-dir', type=Path, required=True, help='Folder containing the private data/ input files')
parser.add_argument('--outdir', type=Path, default=Path(__file__).resolve().parents[1] / 'generated/reply_exploratory')
args = parser.parse_args()
PK = args.input_dir.resolve()
OUT = args.outdir.resolve()
OUT.mkdir(parents=True, exist_ok=True); SEED = 20261011; R = 5000
def read(p):
    with open(p, encoding='utf-8-sig', newline='') as f: return list(csv.DictReader(f))
replies = {r['response_id']: r for r in read(PK/'data/replies.csv')}
scen = {r['id']: r for r in read(PK/'data/scenarios.csv')}
lab = read(PK/'data/labels.csv')
by = {c: {r['response_id']: r for r in lab if r['coder'] == c} for c in ['single', 'coder_a', 'coder_b']}
def version(v):
    pool = dict(by['single']); pool.update(by['coder_a' if v == 1 else 'coder_b'])
    recs = []
    for rid, l in pool.items():
        r = replies[rid]
        g = lambda k: int(l[k]) if l[k] != '' else None
        recs.append(dict(rid=rid, sid=r['scenario_id'], model=r['model'], cond=r['condition'],
                         E=g('emotional_validation'), P=g('procedural_remedy'), text=r['response_text'],
                         cat=scen[r['scenario_id']]['category']))
    return recs
CODE = {'campus': 'A', 'procedure': 'B', 'boundary': 'C', 'procedure_boundary': 'D'}
def state(e, p):
    if e is None or p is None: return None
    return {(1, 1): 'both', (1, 0): 'E only', (0, 1): 'P only', (0, 0): 'neither'}[(e, p)]
STATES = ['both', 'E only', 'P only', 'neither']
def length(t):
    return len(re.sub(r'\s+', '', t))
def paras(t): return len([x for x in re.split(r'\n\s*\n', t.strip()) if x.strip()])
def sents(t): return len([x for x in re.split(r'[。！？!?；;\n]+', t) if x.strip()])
def lists(t): return len(re.findall(r'(?m)^\s*(?:[-*•]|\d+[.、)）]|[一二三四五六七八九十]+[、.])', t))
def ci(d): return [float(x) for x in np.quantile(d, [.025, .975])]
def boot(vals, rng):
    a = np.asarray(vals, float); idx = rng.integers(0, len(a), (R, len(a)))
    return a, a[idx].mean(axis=1)
def paired(recs, f, lhs, rhs, subset=None):
    cell = {(r['sid'], r['model'], r['cond']): r for r in recs}
    sids = sorted({r['sid'] for r in recs}); models = sorted({r['model'] for r in recs})
    vals = []
    for s in sids:
        d = []
        for m in models:
            a, b = cell.get((s, m, lhs)), cell.get((s, m, rhs))
            if a is None or b is None: continue
            x, y = f(a), f(b)
            if x is None or y is None: continue
            d.append(x - y)
        if d: vals.append(np.mean(d))
    return vals
res = {}
for v in (1, 2):
    recs = version(v); rng = np.random.default_rng(SEED)
    # 1 state shares by condition
    sh = {}
    for c in CODE:
        rr = [r for r in recs if r['cond'] == c and state(r['E'], r['P'])]
        sh[CODE[c]] = {'n': len(rr), **{s: sum(state(r['E'], r['P']) == s for r in rr) for s in STATES}}
    # 2 A->B transitions on complete pairs
    cell = {(r['sid'], r['model'], r['cond']): r for r in recs}
    T = {a: {b: 0 for b in STATES} for a in STATES}; n_excl = 0; n_pairs = 0
    for s in sorted({r['sid'] for r in recs}):
        for m in sorted({r['model'] for r in recs}):
            a, b = cell.get((s, m, 'campus')), cell.get((s, m, 'procedure'))
            if a is None or b is None: continue
            sa, sb = state(a['E'], a['P']), state(b['E'], b['P'])
            if sa is None or sb is None: n_excl += 1; continue
            T[sa][sb] += 1; n_pairs += 1
    # share of pairs ending in 'both', gained P, lost E, no P in B (scenario-clustered)
    def pair_ind(fn):
        out = []
        for s in sorted({r['sid'] for r in recs}):
            d = []
            for m in sorted({r['model'] for r in recs}):
                a, b = cell.get((s, m, 'campus')), cell.get((s, m, 'procedure'))
                if a is None or b is None: continue
                sa, sb = state(a['E'], a['P']), state(b['E'], b['P'])
                if sa is None or sb is None: continue
                d.append(fn(sa, sb))
            if d: out.append(np.mean(d))
        return out
    hasE = lambda x: x in ('both', 'E only'); hasP = lambda x: x in ('both', 'P only')
    inds = {'gain_P': lambda a, b: float(not hasP(a) and hasP(b)),
            'lost_E': lambda a, b: float(hasE(a) and not hasE(b)),
            'still_no_P': lambda a, b: float(not hasP(a) and not hasP(b)),
            'already_P_in_A': lambda a, b: float(hasP(a)),
            'lost_P': lambda a, b: float(hasP(a) and not hasP(b))}
    ti = {}
    for k, fn in inds.items():
        vals = pair_ind(fn); a, d = boot(vals, rng); ti[k] = dict(est=float(a.mean()), ci=ci(d))
    # 3 2x2 on complete cells (P)
    def complete(f):
        cells = {}
        for r in recs:
            cells.setdefault((r['sid'], r['model']), {})[r['cond']] = r
        keep = [(k, c) for k, c in cells.items() if len(c) == 4 and all(f(x) is not None for x in c.values())]
        return keep
    did = {}
    for name, f in [('P', lambda r: r['P']), ('E', lambda r: r['E']), ('both', lambda r: None if r['E'] is None or r['P'] is None else int(r['E'] and r['P']))]:
        keep = complete(f); per = {}
        for (s, m), c in keep:
            per.setdefault(s, []).append([f(c['campus']), f(c['procedure']), f(c['boundary']), f(c['procedure_boundary'])])
        arr = np.array([np.mean(x, axis=0) for x in per.values()])
        ba = arr[:, 1] - arr[:, 0]; dc = arr[:, 3] - arr[:, 2]; ix = dc - ba; ca = arr[:, 2] - arr[:, 0]
        o = dict(n_cells=len(keep), n_scen=len(arr))
        idx = rng.integers(0, len(arr), (R, len(arr)))
        for k, x in [('B-A', ba), ('D-C', dc), ('interaction', ix), ('C-A', ca)]:
            o[k] = dict(est=float(x.mean()), ci=ci(x[idx].mean(axis=1)))
        o['means'] = dict(zip('ABCD', [float(x) for x in arr.mean(axis=0)]))
        did[name] = o
    # 4 length
    L = {}
    for c in CODE:
        rr = [r for r in recs if r['cond'] == c]
        ch = [length(r['text']) for r in rr]
        L[CODE[c]] = dict(n=len(rr), median_chars=float(np.median(ch)), q1=float(np.percentile(ch, 25)), q3=float(np.percentile(ch, 75)),
                          mean_chars=float(np.mean(ch)), mean_paras=float(np.mean([paras(r['text']) for r in rr])),
                          mean_sents=float(np.mean([sents(r['text']) for r in rr])),
                          share_list=float(np.mean([lists(r['text']) > 0 for r in rr])))
    for k, fn in [('chars', lambda r: length(r['text'])), ('paras', lambda r: paras(r['text'])),
                  ('list_items', lambda r: lists(r['text'])), ('log_ratio_chars', lambda r: float(np.log(length(r['text']))))]:
        vals = paired(recs, fn, 'procedure', 'campus'); a, d = boot(vals, rng)
        L[f'B-A {k}'] = dict(est=float(a.mean()), ci=ci(d), n_scen=len(a))
    for m in sorted({r['model'] for r in recs}):
        sub = [r for r in recs if r['model'] == m]
        L[f'{m} B-A chars'] = [float(np.median([length(r['text']) for r in sub if r['cond'] == 'procedure'])),
                               float(np.median([length(r['text']) for r in sub if r['cond'] == 'campus']))]
    # 5 within-B: does procedure presence depend on length? (descriptive) 
    res[f'v{v}'] = dict(shares=sh, transitions=T, n_pairs=n_pairs, n_excluded_pairs=n_excl, trans_ind=ti, did=did, length=L)
json.dump(res, open(OUT/'new_analyses.json', 'w'), indent=1, ensure_ascii=False)
