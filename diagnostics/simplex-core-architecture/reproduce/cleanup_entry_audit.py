"""Audit one immutable S5-A census; exclusive artifacts, no repeated Julia work."""
from pathlib import Path
import sys, importlib.util, json, tomllib, itertools, collections
sys.dont_write_bytecode=True
root=Path(__file__).resolve().parents[3]
diag=root/'diagnostics/simplex-core-architecture'
name=sys.argv[1];raw=root/'.superpowers/simplex-core-architecture/S5-A'/name
spec=importlib.util.spec_from_file_location('guard',diag/'reproduce/guarded_run.py')
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
proc=json.loads((raw/'process.json').read_text());pins=json.loads((raw/'pins.json').read_text())
a=tomllib.loads((raw/'reference.toml').read_text())
types=['Float32','Float64','BigFloat','Rational{BigInt}']
expected={'/'.join(c) for c in itertools.product(types,['primal','dual'],['native','markowitz'],['native','checked'],['unobserved','observed','expired','project','bad_hint'])}
expected|={'/'.join(c) for c in itertools.product(['Float64'],['primal','dual'],['native','markowitz'],['native','checked'],['singular','observer_throw','logger_throw'])}
rows=a['cases'];controls=[x['control'] for x in rows]
initial=[next(r for r in x['recomputations'] if r['initial']) for x in rows]
checks=dict(normal_exit=proc['reason']=='exit0' and proc['returncode']==0,
 process_pins=proc['pins_unchanged'],independent_pins=g.pins_match(pins),
 pin_manifest=g.digest(raw/'pins.json')==proc['pins_sha256']==g.digest(raw.parent/(name+'-pins.json')),
 source=a['source']==str(root/'src/JSimplex.jl') and a['source_sha256']==g.digest(root/'src/JSimplex.jl'),
 script=a['script_sha256']==g.digest(raw.parent/(name+'-source')/'cleanup_entry_census.jl'),
 case_coverage=a['case_count']==len(rows)==len(expected)==184 and {c['key'] for c in controls}==expected,
 exact_pairs=all(x['exact_pair'] for x in rows),caller_basis_preserved=all(c['restored_basis_unchanged'] for c in controls),
 initial_scope=all(sum(r['initial'] for r in x['recomputations'])==1 for x in rows),
 initial_work=all(r['completed'] and r['counts'][:3]==[1,1,1] and r['counts'][6]==0 for r in initial),
 normal_optima=all(c['status']=='OPTIMAL' and c['original_feasible'] for c in controls if c['mode'] in ['unobserved','observed','project','bad_hint']),
 expired=all(c['status']=='TIME_LIMIT' and c['iterations']==7 and c['refactorizations']==3 and len(x['recomputations'])==1 for x,c in zip(rows,controls) if c['mode']=='expired'),
 singular=all(c['status']=='NUMERICAL_ERROR' for c in controls if c['mode']=='singular'),
 exceptions=all(c['caller_exception_preserved'] for c in controls if c['mode'] in ['observer_throw','logger_throw']),
 policy=all(c['recovery_enabled']==(c['profile']=='checked') for c in controls),
 native_no_checkpoint=all(r['counts'][4:6]==[0,0] and not r['after']['checkpoints'] for r,c in zip(initial,controls) if c['profile']=='native'),
 checked_checkpoint=all(r['counts'][4:6]==[1,1] and len(r['after']['checkpoints'])==1 for r,c in zip(initial,controls) if c['profile']=='checked'),
 observed_initial=all(any(e['reason']=='refactor_initial' for e in c['events']) for c in controls if c['mode']!='unobserved'),
 restored_scope=all(len(x['recomputations'])>=2 and x['recomputations'][1]['refactor_requested'] for x,c in zip(rows,controls) if c['mode'] not in ['expired','observer_throw']))
summary=[]
for profile in ['native','checked']:
 group=[r for r,c in zip(initial,controls) if c['profile']==profile]
 summary.append({'profile':profile,'cases':len(group),'initial_counts':sorted({tuple(r['counts']) for r in group})})
res=[json.loads(l) for l in (raw/'resources.jsonl').read_text().splitlines()]
resources={'min_available_kib':min(r['available_kib'] for r in res),'max_swap_kib':max(r['swap_used_kib'] for r in res)}
for key in ['VmPeak','VmRSS']:resources[key+'_kib']=max(int(v.split()[1]) for r in res for v in r['child_memory'] if v.startswith(key+':'))
out={'accepted':all(checks.values()),'checks':checks,'initial_summary':summary,'resources':resources,
 'reference_sha256':g.digest(raw/'reference.toml'),'scope':'Bounded unchanged-body census; no timing, raw-factor-solve count, full recovery coverage or production optimization claim'}
dest=diag/'results/S5-A';dest.mkdir(exist_ok=True)
paths=[dest/(name+'-'+s) for s in ['audit.json','process.json','reference.toml','run.log']]
assert not any(p.exists() for p in paths),'refuse to replace existing evidence'
with paths[0].open('x') as f:json.dump(out,f,indent=2);f.write('\n')
for target,s in zip(paths[1:],['process.json','reference.toml','run.log']):
 with target.open('xb') as f:f.write((raw/s).read_bytes())
print(json.dumps(out,indent=2));assert out['accepted'],checks
