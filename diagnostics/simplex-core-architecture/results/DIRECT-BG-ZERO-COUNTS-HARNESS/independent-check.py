from pathlib import Path
import sys, json, hashlib, copy, re
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/simplex-core-architecture/results/DIRECT-BG-ZERO-COUNTS-HARNESS')
sys.path.insert(0,str(D))
import oracle, audit
checks=[]
def chk(name, value):
    if not value: raise AssertionError(name)
    checks.append(name)
def refuse(name, fn):
    try: fn()
    except (ValueError, RuntimeError, TypeError, KeyError): checks.append(name); return
    raise AssertionError('accepted '+name)
def metric(): return dict(seconds=.0001,bytes=16,events=1,gc_seconds=0.,compile_seconds=0.,recompile_seconds=0.)
def node(name,n): return dict(name=name,**{'pass':n,'fail':0,'error':0,'broken':0,'children':[]})
loaded={'JSimplex':'/expected/JSimplex.jl','Test':'/expected/Test.jl','TOML':'/expected/TOML.jl','LinearAlgebra':'/expected/LinearAlgebra.jl'}
suite=dict(tree=node('zero-count candidate',0),failure_count=0,failures=[])
suite['tree']['children']=[node(n,c) for n,c in zip(oracle.NAMES,(7,300,10,26,7))]
rows=[]
for i,(case,phase,pair,arm) in enumerate(oracle.SCHEDULE,1):
    observed={'counters':[0]*20}
    if case=='constructor':observed['fresh_owner']=True
    elif case!='zeros':observed.update(start=1,count=0,accepted=False,reason='dimensions',finite=True)
    rows.append(dict(index=i,case=case,phase=phase,pair=pair,arm=arm,inner_bytes=32,inner_events=1,assignment_ok=True,decision_ok=True,observed=observed,bytes_wrapper=metric(),events_wrapper=metric(),consumed_result=metric()))
payload={n:metric() for n in oracle.PREPARATION}
payload.update({'tests.toml':suite,'raw.toml':dict(schema=1,complete=True,fatal='',qualification='zero_counts_diagnostic',records=copy.deepcopy(rows),loaded=loaded,input_unchanged=True,replacement_unchanged=True,tests=copy.deepcopy(suite))})
payload.update({f'record-{i}.toml':v for i,v in enumerate(rows,1)})
result=oracle.validate(payload,loaded)
chk('exact_60_rows_69_files',len(result['records'])==60 and len(payload)==69)
chk('source_calls_204_not_runtime_claim',result['source_schedule_invocations']==204)
chk('350_assertions',result['structural_assertions']==350)
chk('no_qualification',result['p011_accepted'] is False and result['red_accepted'] is False)
for case in oracle.CASES:
    for arm in ('reference','candidate'):
        chk('four_samples_'+case+'_'+arm,len(result['descriptive_sample_counters'][case][arm]['inner_bytes'])==4)
for i,row in enumerate(rows,1):
    def altered(mut):
        q=copy.deepcopy(payload); mut(q[f'record-{i}.toml']);q['raw.toml']['records'][i-1]=copy.deepcopy(q[f'record-{i}.toml']);return q
    for slot in range(20):
        for bad in (False,1):
            q=altered(lambda r:r['observed']['counters'].__setitem__(slot,bad))
            refuse(f'row{i}_counter{slot}_{bad}',lambda q=q:oracle.validate(q,loaded))
    for key in ('inner_bytes','inner_events'):
        for bad in (True,-1,1.25,2**63):
            q=altered(lambda r:r.__setitem__(key,bad))
            refuse(f'row{i}_{key}_{bad}',lambda q=q:oracle.validate(q,loaded))
    if row['case']=='constructor':
        for bad in (False,1,'true'):
            q=altered(lambda r:r['observed'].__setitem__('fresh_owner',bad))
            refuse(f'constructor{i}_{bad}',lambda q=q:oracle.validate(q,loaded))
for i in (5,17,29,41,53):
    q=copy.deepcopy(payload)
    q[f'record-{i}.toml']['consumed_result']['gc_seconds']=.001
    q['raw.toml']['records'][i-1]=copy.deepcopy(q[f'record-{i}.toml'])
    v=oracle.validate(q,loaded);r=q[f'record-{i}.toml']
    chk('gc_retained_excluded_'+str(i),i not in v['descriptive_sample_counters'][r['case']][r['arm']]['clean_wrapper_indices'])
mem=dict(available_kib=8*1024**2,swap_used_kib=0)
chk('resource_good',audit.resource_records([dict(mem,elapsed=.5)],mem,1.))
for k in ('available_kib','swap_used_kib'):
    for bad in (True,-1,1.1):
        term=dict(mem);term[k]=bad
        refuse(f'resource_terminal_{k}_{bad}',lambda term=term:audit.resource_records([dict(mem,elapsed=.5)],term,1.))
for bad in (True,float('nan'),float('inf'),-1,293):
    refuse('resource_elapsed_'+repr(bad),lambda bad=bad:audit.resource_records([dict(mem,elapsed=.5)],mem,bad))
# Julia source inspection only: no Julia runtime, parser, import, query, compile, or IR.
ops=(D/'operations.jl').read_text()
chk('constructor_dictionary_accepts_bool',bool(re.search(r'function observed\(::Val\{:constructor\},v\)\s+Dict\{String,Any\}',ops)))
chk('five_driver_cases','(Val(:zeros),Val(:constructor),Val(:dimensions),Val(:eligibility),Val(:original))' in (D/'driver.jl').read_text())
chk('top_level_includes_before_module', (D/'driver.jl').read_text().index('const CANDIDATE_LOAD') < (D/'driver.jl').read_text().index('module ZeroDriver'))
res=dict(all_passed=True,count=len(checks),checks=checks,scope='Independent synthetic Python payload/resource rejection and Julia text inspection only; no launcher/outer/seal/guard entrypoint, no Julia execution.',sha256={str(D/n):hashlib.sha256((D/n).read_bytes()).hexdigest() for n in ['oracle.py','audit.py','control.py','operations.jl','driver.jl']},reviewer_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
Path('/tmp/zero-counts-independent-review.json').write_text(json.dumps(res,indent=2)+'\n')
print(json.dumps(dict(all_passed=True,count=len(checks))))
