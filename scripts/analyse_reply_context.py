"""Exploratory analysis of procedural content by theme.
Word-presence indicators on the reply text (no new labels), plus theme ranges from the
deposited prevalence table. Exploratory and descriptive."""
import csv, re, json
from pathlib import Path
import numpy as np

import argparse
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--input-dir', type=Path, required=True, help='Folder containing the private data/ input files')
parser.add_argument('--outdir', type=Path, default=Path(__file__).resolve().parents[1] / 'generated/reply_exploratory')
args = parser.parse_args()
PK = args.input_dir.resolve()
OUT = args.outdir.resolve()
OUT.mkdir(parents=True, exist_ok=True)
SEED, R = 20261011, 5000

def rd(p):
    with open(p, encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

# Indicators: presence of at least one match in the reply (Chinese text).
IND = {
    'school_role': r'班主任|辅导员|心理老师|心理咨询室|心理辅导|心理健康中心|心理中心|校医|宿管|值班老师|任课老师|学科老师|德育处|政教处|教务处|学生处|校长',
    'record': r'记录|记下|截图|留存|证据',
    'safety_net': r'伤害自己|自伤|轻生|自杀|心理热线|心理援助热线|12355|心理援助|急诊|生命危险',
    'self_help': r'深呼吸|呼吸|(?<!课间)休息|番茄|分解|拆分|清单|散步|运动|早点睡|喝水|日记|拉伸',
}
LOW = {'academic_pressure', 'self_awareness', 'self_management'}  # lowest default rates (Section 4.1)

rep = [r for r in rd(PK/'data/replies.csv') if r['coding_split'] != 'calibration']
scen = {r['id']: r for r in rd(PK/'data/scenarios.csv')}
for r in rep:
    r['cat'] = scen[r['scenario_id']]['category']
    for k, p in IND.items():
        r[k] = int(bool(re.search(p, r['response_text'])))

cell = {(r['scenario_id'], r['model'], r['condition']): r for r in rep}
models = sorted({r['model'] for r in rep})

def paired(sids, k, lhs='procedure', rhs='campus'):
    vals = []
    for s in sids:
        d = [cell[(s, m, lhs)][k] - cell[(s, m, rhs)][k] for m in models
             if (s, m, lhs) in cell and (s, m, rhs) in cell]
        if d: vals.append(np.mean(d))
    return np.asarray(vals, float)

def boot(a, rng):
    idx = rng.integers(0, len(a), (R, len(a)))
    return [float(x) for x in np.quantile(a[idx].mean(axis=1), [.025, .975])]

rng = np.random.default_rng(SEED)
groups = {'low_default': sorted({r['scenario_id'] for r in rep if r['cat'] in LOW}),
          'other': sorted({r['scenario_id'] for r in rep if r['cat'] not in LOW}),
          'all': sorted({r['scenario_id'] for r in rep})}
res = {'n_scenarios': {g: len(s) for g, s in groups.items()}, 'indicators': {}}
for k in IND:
    res['indicators'][k] = {}
    for g, sids in groups.items():
        o = {}
        for c in ('campus', 'procedure', 'boundary', 'procedure_boundary'):
            rr = [r for r in rep if r['scenario_id'] in sids and r['condition'] == c]
            o[c] = dict(n=len(rr), share=float(np.mean([r[k] for r in rr])))
        a = paired(sids, k)
        o['B_minus_A'] = dict(est=float(a.mean()), ci=boot(a, rng), n_scen=len(a))
        res['indicators'][k][g] = o
for k in IND:  # boundary module alone (C minus A) and added to guidance (D minus B), all scenarios
    for lhs, rhs, nm in (('boundary', 'campus', 'C_minus_A'), ('procedure_boundary', 'procedure', 'D_minus_B')):
        a = paired(groups['all'], k, lhs, rhs)
        res['indicators'][k]['all'][nm] = dict(est=float(a.mean()), ci=boot(a, rng), n_scen=len(a))
        print(f"{k:12s} {nm} {a.mean()*100:+5.1f} {[round(x*100,1) for x in res['indicators'][k]['all'][nm]['ci']]}")
# school role by theme (for flattening)
res['school_role_by_theme'] = {}
for cat in sorted({r['cat'] for r in rep}):
    res['school_role_by_theme'][cat] = {c: float(np.mean([r['school_role'] for r in rep if r['cat'] == cat and r['condition'] == c]))
                                        for c in ('campus', 'procedure')}
# theme range of concrete procedure (deposited prevalence)
# Compute theme rates directly from private labels; no deposited AI results are needed.
label_rows = rd(PK/'data/labels.csv')
label_by = {c: {r['response_id']: r for r in label_rows if r['coder'] == c}
            for c in ('single', 'coder_a', 'coder_b')}
prev = []
for coder, version in (('coder_a', 'rater_1'), ('coder_b', 'rater_2')):
    pool = dict(label_by['single']); pool.update(label_by[coder])
    for category in sorted({r['cat'] for r in rep}):
        for condition in ('campus', 'procedure'):
            values = [int(pool[r['response_id']]['procedural_remedy']) for r in rep
                      if r['cat'] == category and r['condition'] == condition
                      and r['response_id'] in pool and pool[r['response_id']]['procedural_remedy'] != '']
            prev.append(dict(estimate=float(np.mean(values)), scope='all_noncalibration',
                coding_version=version, group_type='category', feature='procedural_remedy', condition=condition))
rng_out = {}
for ver in ('rater_1', 'rater_2'):
    for cond in ('campus', 'procedure'):
        v = [float(r['estimate'])*100 for r in prev if r['scope'] == 'all_noncalibration' and r['coding_version'] == ver
             and r['group_type'] == 'category' and r['feature'] == 'procedural_remedy' and r['condition'] == cond]
        rng_out[f'{ver}_{cond}'] = dict(min=min(v), max=max(v), range=max(v)-min(v), n=len(v))
res['theme_range_procedure'] = rng_out
res['dictionary'] = IND
json.dump(res, open(OUT/'context_analyses.json', 'w'), indent=1, ensure_ascii=False)
for k in IND:
    for g in ('low_default', 'other'):
        o = res['indicators'][k][g]
        print(f"{k:12s} {g:12s} A {o['campus']['share']*100:5.1f} B {o['procedure']['share']*100:5.1f} "
              f"B-A {o['B_minus_A']['est']*100:+5.1f} [{o['B_minus_A']['ci'][0]*100:+.1f},{o['B_minus_A']['ci'][1]*100:+.1f}] n={o['B_minus_A']['n_scen']}")
print(json.dumps(rng_out, indent=0))
print({k: {c: round(v*100) for c, v in d.items()} for k, d in res['school_role_by_theme'].items()})

# 2x2 cell means with scenario-bootstrap intervals, on complete cells (as in new_analyses.py)
lab = rd(PK/'data/labels.csv')
by = {c: {l['response_id']: l for l in lab if l['coder'] == c} for c in ('single', 'coder_a', 'coder_b')}
repid = {r['response_id']: r for r in rep}
res['cell_means_P'] = {}
for v in (1, 2):
    pool = dict(by['single']); pool.update(by['coder_a' if v == 1 else 'coder_b'])
    cells = {}
    for rid, l in pool.items():
        if rid not in repid or l['procedural_remedy'] == '': continue
        r = repid[rid]; cells.setdefault((r['scenario_id'], r['model']), {})[r['condition']] = int(l['procedural_remedy'])
    per = {}
    for (s_, m), c in cells.items():
        if len(c) == 4: per.setdefault(s_, []).append([c['campus'], c['procedure'], c['boundary'], c['procedure_boundary']])
    arr = np.array([np.mean(x, axis=0) for x in per.values()]); idx = rng.integers(0, len(arr), (R, len(arr)))
    bm = arr[idx].mean(axis=1)
    res['cell_means_P'][f'v{v}'] = {k: dict(est=float(arr[:, j].mean()), ci=[float(x) for x in np.quantile(bm[:, j], [.025, .975])])
                                    for j, k in enumerate('ABCD')}
    res['cell_means_P'][f'v{v}']['n_cells'] = int(sum(len(x) for x in per.values()))
print(json.dumps(res['cell_means_P'], indent=0))
json.dump(res, open(OUT/'context_analyses.json', 'w'), indent=1, ensure_ascii=False)

# what the recording step asks the student to record: words within the 25 characters before and 40 after each match
INNER = r'情绪|感受|心情|睡眠|状态|想法|压力|焦虑'; EVENT = r'经过|地点|事实|对话|聊天|证据|截图|发生'
res['record_context'] = {}
for g, sids in (('low_default', groups['low_default']), ('other', groups['other'])):
    n = inner = event = 0
    for r in rep:
        if r['condition'] != 'procedure' or r['scenario_id'] not in sids: continue
        ms = [m.start() for m in re.finditer(IND['record'], r['response_text'])]
        if not ms: continue
        win = ' '.join(r['response_text'][max(0, s - 25):s + 40] for s in ms); n += 1
        inner += bool(re.search(INNER, win)); event += bool(re.search(EVENT, win))
    res['record_context'][g] = dict(n=n, inner=inner, event=event)
print('record context', res['record_context'])
json.dump(res, open(OUT/'context_analyses.json', 'w'), indent=1, ensure_ascii=False)

# boundary replies that name a school role where the matched default reply does not; random ten saved for reading
import random
newrole = [cell[(s, m, 'boundary')] for (s, m, c) in cell if c == 'boundary' and (s, m, 'campus') in cell
           and cell[(s, m, 'boundary')]['school_role'] and not cell[(s, m, 'campus')]['school_role']]
random.seed(3); pick = random.sample(sorted(newrole, key=lambda r: r['response_id']), 10)
with open(OUT/'boundary_role_sample.txt', 'w', encoding='utf-8') as f:
    for r in pick:
        mm = re.search(IND['school_role'], r['response_text'])
        f.write(r['response_id'] + '\t' + r['response_text'][max(0, mm.start() - 40):mm.end() + 40].replace('\n', ' ') + '\n')
print('boundary new-role replies', len(newrole))

# spot check of the final word lists: 12 random matches per indicator, saved for reading
random.seed(20261105)
with open(OUT/'indicator_spotcheck.txt', 'w', encoding='utf-8') as f:
    for k in IND:
        hits = []
        for r in sorted(rep, key=lambda r: r['response_id']):
            mm = re.search(IND[k], r['response_text'])
            if mm: hits.append((r['response_id'], r['response_text'][max(0, mm.start() - 25):mm.end() + 20].replace('\n', ' ')))
        f.write(f'== {k} ({len(hits)} replies)\n')
        for rid, t in random.sample(hits, 12): f.write(f'{rid}\t{t}\n')
