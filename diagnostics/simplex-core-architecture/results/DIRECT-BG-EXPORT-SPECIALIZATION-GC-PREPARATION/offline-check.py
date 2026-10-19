"""New offline text inverse and synthetic record tests. Never invokes Julia."""
from pathlib import Path
import sys,json,copy,hashlib
N=Path(__file__).resolve().parent;D=N.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-DRIVER');R=N.parents[3]
sys.path.insert(0,str(N));from preparation_schema import validate_record,validate_records
checks={}
def ck(n,v):checks[n]=bool(v)
def reject(n,fn):
 try:fn();ck(n,False)
 except ValueError:ck(n,True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
a=(N/'driver.jl').read_text();old=(D/'driver.jl').read_text()
b=a.replace('# UNEXECUTED GC preparation amendment; same lifecycle and gates, separate run admission required.','# UNEXECUTED Task2; ordinary stage, all definitions before main; no runtime include.',1).replace('PHASE in ("redgc300","greengc300")','PHASE in ("red300","green300","red600","green600")',1).replace('include("preparation.jl")\n','',1).replace('            pair == 3 && prepare_gc!(cell,f.name)\n','',1).replace('        require(PREPARATION_CALLS[] == PREPARATION_COMPLETED[] == 3,"Preparation count")\n','',1).replace('        raw["preparation_calls"]=PREPARATION_CALLS[]\n        raw["preparations_completed"]=PREPARATION_COMPLETED[]\n','',1)
ck('complete_original_driver_inverse',b==old)
for n in ['red-kernel.jl','green-kernel.jl','recorder.jl','inputs.toml','expected-tests.toml']:ck('copy_'+n,(N/n).read_bytes()==(D/n).read_bytes())
h=(N/'preparation.jl').read_text();ck('one_fixed_GC_call',h.count('GC.gc(true)')==1 and h.count('GC.gc(')==1)
ck('no_factor_parameter','function prepare_gc!(cell::Int,fixture)' in h and 'factor' not in h.split('\n',1)[1])
ck('one_call_site_after_pair_check',a.count('prepare_gc!(cell,f.name)')==1 and '"Paired output/mode mismatch")\n            pair == 3 && prepare_gc!(cell,f.name)' in a)
ck('top_level_include_before_functions',a.index('include("preparation.jl")')<a.index('function exact_tree'))
ck('no_gc_disable_or_manual_finalize',all(x not in a+h for x in ['GC.enable(', 'GC.enable_finalizers(', 'finalize(', 'precompile(', 'eval(']))
ck('attempt_before_GC_record_before_completed',h.index('PREPARATION_CALLS[] += 1')<h.index('@timed GC.gc(true)')<h.index('save_window(')<h.index('PREPARATION_COMPLETED[] += 1'))
ck('final_raw_counters',a.index('raw["preparation_calls"]')>a.index('finally\n') and a.index('raw["preparations_completed"]')<a.index('save_window("raw.toml"'))
ck('guarded_completion_before_true',a.index('"Preparation count")')<a.index('raw["complete"]=true'))
ck('no_automatic_launch',not any((N/n).exists() for n in ['launch.py','seal.py','reservation.json','runs']))
red=json.loads((N/'structural-red.json').read_text());ck('source_RED_before_candidate',red['candidate_absent'] and red['actual_missing']==red['expected_missing']==3)
base=dict(phase='redgc300',fixture='sparse32',cell=1,after_pair=3,before_pair=4,requested_full_gc=True,calls=1,cumulative_calls=1,returned=True,seconds=.04,bytes=64,events=2,gc_seconds=.03,compile_seconds=.01,recompile_seconds=0.,gc_pauses=1,full_collections=1)
ck('valid_record',validate_record(base,1,'redgc300'))
for k,v in [('phase','red300'),('fixture','dense32'),('cell',2),('cell',True),('after_pair',4),('before_pair',3),('calls',2),('calls',True),('cumulative_calls',2),('requested_full_gc',False),('returned',False)]:
 z=copy.deepcopy(base);z[k]=v;reject('reject_'+k+'_'+str(v),lambda z=z:validate_record(z,1,'redgc300'))
for key in ['bytes','events','gc_pauses','full_collections']:
 for value in [-1,True,1.0]:
  z=copy.deepcopy(base);z[key]=value;reject('reject_'+key+'_'+str(value),lambda z=z:validate_record(z,1,'redgc300'))
for key in ['seconds','gc_seconds','compile_seconds','recompile_seconds']:
 for value in [-1.,float('nan'),float('inf'),True,1]:
  z=copy.deepcopy(base);z[key]=value;reject('reject_'+key+'_'+str(value),lambda z=z:validate_record(z,1,'redgc300'))
z=copy.deepcopy(base);del z['events'];reject('reject_missing',lambda:validate_record(z,1,'redgc300'))
z2=copy.deepcopy(base);z2['extra']=0;reject('reject_extra',lambda:validate_record(z2,1,'redgc300'))
for phase in ['redgc300','greengc300']:
 rows={}
 for i,name in enumerate(['sparse32','dense32','sparse96'],1):
  v=copy.deepcopy(base);v.update(phase=phase,fixture=name,cell=i,cumulative_calls=i);rows[f'preparation-{i}.toml']=v
 ck('complete_'+phase,validate_records(rows,phase,True));ck('partial_'+phase,validate_records({'preparation-1.toml':rows['preparation-1.toml']},phase,False))
 reject('reject_gap_'+phase,lambda rows=rows,phase=phase:validate_records({'preparation-2.toml':rows['preparation-2.toml']},phase,False))
 reject('reject_incomplete_'+phase,lambda phase=phase:validate_records({},phase,True))
# Deliberately allow cold preparation compilation and overlapping timer totals.
z=copy.deepcopy(base);z.update(compile_seconds=2.,gc_seconds=2.,seconds=1.,full_collections=2)
ck('no_sum_or_exact_collection_gate',validate_record(z,1,'redgc300'))
paths=[p for p in N.iterdir() if p.is_file()]+[D/'driver.jl']+[D/n for n in ['red-kernel.jl','green-kernel.jl','recorder.jl','inputs.toml','expected-tests.toml']]
v=dict(all_passed=all(checks.values()),checks=checks,sha256={str(p):sha(p) for p in sorted(paths)},scope='Offline source/synthetic validation only; no Julia parsing, runtime or full admission audit')
with (N/'offline-check.json').open('x') as f:json.dump(v,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=v['all_passed'],checks=len(checks),failed=[n for n,x in checks.items() if not x])))
if not v['all_passed']:raise SystemExit(1)
