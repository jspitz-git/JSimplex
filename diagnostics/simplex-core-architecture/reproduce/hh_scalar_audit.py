from pathlib import Path
import sys,importlib.util,json,tomllib,collections,statistics,shutil,math
sys.dont_write_bytecode=True
r=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');d=r/'diagnostics/simplex-core-architecture';name=sys.argv[1];p=r/'.superpowers/simplex-core-architecture/S4-D'/name
s=importlib.util.spec_from_file_location('guard',d/'reproduce/guarded_run.py');g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
a=tomllib.loads((p/'reference.toml').read_text());proc=json.loads((p/'process.json').read_text());pins=json.loads((p/'pins.json').read_text())
types=['Float16','Float32','BigFloat','Rational{BigInt}','Rational{Int64}'];backends=['native','markowitz']
expected={f'{t}/{b}/{shape}{n}' for t in types for b in backends for shape in ['sparse','dense'] for n in [8,32]}
checks=dict(normal_exit=proc['reason']=='exit0' and proc['returncode']==0,pins_unchanged=proc['pins_unchanged'],pins_reverified=g.pins_match(pins),pin_digest=g.digest(p/'pins.json')==proc['pins_sha256']==g.digest(p.parent/(name+'-pins.json')),complete=a.get('complete',False),single_threads=a['julia_threads']==a['blas_threads']==1,source=a['source']==str(r/'src') and a['source_hh_sha256']==g.digest(r/'src/huangfu_hall_factorization.jl'),bigfloat_precision=a['bigfloat_precision']==256,sample_count=len(a['samples'])==360,compile_zero=all(x['compile_seconds']==0 for x in a['samples']),cases=len(a['cases'])==40 and {x['case'] for x in a['cases']}==expected,retention_cases=len(a['retention'])==80 and {(x['case'],x['state']) for x in a['retention']}=={(c,s) for c in expected for s in ['fresh','cycled']},lifecycle_cases=len(a['lifecycle'])==10 and {(x['precision'],x['backend']) for x in a['lifecycle']}=={(t,b) for t in types for b in backends},lifecycle_checks=all(x['failed_refactor_preserved'] and [y['transition'] for y in x['transitions']]==['changed_pattern','shrink','dense_regrow','empty','restore'] for x in a['lifecycle']),sample_settings=a['calls_per_sample']==4 and a['rounds']==3,finite_metrics=all(math.isfinite(x[k]) and x[k]>=0 for x in a['samples'] for k in ['seconds','compile_seconds','gc_seconds','bytes','allocations']))
groups=collections.defaultdict(list)
for row in a['samples']:groups[(row['case'],row['region'])].append(row)
checks['all_groups_complete']=set(groups)=={(c,b) for c in expected for b in ['backend','extraction','whole_refactor']} and all(sorted(x['round'] for x in rows)==[1,2,3] for rows in groups.values())
matrices=collections.defaultdict(list)
for row in a['cases']:matrices[(row['precision'],row['case'].rsplit('/',1)[1])].append(row['matrix_sha256'])
checks['paired_backend_matrix_hashes']=len(matrices)==20 and all(len(x)==2 and x[0]==x[1] for x in matrices.values())
folder=d/'results/S4-D';folder.mkdir(exist_ok=True)
(folder/(name+'-initial-audit.json')).write_text(json.dumps({'accepted':False,'checks':checks,'reason':'BigFloat Serialization fingerprint is representation-dependent; separate canonical probe required'},indent=2)+'\n')
legacy_hash_result=checks.pop('paired_backend_matrix_hashes')
checks['non_bigfloat_backend_hashes']=all(len(x)==2 and x[0]==x[1] for key,x in matrices.items() if key[0]!='BigFloat')
probe=p.parent/'scalar-hash-probe-1';pr=json.loads((probe/'process.json').read_text());pa=tomllib.loads((probe/'reference.toml').read_text())
checks['probe_exit_pins']=pr['returncode']==0 and pr['pins_unchanged'] and g.pins_match(json.loads((probe/'pins.json').read_text()))
checks['probe_eight_unchanged_inputs']=pa['complete'] and len(pa['rows'])==8 and all(x['input_unchanged'] and x['serialized_before']==x['serialized_after'] for x in pa['rows'])
checks['probe_canonical_pairs']=all(len(rows:=[x for x in pa['rows'] if x['dimension']==n and x['dense']==dense])==2 and rows[0]['canonical_hash']==rows[1]['canonical_hash'] for n in [8,32] for dense in [False,True])
checks['serialization_representation_mismatch_reproduced']=all(x['repeated_serialization_equal'] and not x['serialized_equal_copy'] for x in pa['rows'])
assert all(checks.values()),checks
out={'accepted':True,'scope':'Bounded scalar diagnostic; BigFloat original Serialization hashes are not canonical input equality evidence. Separate same-recipe probe proves exact unchanged inputs/canonical pairs, not retroactive hashes for original cost records. No speedup or full S4/S6 closure','checks':checks,'reference_sha256':g.digest(p/'reference.toml'),'pins_sha256':proc['pins_sha256'],'groups':[]}
for (case,region),rows in sorted(groups.items()):
 row={'case':case,'region':region,'calls_per_sample':4}
 for field in ['seconds','bytes','allocations','gc_seconds']:
  vals=[x[field] for x in rows];row[field]={'median':statistics.median(vals),'min':min(vals),'max':max(vals)}
 out['groups'].append(row)
res=[json.loads(l) for l in (p/'resources.jsonl').read_text().splitlines()]
def mem(key):return max(int(s.split()[1]) for row in res for s in row['child_memory'] if s.startswith(key+':'))
out['resources']={'peak_vm_kib':mem('VmPeak'),'max_sampled_rss_kib':mem('VmRSS'),'min_available_kib':min(x['available_kib'] for x in res),'max_swap_used_kib':max(x['swap_used_kib'] for x in res)}
folder=d/'results/S4-D';folder.mkdir(exist_ok=True)
for f in ['reference.toml','process.json','run.log']:
 target=folder/(name+'-'+f);assert not target.exists();shutil.copyfile(p/f,target)
with (folder/(name+'-audit.json')).open('x') as f:f.write(json.dumps(out,indent=2)+'\n')
print('checks',checks);print('resources',out['resources'])
for x in out['groups']:
 if x['case'].endswith('32'):print(x['case'],x['region'],'us/call',x['seconds']['median']*1e6/4,'B/4calls',x['bytes']['median'],'events',x['allocations']['median'])
