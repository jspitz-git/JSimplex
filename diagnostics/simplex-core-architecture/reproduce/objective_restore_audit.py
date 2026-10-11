"""Exclusive post-exit audit of bounded objective restoration census."""
from pathlib import Path
import sys,json,tomllib,itertools,importlib.util,collections
sys.dont_write_bytecode=True
root=Path(__file__).resolve().parents[3];diag=root/'diagnostics/simplex-core-architecture'
name=sys.argv[1];raw=root/'.superpowers/simplex-core-architecture/S5-B'/name
spec=importlib.util.spec_from_file_location('guard',diag/'reproduce/guarded_run.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
a=tomllib.loads((raw/'reference.toml').read_text());proc=json.loads((raw/'process.json').read_text());pins=json.loads((raw/'pins.json').read_text())
modes=['original','cost_owned','cost_detached','cost_unowned','bounds_owned','bounds_alien','expired','stop_restored','observer_throw']
expected={'/'.join(c) for c in itertools.product(['Float64','Rational{BigInt}'],['primal','dual'],['native','markowitz'],['native','checked'],modes)}
rows=a['cases'];controls=[x['control'] for x in rows]
normal=['original','cost_owned','cost_detached','cost_unowned','bounds_owned']
checks=dict(normal_exit=proc['reason']=='exit0' and proc['returncode']==0,process_pins=proc['pins_unchanged'],
 independent_pins=g.pins_match(pins),manifest=g.digest(raw/'pins.json')==proc['pins_sha256']==g.digest(raw.parent/(name+'-pins.json')),
 source=a['source']==str(root/'src/JSimplex.jl') and a['source_sha256']==g.digest(root/'src/JSimplex.jl'),
 script=a['script_sha256']==g.digest(raw.parent/(name+'-source')/'objective_restore_census.jl'),
 threads=a['julia_threads']==a['blas_threads']==1,
 cases=len(rows)==a['case_count']==144 and {c['key'] for c in controls}==expected,
 recorded_pairs=all(x['exact_recorded_pair'] for x in rows),input_preserved=all(c['input_unchanged'] for c in controls),
 foreign_model=all(c['foreign_checkpoint_rejected'] for c in controls),
 original_optima=all(c['status']=='OPTIMAL' and c['original_feasible'] and c['objective'] in ['0.0','0//1'] for c in controls if c['mode'] in normal),
 alien_bound_proof_rejected=all(c['status']=='NUMERICAL_ERROR' and not c['primal'] for c in controls if c['mode']=='bounds_alien'),
 cancellation=all(c['status']=='TIME_LIMIT' and not c['primal'] for c in controls if c['mode'] in ['expired','stop_restored']),
 caller_exception=all(c['exception_preserved'] for c in controls if c['mode']=='observer_throw'),
 budget_monotone=all(c['budget_iterations']>=5 and c['budget_refactorizations']>=2 for c in controls),
 phase_checkpoint=all(not c['checkpoint_still_matches'] and not c['final']['journal_present'] for c in controls if c['mode'] in ['cost_owned','cost_detached','cost_unowned','bounds_owned','stop_restored']),
 alias_controls=all(c['initial']['active_costs_same']==(c['mode']=='cost_owned') for c in controls if c['mode'] in ['cost_owned','cost_detached']),
 restore_no_reconstruction=all(r['counts'][6:9]==[0,0,0] for x in rows for r in x['restorations']),
 alias_duplicate_cost_copy=all(len(x['restorations'])==1 and x['restorations'][0]['counts'][9:11]==[3,5] for x in rows if x['control']['mode']=='cost_owned'),
 detached_copy_preserved=all(len(x['restorations'])==1 and x['restorations'][0]['counts'][9:11]==[3,5] for x in rows if x['control']['mode']=='cost_detached'))
groups=collections.defaultdict(set)
for x in rows:
 for r in x['restorations']:groups[x['control']['mode']].add(tuple(r['counts']))
out={'accepted':all(checks.values()),'checks':checks,'restoration_counts':{k:sorted(v) for k,v in groups.items()},'reference_sha256':g.digest(raw/'reference.toml'),
 'scope':'Exact selected recorded state/event representation; controlled journal states, no natural frequency or timing claim. Copy counters cover only restoration functions.'}
res=[json.loads(l) for l in (raw/'resources.jsonl').read_text().splitlines()]
out['resources']={'min_available_kib':min(x['available_kib'] for x in res),'max_swap_kib':max(x['swap_used_kib'] for x in res)}
for key in ['VmPeak','VmRSS']:out['resources'][key+'_kib']=max(int(s.split()[1]) for x in res for s in x['child_memory'] if s.startswith(key+':'))
dest=diag/'results/S5-B';dest.mkdir(exist_ok=True);names=['audit.json','process.json','reference.toml','run.log']
assert not any((dest/(name+'-'+s)).exists() for s in names),'evidence already exists'
with (dest/(name+'-audit.json')).open('x') as f:json.dump(out,f,indent=2);f.write('\n')
for s in names[1:]:
 with (dest/(name+'-'+s)).open('xb') as f:f.write((raw/s).read_bytes())
print(json.dumps(out,indent=2));assert out['accepted'],checks
