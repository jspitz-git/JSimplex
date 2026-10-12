"""Exclusive postexit S4-K audit. Never rerun against accepted evidence."""
from pathlib import Path
from fractions import Fraction as Q
import json,tomllib,hashlib,struct,math,subprocess
r=Path.cwd();d=r/'diagnostics/simplex-core-architecture';o=d/'results/S4-K';raw=r/'.superpowers/simplex-core-architecture/S4-K/nonfinite-1';v=tomllib.loads((o/'nonfinite-1-report.toml').read_text());p=json.loads((o/'nonfinite-1-process.json').read_text());pins=json.loads((o/'nonfinite-1-pins.json').read_text());pre=json.loads((o/'preflight.json').read_text());oracle=json.loads((o/'exact-inputs.json').read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();decode=lambda h:struct.unpack('>d',bytes.fromhex(h))[0]
exact=[]
for z in v['solves']:
 M=[[Q(4),Q(1)],[Q(1),Q(3)]];b=list(map(Q,oracle['rhs']));x=[Q(decode(h)) for h in z['solution_bits']];res=[sum(M[i][j]*x[j] for j in range(2))-b[i] for i in range(2)];bound=64*Q(1,2**52)*max(Q(1),max(sum(abs(a) for a in row) for row in M)*max(map(abs,x)),max(map(abs,b)));exact.append({'label':z['label'],'residuals':list(map(str,res)),'bound':str(bound),'passed':max(map(abs,res))<=bound,'runtime_bound_matches':z['bound']==64*2**-52*max(1,5*max(abs(decode(h)) for h in z['solution_bits']),2)})
source=(r/'src/huangfu_hall_factorization.jl').read_text();sl=source[source.index('_hh_refactor_lu!(F::Float64UMFPACK'):source.index('function copy_basis_factorization(f::HuangfuHall')];clone=(d/'reproduce/hh_nonfinite_reuse_clone.jl').read_text();inv=clone.replace('_s4k_refactor_lu!','_hh_refactor_lu!').replace('_s4k_refactor_backend','_hh_refactor_backend').replace('function _s4k_refactorize!','function refactorize!').replace('reuse_symbolic=_same_umfpack_pattern(F,convert(SparseMatrixCSC{Float64,Int},B))','reuse_symbolic=false');records=v['records'];resources=[json.loads(s) for s in (o/'nonfinite-1-resources.jsonl').read_text().splitlines()]
checks={
 'process_exit':p['returncode']==0 and p['reason']=='exit0' and p['pins_unchanged'],
 'runtime49':v['complete'] and len(v['checks'])==49 and all(v['checks'].values()) and 'error' not in v,
 'counts':v['entries']==oracle['counts_if_all_qualify'],
 'four_cases_order':len(records)==4 and [z['label'] for z in records]==oracle['case_order'] and all(z['complete'] for z in records),
 'eight_solve_records':len(exact)==8 and [z['label'] for z in v['solves']]==[label+'_'+mode for label in oracle['case_order'] for mode in ['FTRAN','BTRAN']],
 'exact_input_bits':all(z['B0']=={'m':2,'n':2,'colptr':oracle['colptr'],'rowval':oracle['rowval'],'bits':oracle['B0_nzval_bits']} and z['target']=={'m':2,'n':2,'colptr':oracle['colptr'],'rowval':oracle['rowval'],'bits':[oracle['target_bits'][i//2],*oracle['B0_nzval_bits'][1:]]} for i,z in enumerate(records)),
 'solve_binding':all(z['matrix']==records[i//2]['B0'] and z['rhs_bits']==['3ff0000000000000','4000000000000000'] and z['transpose']==bool(i%2) for i,z in enumerate(v['solves'])),
 'fixed_exact_residuals':all(z['passed'] and z['runtime_bound_matches'] for z in exact),
 'qualified_errors':all(z['exception'] in ['SingularException','JSimplex._UnreliableBasisSolve'] or (z['exception']=='ArgumentError' and z['message']=='ArgumentError: invalid matrix') for z in records),
 'discarded':all(z['discarded'] for z in records),
 'owned_state_preserved':all(z['before']==z['after'] for z in records),
 'empty_histories_pools':all(not z['before']['updates'] and not z['before']['u_pool']['pairs'] and not z['before']['v_pool']['pairs'] and z['before']['shared']==0 for z in records),
 'controls_same':all(z['control_before']==z['control_after']==records[0]['control_before'] for z in records),
 'actual_symbolic_identity':all(z['symbolic_same']==z['candidate'] and not z['numeric_same'] for z in records),
 'owned_native_target':all(z['native_after']=={'m':2,'n':2,'colptr':[0,2,4],'rowval':[0,1,0,1],'bits':z['target']['bits']} for z in records),
 'single_threads_globals':v['threads']==v['blas_threads']==1 and v['precision']==256 and v['rounding']=='RoundingMode{:Nearest}()',
 'actual_source':Path(v['source']).resolve()==(r/'src').resolve(),
 'full551pins':len(pins['inventory'])==551 and all(sha(k)==x['sha256'] and str(Path(k).resolve())==x['resolved'] for k,x in pins['inventory'].items()),
 'raw_portable4':all((raw/n).read_bytes()==(o/('nonfinite-1-'+n)).read_bytes() for n in ['report.toml','process.json','run.log','resources.jsonl']),
 'driver_clone_source':sha(d/'reproduce/hh_nonfinite_reuse.jl')==pre['driver_sha256'] and sha(d/'reproduce/hh_nonfinite_reuse_clone.jl')==pre['clone_sha256']==v['clone_sha256'] and inv==sl==(o/'production-refactor.txt').read_text(),
 'native_pinned':v['native_sha256']==pre['native_libraries'][v['native_path']]==sha(v['native_path']),
 'oracle_prelaunch':sha(o/'exact-inputs.json')==pre['oracle_sha256'] and pins['created']<p['started'],
 'user6':all(sha(k)==h for k,h in pre['user_hashes'].items()),
 'source_test_CI_master':not subprocess.check_output(['git','diff','master','--','src','test','.github'],text=True),
 'postexit_host':not json.loads((o/'host-postexit.json').read_text())['matches'],
 'resource_guard':bool(resources) and all(z['available_kib']>=6*1024**2 and z['swap_used_kib']<=1024**2 for z in resources),
}
result={'checks':checks,'all_passed':all(checks.values()),'exact_solves':exact,'observed_exceptions':[z['exception'] for z in records],'observed_status':[z['native_status'] for z in records],'resource_samples':len(resources),'raw_sha256':sha(raw/'report.toml'),'auditor_sha256':sha(__file__),'auditor_scope':'written after exit; separate hash, NOT a launch pin','implicit_work':'8native entries source-derived; target numeric<=4/extraction<=4/orientation total<=8 bounds, not instrumentation'}
with (o/'nonfinite-1-audit.json').open('x') as f:json.dump(result,f,indent=2)
print({'checks':len(checks),'failed':[k for k,x in checks.items() if not x],'exact_nonzero':sum(any(Q(q)!=0 for q in z['residuals']) for z in exact),'samples':len(resources)});assert result['all_passed']
