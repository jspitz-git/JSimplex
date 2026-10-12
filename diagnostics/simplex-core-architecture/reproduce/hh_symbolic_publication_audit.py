"""Exclusive S4-G postexit audit; accepted evidence must not be rerun."""
from pathlib import Path
import json,tomllib,hashlib,struct,subprocess
from fractions import Fraction as Q
root=Path.cwd();d=root/'diagnostics/simplex-core-architecture';o=d/'results/S4-G';base=root/'.superpowers/simplex-core-architecture/S4-G/publication-1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
r=tomllib.loads((base/'report.toml').read_text());p=json.loads((base/'process.json').read_text());pins_path=base.parent/'publication-1-pins.json';pins=json.loads(pins_path.read_text());pre=json.loads((o/'preflight.json').read_text());host=json.loads((o/'host-after-publication-1.json').read_text());cl=json.loads((o/'clone-source.json').read_text());inputs=json.loads((o/'exact-inputs.json').read_text())
def val(x):return Q.from_float(struct.unpack('>d',bytes.fromhex(x))[0])
def mat(q):
 A=[[Q(0) for _ in range(q['n'])] for _ in range(q['m'])]
 for j in range(q['n']):
  for k in range(q['colptr'][j]-1,q['colptr'][j+1]-1):A[q['rowval'][k]-1][j]=val(q['bits'][k])
 return A
exact=[]
expected=[(4,[5,1],False),(5,[6,1],False),(6,[1,2],False),(7,[1,2],True),(5,[1,2],False),(5,[1,2],True),(7,[8,1],False),(8,[1,3],False),(8,[1,2],False),(8,[1,2],True),(5,[1,2],False),(5,[1,2],True)]
for i,s in enumerate(r['solves']):
 A=mat(s['matrix']);rhs=list(map(val,s['rhs_bits']));z=list(map(val,s['solution_bits']));M=list(map(list,zip(*A))) if s['transpose'] else A
 residual=[sum(a*b for a,b in zip(row,z))-b for row,b in zip(M,rhs)];norm=lambda x:max(map(abs,x));anorm=max(sum(map(abs,row)) for row in M);bound=Q(1,2**46)*max(1,anorm*norm(z),norm(rhs));a,b,t=expected[i%12]
 exact.append({'label':s['label'],'source_state_recipe':A==[[a,1],[1,3]] and rhs==b and s['transpose']==t,'exact_residual_matches':residual==[Q(x.replace('//','/')) for x in s['exact_residual']],'exact_fixed_bound':norm(residual)<=bound,'bound':str(bound),'residual':list(map(str,residual))})
source=(root/'src/huangfu_hall_factorization.jl').read_text();block=source[source.index('_hh_refactor_lu!(F::Float64UMFPACK'):source.index('function copy_basis_factorization(f::HuangfuHall')]
clone=(d/'reproduce/hh_symbolic_publication_clone.jl').read_text();back=clone.replace('_s4g_refactor_lu!','_hh_refactor_lu!').replace('_s4g_refactor_backend','_hh_refactor_backend').replace('function _s4g_refactorize!','function refactorize!').replace('reuse_symbolic=_same_umfpack_pattern(F,convert(SparseMatrixCSC{Float64,Int},B))','reuse_symbolic=false')
rows=r['records'];res=[json.loads(x) for x in (base/'resources.jsonl').read_text().splitlines()];old=tomllib.loads((d/'results/S4-F/boundary-1-report.toml').read_text())['records'][0]['controls_bits']
checks={
'exit0':p['returncode']==0 and p['reason']=='exit0',
'guard_pins_unchanged':p['pins_unchanged'],
'all_pins_independently_hashed':all(Path(k).resolve()==Path(v['resolved']) and sha(k)==v['sha256'] for k,v in pins['inventory'].items()),
'pin_digest':sha(pins_path)==p['pins_sha256'],
'complete79':r['complete'] and 'error' not in r and len(r['checks'])==79 and all(r['checks'].values()),
'exact_call_budget':r['entries']==pre['calls'],
'24_solves':len(r['solves'])==24,
'2_lifecycles':len(rows)==2 and [x['side'] for x in rows]==['reference','candidate'] and all(x['complete'] for x in rows),
'exact_recipe_residuals_bounds':len(exact)==24 and all(all(x[k] for k in ['source_state_recipe','exact_residual_matches','exact_fixed_bound']) for x in exact),
'fixed_float_bounds':all(s['residual']<=s['bound'] for s in r['solves']),
'input_oracles':all(mat(x['matrices'][k])==v['matrix'] and v['det']==3*v['matrix'][0][0]-1 and list(map(Q,v['exact_solution']))==[Q(1,v['det']),Q(2*v['matrix'][0][0]-1,v['det'])] for x in rows for k,v in inputs.items()),
'candidate_clone_exact_inverse':block==back==cl['original'] and clone==cl['clone'] and sha(root/'src/huangfu_hall_factorization.jl')==cl['source_sha256'] and r['clone_sha256']==sha(d/'reproduce/hh_symbolic_publication_clone.jl'),
'actual_frozen_drivers':all((base.parent/'publication-1-source'/name).read_bytes()==(d/'reproduce'/name).read_bytes() for name in ['hh_symbolic_publication.jl','hh_symbolic_publication_clone.jl']) and sha(d/'reproduce/hh_symbolic_publication.jl')==pre['driver_sha256'],
'default_controls_preserved':all(x['control_bits']==old for x in rows),
'success_prepared_transition':all(x['live_before_success']['prepared_valid'] and not x['live_after_success']['prepared_valid'] for x in rows),
'saved_success_unchanged':all(x['saved_before_success']==x['saved_after_success'] for x in rows),
'failure_live_and_saved_unchanged':all(x['live_before_failure']==x['live_after_failure'] and x['saved_before_failure']==x['saved_after_failure'] and x['live_before_failure']['prepared_valid'] for x in rows),
'singular2_symbolic_rules':all(x['exception']=='SingularException' and x['failure_status']==1 and x['failure_symbolic_same']==(x['side']=='candidate') and x['success_symbolic_same']==(x['side']=='candidate') and not x['success_numeric_same'] and not x['failure_numeric_same'] for x in rows),
'actual_source':r['source']==str(root/'src'),
'native_loaded_pinned':r['native_sha256']==pre['native_libraries'][r['native_path']]==sha(r['native_path']),
'globals_threads':r['threads']==r['blas_threads']==1 and r['precision']==256 and r['rounding']=='RoundingMode{:Nearest}()',
'implicit_calls_scoped':r['implicit_native_scale_solves_upper_bound']==4 and r['implicit_native_scale_solves_observed']=='not instrumented',
'host_full_groups_absent':not host['identities'] and not host['members'] and not host['julia'] and host['boot_id']==p['runner']['boot_id']==p['child']['boot_id'],
'user_preserved':all(sha(k)==v for k,v in pre['user_hashes'].items()),
'no_production_test_ci_edit':not subprocess.check_output(['git','diff','master','--','src','test','.github'],text=True),
'resources':bool(res) and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in res),
}
report={'checks':checks,'all_passed':all(checks.values()),'pins':len(pins['inventory']),'exact':exact,'raw_report_sha256':sha(base/'report.toml'),'resources':{'samples':len(res),'min_available_kib':min(x['available_kib'] for x in res),'max_swap_kib':max(x['swap_used_kib'] for x in res)},'scope':'two new diagnostic HH lifecycles; no production promotion/performance/fullsuite/CI cause'}
with (o/'publication-1-audit.json').open('x') as f:json.dump(report,f,indent=2)
for name in ['report.toml','run.log','process.json','resources.jsonl']:
 with (o/('publication-1-'+name)).open('xb') as f:f.write((base/name).read_bytes())
for src,dst in [(pins_path,'publication-1-pins.json'),(d/'reproduce/hh_symbolic_publication.jl','driver.jl.txt'),(d/'reproduce/hh_symbolic_publication_clone.jl','clone.jl.txt'),(Path('/tmp/jsimplex-hh-publication-attempt.py'),'launcher.py.txt'),(Path('/tmp/s4-g-preflight.py'),'preflight.py.txt'),(Path('/tmp/s4-g-prepare.py'),'prepare.py.txt')]:
 with (o/dst).open('xb') as f:f.write(src.read_bytes())
print(json.dumps({k:v for k,v in report.items() if k!='exact'},indent=2));raise SystemExit(0 if report['all_passed'] else 1)
