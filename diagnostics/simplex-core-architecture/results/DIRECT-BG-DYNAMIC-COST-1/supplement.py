"""New offline supplement for one surplus expected diagnostic module key; no old auditor rerun."""
from pathlib import Path
import sys,json,tomllib
E=Path(__file__).resolve().parent;D=E.parent/'DIRECT-BG-DYNAMIC-COST-PREPARATION';sys.path.insert(0,str(D))
import control_reviewed as c
from analysis_reviewed import summarize,schedule,first_process_viable
run=D/'runs/cost1-300';out=run/'output';checks={}
def check(n,v):
 checks[n]=bool(v);c.require(v,n)
def toml(p):return tomllib.loads(p.read_text())
a=c.rd(run/'audit.json');check('original_false_preserved',a['all_passed'] is False and a['pure_timeout'] is False and a['error']=="RuntimeError('Raw schema/count/path')" and a['cells']==[] and c.bindings(a))
raw=toml(out/'raw.toml');loaded=c.loaded_for(c.config('cost1-300'))
expected=dict(phase='cost1-300',loaded=loaded,completed=True,fatal='',cells=8,windows=160,threads=1,blas_threads=1)
check('original_exact_schema_fails',raw!=expected)
check('only_Test_reporting_key_differs',set(expected['loaded'])-set(raw['loaded'])=={'Test'} and not set(raw['loaded'])-set(expected['loaded']) and all(v==expected['loaded'][k] for k,v in raw['loaded'].items()) and {k:v for k,v in raw.items() if k!='loaded'}=={k:v for k,v in expected.items() if k!='loaded'})
source=(D/'cost.jl').read_text();check('driver_reports_exact_five_modules','loaded=Dict(string(nameof(m))=>realpath(pathof(m)) for m in (J,LinearAlgebra,SparseArrays,TOML,PrecompileTools))' in source and 'using JSimplex, LinearAlgebra, SparseArrays, TOML, PrecompileTools' in source)
corrected_loaded={k:v for k,v in loaded.items() if k!='Test'}
check('narrow_schema_matches',raw==dict(expected,loaded=corrected_loaded))
# This is a new saved-output supplement, not a rewritten audit or in-memory patch.
check('original_false_blocks_second',not first_process_viable(a,c.rd(D/'inputs.json')['fixtures']))
p=c.rd(out/'process.json');inv=c.rd(run/'invocation.json');check('exit_and_limit',p['returncode']==0 and p['reason']=='exit0' and p['pins_unchanged'] is True and inv['supervisor']['accepted'] is True and 0<=inv['elapsed_seconds']<=300)
check('seal_launch_pins_unchanged',c.guard.pins_match(c.rd(run/'sealed.json')) and c.guard.pins_match(c.rd(run/'launch-pins.json')))
resources=[json.loads(x) for x in (out/'resources.jsonl').read_text().splitlines()];check('resources',bool(resources) and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in resources+[p['terminal_memory']]))
h=c.full_host(c.rd(run/'posthost.json')['groups']);check('fresh_full_process_closure',not h['matches'] and all(h[k]==c.rd(run/'sealed.json')[k] for k in ['head','master','boot_id']))
check('one_attempt_only',{x.name for x in (D/'runs').iterdir()}=={'cost1-300'})
check('complete_output_membership',{x.name for x in out.iterdir()}=={'pins.json','current.json','process.json','resources.jsonl','run.log','raw.toml'}|{f'{q}-{i}.toml' for q in ['started','preflight','probe','cell'] for i in range(1,9)}|{f'window-{i}-{j}.toml' for i in range(1,9) for j in range(1,21)})
fixtures=c.rd(D/'inputs.json')['fixtures'];cells=[];summary=[];windows=[]
for i,(f,backend) in enumerate([(f,b) for f in fixtures for b in ['native','markowitz']],1):
 identity=dict(fixture=f['name'],manager='BG',backend=backend,policy='threshold_one' if backend=='native' else 'default')
 check(f'cell{i}_identity',toml(out/f'started-{i}.toml')==identity and toml(out/f'cell-{i}.toml')==dict(identity,windows=20))
 rows=[toml(out/f'window-{i}-{j}.toml') for j in range(1,21)];windows+=rows
 check(f'cell{i}_schedule_pairs',all(r['pair']==(j+1)//2 and r['order']==1+(j-1)%2 and r['side']==schedule(1,(j+1)//2)[(j-1)%2] and r['policy']==identity['policy'] and r['measured']==(j>6) and r['correct'] is True and r['inputs_unchanged'] is True for j,r in enumerate(rows,1)) and all(rows[j]['outputs']==rows[j+1]['outputs'] and rows[j]['modes']==rows[j+1]['modes'] for j in range(0,20,2)))
 st=summarize(rows);pr=toml(out/f'probe-{i}.toml');states=pr['states'];st['probe_memory_gate']=all(10*z['graphs'][1]<=11*z['graphs'][0] for z in states);st['memory_gate'] &= st['probe_memory_gate']
 cells.append(dict(identity,statistics=st))
 summary.append(dict(identity,time_ratio=st['seconds']['paired_ratio']['median'],ratio_range=[st['seconds']['paired_ratio'][k] for k in ['minimum','maximum']],ratio_mad=st['seconds']['paired_ratio']['mad'],reference_seconds=st['seconds']['reference']['median'],candidate_seconds=st['seconds']['candidate']['median'],faster_pairs=st['faster_pairs'],bytes=[st['bytes'][s]['median'] for s in ['reference','candidate']],events=[st['events'][s]['median'] for s in ['reference','candidate']],final_graph=[st['retained_bytes'][s]['median'] for s in ['reference','candidate']],max_checkpoint_graph_ratio=max(z['graphs'][1]/z['graphs'][0] for z in states),gates={k:st[k] for k in ['time_median_gate','allocation_gate','memory_gate','probe_memory_gate']},probe_counters=pr['counts'],max_capacity=max(z['capacity'] for z in states),max_live=max(z['live'] for z in states),max_arena_payload=max(z['requested_payload_bytes'] for z in states),nested_seconds=st['nested_seconds']))
check('48warm112measured',len(windows)==160 and sum(w['measured'] for w in windows)==112)
check('measured_compilation_zero',all(w['compile_seconds']==w['recompile_seconds']==0 for w in windows if w['measured']))
viable=all(all(z['gates'].values()) and z['faster_pairs']>=3 for z in summary)
log=(out/'run.log').read_text();check('no_runtime_warnings_errors',not any(x in log for x in ['WARNING:','ERROR:','FATAL COST:','Traceback']))
c.save(E/'supplement-host.json',h)
files=sorted([x for x in run.rglob('*') if x.is_file()]+[E/'supplement.py',E/'supplement-host.json',E/'authorization.json',E/'entry.json'])
c.save(E/'supplement.json',dict(all_passed=True,checks=checks,original_audit_pass=False,original_audit_sha256=c.sha(run/'audit.json'),schema_difference='Only expected Test key absent from intentional five-module cost-driver loaded report. Does not prove Test was absent from process.',first_process_cost_viable=viable,cells=cells,summary=summary,process=dict(elapsed_seconds=inv['elapsed_seconds'],resource_samples=len(resources),min_available_kib=min(x['available_kib'] for x in resources),max_swap_used_kib=max(x['swap_used_kib'] for x in resources),terminal_memory=p['terminal_memory'],child_maxrss_kib=p['child_maxrss_kib'],measured_nonzero_gc_windows=sum(w['gc_seconds']>0 for w in windows if w['measured']),warnings=[]),scope='Narrow new offline diagnostic schema reconciliation and descriptive costs. Original false audit unchanged; exact numerical revalidation delegated to independent saved-data review; no automatic successor or production acceptance.',sha256={str(x):c.sha(x) for x in files}))
print('Supplement PASS',len(checks),'cost_viable',viable)
for x in summary:print(x['fixture'],x['backend'],'ratio',x['time_ratio'],'bytes',x['bytes'],'events',x['events'],'graph',x['final_graph'],'probe_max',x['max_checkpoint_graph_ratio'],'gates',x['gates'])
