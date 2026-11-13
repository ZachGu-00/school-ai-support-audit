"""Compute primary reply statistics from separately supplied private input records."""
from pathlib import Path
import csv, json, math, subprocess, sys
import numpy as np
from audit_statistics import FEATURES, groupings, prevalence, paired_contrast, reliability

ROOT=Path(__file__).resolve().parents[1]
import argparse
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--input-dir',type=Path,required=True,help='Folder containing data/replies.csv, data/labels.csv and data/scenarios.csv')
parser.add_argument('--outdir',type=Path,default=ROOT/'generated/reply_primary')
args=parser.parse_args()
PK=args.input_dir.resolve()
OUT=args.outdir.resolve()
OUT.mkdir(parents=True,exist_ok=True)
CONDITIONS=['campus','procedure','boundary','procedure_boundary']
CONTRASTS={'B_minus_A':('procedure','campus'),'D_minus_B':('procedure_boundary','procedure'),
           'C_minus_A':('boundary','campus'),'D_minus_C':('procedure_boundary','boundary')}
JOINTS={'procedure_and_emotional_validation':['procedural_remedy','emotional_validation'],
        'procedure_and_institutional_stakes':['procedural_remedy','institutional_stake_recognition']}

def read(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def save(name,rows):
    with (OUT/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

replies={r['response_id']:r for r in read(PK/'data/replies.csv')}
scenarios={r['id']:r for r in read(PK/'data/scenarios.csv')}
labels=read(PK/'data/labels.csv')
by_coder={c:{} for c in ['single','coder_a','coder_b']}
for r in labels:by_coder[r['coder']][r['response_id']]=r
assert len(replies)==720 and len(by_coder['single'])==552
assert len(by_coder['coder_a'])==144 and set(by_coder['coder_a'])==set(by_coder['coder_b'])
assert not (set(by_coder['single']) & set(by_coder['coder_a']))
pr,cr=[],[]
for scope in ['all_noncalibration','double_coded_subset']:
    for coder,version in [('coder_a','rater_1'),('coder_b','rater_2')]:
        pool=dict(by_coder[coder])
        if scope=='all_noncalibration':pool.update(by_coder['single'])
        records=[]
        for rid,label in sorted(pool.items()):
            r=replies[rid];s=scenarios[r['scenario_id']]
            rec={k:r[k] for k in ['response_id','scenario_id','model','condition']}
            rec.update({k:s[k] for k in ['category','difficulty']})
            rec.update({f:int(label[f]) if label[f] else None for f in FEATURES})
            for joint,members in JOINTS.items():rec[joint]=None if any(rec[f] is None for f in members) else int(all(rec[f]==1 for f in members))
            records.append(rec)
        for group,value,subset in groupings(records):
            for feature in FEATURES+list(JOINTS):
                prefix=dict(scope=scope,coding_version=version,coder_stream=coder,group_type=group,group_value=value,group_display_name=value,feature=feature)
                for condition in CONDITIONS:pr.append({**prefix,'condition':condition,**prevalence(subset,feature,condition,5000)})
                for contrast,(lhs,rhs) in CONTRASTS.items():cr.append({**prefix,'contrast':contrast,'lhs':lhs,'rhs':rhs,**paired_contrast(subset,feature,lhs,rhs,5000)})
        print('Computed',scope,version,flush=True)
imported={c:{rid:{f:r[f] if r[f] else 'U' for f in FEATURES} for rid,r in by_coder[c].items()} for c in ['coder_a','coder_b']}
ar=reliability(imported,replies,5000)
report=[]
for name,rows,keys in [('prevalence.csv',pr,['scope','coding_version','group_type','group_value','feature','condition']),
                       ('contrasts.csv',cr,['scope','coding_version','group_type','group_value','feature','contrast']),
                       ('agreement.csv',ar,['feature'])]:
    save(name,rows)
