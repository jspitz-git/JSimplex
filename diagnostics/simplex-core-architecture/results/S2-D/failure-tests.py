"""Synthetic validation tests only; no subprocess or Julia invocation."""
import copy,json,tomllib
from common import *
from audit import cost_ok,validate_records
checks={}
f=tomllib.loads((D/'fixtures.toml').read_text())['fixtures'][0]
samples=[dict(fixture=f['id'],round=r,side=s,measured=r>4,calls=16,ok=True,seconds=0.1,bytes=128,allocations=2,gc_seconds=0.,compile_seconds=0.,recompile_seconds=0.) for r in range(1,13) for s in (['reference','candidate'] if r%2 else ['candidate','reference'])]
base=dict(fixture=f['id'],samples=samples,inputs_preserved=True,m=f['m'],n=f['n'],nnz=len(f['rowval']),input_sha256=f['nzval_sha256'])
checks['valid_cost_schema']=cost_ok(base,f)
for name,key,value in [('compile','compile_seconds',0.1),('recompile','recompile_seconds',0.1),('nan_time','seconds',float('nan')),('negative_bytes','bytes',-1),('bool_bytes','bytes',True),('wrong_calls','calls',15),('false_output','ok',False),('wrong_measured','measured',False),('wrong_side','side','reference')]:
 x=copy.deepcopy(base);x['samples'][9][key]=value;checks['reject_'+name]=not cost_ok(x,f)
for name in ['missing','duplicate','reverse']:
 x=copy.deepcopy(base)
 if name=='missing':x['samples'].pop()
 if name=='duplicate':x['samples'][9]=x['samples'][8]
 if name=='reverse':x['samples'].reverse()
 checks['reject_'+name]=not cost_ok(x,f)
x=copy.deepcopy(base);x['inputs_preserved']=False;checks['reject_mutated_input']=not cost_ok(x,f)
p=dict(reason='exit0',returncode=0,pins_unchanged=True,elapsed_including_launch=1.,terminal_memory=dict(available_kib=7*1024**2,swap_used_kib=0))
checks['valid_terminal']=terminal_ok(p)
for name,k,v in [('late','elapsed_including_launch',181),('nan','elapsed_including_launch',float('nan')),('return_bool','returncode',False),('pins','pins_unchanged',False),('reason','reason','terminal_memory_guard')]:
 x=copy.deepcopy(p);x[k]=v;checks['reject_terminal_'+name]=not terminal_ok(x)
x=copy.deepcopy(p);x['terminal_memory']['available_kib']=5*1024**2;checks['reject_terminal_ram']=not terminal_ok(x)
x=copy.deepcopy(p);x['terminal_memory']['swap_used_kib']=2*1024**2;checks['reject_terminal_swap']=not terminal_ok(x)
checks['reject_empty_allowance']=not allowance_valid({},'x',{})
checks['reject_missing_records']=not validate_records({}, {}, {}, {}, 'x','x')
checks['reject_empty_manifest']=not manifest_ok({}, {})
with (D/'failure-tests.json').open('x') as out:json.dump({'checks':checks,'all_passed':all(checks.values()),'scope':'NEW synthetic Python records only; no launcher, guard or Julia execution'},out,indent=2);out.write('\n')
print(len(checks),checks);assert all(checks.values())
