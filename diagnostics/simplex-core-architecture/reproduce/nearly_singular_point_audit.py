from pathlib import Path
import json,tomllib,hashlib,importlib.util,sys,shutil
from fractions import Fraction as F
from collections import Counter
sys.dont_write_bytecode=True
root=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');d=root/'diagnostics/simplex-core-architecture';base=root/'.superpowers/simplex-core-architecture/S6-Q/trace-1';out=d/'results/S6-Q'
r=tomllib.loads((base/'report.toml').read_text());p=json.loads((base/'process.json').read_text());pins=json.loads((base/'pins.json').read_text());saved=tomllib.loads((d/'results/S6-N/census-2-report.toml').read_text());control=next(x for x in saved['records'] if x['type']=='Float64');pre=json.loads((out/'control-preflight.json').read_text())
Q=lambda s:F(s.replace('//','/'));checks={}
s=importlib.util.spec_from_file_location('guard',d/'reproduce/guarded_run.py');g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
checks['guard_exit0']=p['returncode']==0 and p['reason']=='exit0' and p['pins_unchanged']
checks['pins_guard']=g.pins_match(pins)
checks['pins_independent']=all(hashlib.sha256(Path(k).read_bytes()).hexdigest()==v['sha256'] and str(Path(k).resolve())==v['resolved'] for k,v in pins['inventory'].items())
paths=set(pins['files'])
for t in pins['trees']:paths.update(str(x) for x in Path(t).rglob('*') if x.is_file())
checks['inventory_membership']=paths==set(pins['inventory'])
checks['control_preflight']=pre['all_passed'] and all(pre['checks'].values()) and pre['count']==517
checks['actual_source']=r['source']==str(root/'src/JSimplex.jl')
checks['saved_control_hash']=r['control_sha256']==hashlib.sha256((d/'results/S6-N/census-2-report.toml').read_bytes()).hexdigest()
checks['source_comparability']=all(pins['inventory'][k]==v for k,v in json.loads((d/'results/S6-N/census-2-pins.json').read_text())['inventory'].items() if k in pre['checks'])
checks['runtime_threads']=r['julia_version']==saved['julia_version'] and r['arch']==saved['arch'] and r['julia_threads']==r['blas_threads']==saved['julia_threads']==saved['blas_threads']==1
checks['model_preserved']=r['model_before']==r['model_after']==control['model_before']
checks['default_options_policy']=r['options']==control['options'] and r['policy']==control['policy']
checks['endpoint_match']=r['solver_returned'] and r['endpoint_equal'] and all(r[k]==control[k] for k in ['status','primal','objective','iterations','refactorizations'])
checks['globals_and_nonworkspace']=r['globals_preserved'] and r['nonworkspace_probe_passed']
events=r['events'];counts=Counter(e['event'] for e in events)
checks['eleven_observer_events']=len(events)==11 and all(counts[k]==r['counts'][k] for k in counts)
checks['expected_event_sequence']=[e['event'] for e in events]==['refactor_initial','phase_dual','phase_auxiliary','pricing','pivot_proposed','pivot_completed','pricing','pivot_proposed','pivot_completed','refactor_other','certification']
summary=[];matrices=[]
for i,e in enumerate(events,1):
 m,n=e['matrix_shape'];A=[[F(0) for _ in range(n)] for _ in range(m)]
 for j in range(n):
  for k in range(e['matrix_colptr'][j]-1,e['matrix_colptr'][j+1]-1):A[e['matrix_rowval'][k]-1][j]=Q(e['matrix_nzval'][k])
 matrices.append(A);x=list(map(Q,e['primal']));rowfac=list(map(Q,e['row_scaling']));colfac=list(map(Q,e['column_scaling']));origx=[x[j]*colfac[j] for j in range(n)]
 origA=[[F(1,2**20),F(1,2**20)],[F(1,2**20),F(1,2**20)+F(1,2**43)]]
 assert all(A[i][j]*rowfac[i]/colfac[j]==origA[i][j] for i in range(m) for j in range(n))
 rows=[sum(origA[i][j]*origx[j] for j in range(n)) for i in range(m)]
 residual=[sum(A[i][j]*x[j] for j in range(n))-x[n+i] for i in range(m)]
 violation=[max(abs(v)-1,0) for v in rows]
 summary.append({'index':i,'event':e['event'],'iterations':e['iterations'],'refactorizations':e['refactorizations'],'basis_indices':e['basis_indices'],'staged':e['staged_workspace'],'update_count':len(e['updates']),'original_rows':list(map(str,rows)),'original_bound_violations':list(map(str,violation)),'working_equation_residual':list(map(str,residual))})
checks['scaling_reconstructs_original']=True
checks['first_bound_violation_at_certification']=next(i['index'] for i in summary if any(F(v)!=0 for v in i['original_bound_violations']))==11
checks['first_working_equation_residual']=next(i['index'] for i in summary if any(F(v)!=0 for v in i['working_equation_residual']))==6
last=events[-1];trial=events[-2]
checks['no_eta_at_handoff']=trial['staged_workspace'] and not last['staged_workspace'] and trial['updates']==last['updates']==[] and trial['basis_indices']==last['basis_indices']==[1,2]
checks['same_matrix_model_identity']=trial['model_id']==last['model_id'] and matrices[-2]==matrices[-1]
checks['known_bound_states']=trial['basis_states']==last['basis_states']==['BASIC','BASIC','AT_LOWER','AT_UPPER']
checks['final_scratch_primal_matches']=last['scratch_row_solution']==last['primal'][:2] and list(map(Q,last['primal'][:2]))==[Q(x['exact']) for x in r['primal']]
checks['final_gap_identity']=Q(r['objective']['exact'])+2**44==-F(1,16) and F(summary[-1]['original_bound_violations'][1])==F(1,2**47)
checks['original_test_unchanged']='5      5' in (base/'run.log').read_text() and 'Test Failed' not in (base/'run.log').read_text()
audit={'checks':checks,'all_passed':all(checks.values()),'pin_count':len(pins['inventory']),'events':summary,'replay_inputs':{'matrix_column_major':trial['matrix_nzval'],'primal_rhs_derived_from_bound_states':['-1048576','1048576'],'dual_rhs_from_costs':['0','-1'],'note':'RHS derived offline from current basis states/bounds; captured scratch_row_rhs at certification is overwritten for BTRAN and is not primal RHS.'},'limits':'First observed bound violation, not first arithmetic error/cause. Scratch rho is not an independently validated runtime witness. No opaque factor/permutations/internal scaling captured; endpoint equality is not observer neutrality.'}
with (out/'trace-1-audit.json').open('x') as f:json.dump(audit,f,indent=2);f.write('\n')
for name in ['report.toml','run.log','pins.json','process.json']:shutil.copyfile(base/name,out/('trace-1-'+name))
shutil.copyfile(d/'reproduce/nearly_singular_point_trace.jl',out/'trace-1-driver.jl')
print(json.dumps({'checks':checks,'all_passed':all(checks.values()),'pin_count':len(pins['inventory']),'first_residual':summary[5],'final':summary[-1]},indent=2))
