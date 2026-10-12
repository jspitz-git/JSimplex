from pathlib import Path
from fractions import Fraction as Q
import json,tomllib,sys,hashlib,importlib.util,math,re,shutil
sys.dont_write_bytecode=True
root=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');d=root/'diagnostics/simplex-core-architecture';name=sys.argv[1];base=root/'.superpowers/simplex-core-architecture/S6-X'/name;out=d/'results/S6-X'
r=tomllib.loads((base/'report.toml').read_text());p=json.loads((base/'process.json').read_text());pins=json.loads((base/'pins.json').read_text());log=(base/'run.log').read_text();source=(root/'test/native_phase_transfer_tests.jl').read_text()
s=importlib.util.spec_from_file_location('g',d/'reproduce/guarded_run.py');g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
def extract(title):
 marker='@testset "'+title+'" begin';return marker+source.split(marker,1)[1].split('\n@testset',1)[0]
original='\n'.join(extract(t) for t in ['Artificial exchanges certify native reconstruction before export','Reliable artificial exchanges need no reconstruction recovery'])
expected=original.replace('phase,mapping,original,policy=artificial_exchange_roundoff_fixture(T,manager)','diagnostics=diagnostics_for_capture()\n        phase,mapping,original,policy=artificial_exchange_roundoff_fixture(T,manager;diagnostics)').replace('JSimplex.SimplexDiagnostics()','diagnostics_for_capture()').replace('JSimplex.remove_artificials!','observed_remove!')
helper='function artificial_exchange_roundoff_fixture'+source.split('function artificial_exchange_roundoff_fixture',1)[1].split('\n@testset',1)[0]
checks={'process_completed':p['returncode'] in (0,1) and p['reason']=='exit'+str(p['returncode']) and p['pins_unchanged'],'exit_matches_oracle':(p['returncode']==1)==('Test Failed' in log),'pins_guard':g.pins_match(pins),'pins_independent':all(hashlib.sha256(Path(k).read_bytes()).hexdigest()==v['sha256'] and str(Path(k).resolve())==v['resolved'] for k,v in pins['inventory'].items()),'actual_source':r['source']==str(root/'src/JSimplex.jl'),'test_hash':r['test_sha256']==hashlib.sha256(source.encode()).hexdigest(),'exact_helper':r['helper']==helper,'original_oracle':r['original_oracle']==original,'only_passive_routing':r['executed_oracle']==expected,'no_harness_errors':'Error During Test' not in log and 'ERROR: LoadError: UndefVarError' not in log,'one_thread':r['julia_threads']==r['blas_threads']==1,'globals':r['globals_preserved']}
paths=set(pins['files'])
for t in pins['trees']:paths.update(str(v) for v in Path(t).rglob('*') if v.is_file())
checks['inventory_membership']=paths==set(pins['inventory'])
records=r['records'];managers={'pfi','forrest_tomlin','suhl_suhl','bartels_golub'}
checks['twelve_complete']=len(records)==12 and all('accepted' in c for c in records)
checks['exact_case_grid']={(c['scalar'],c['manager'],c['max_refinements']) for c in records}=={(T,m,k) for T,k in [('Float32',3),('Float64',3),('Float32',0)] for m in managers}
A0=[[8,-2,0,1,-3,2],[2,6,1,2,-2,-2],[1,-2,3,0,-1,3],[3,-1,0,5,-2,-2],[0,0,-1,0,6,-3],[0,0,-1,-2,-1,8]]
def matrix(v):
 m,n=v['m'],v['n'];a=[[Q(0) for _ in range(n)] for _ in range(m)]
 for j in range(n):
  for k in range(v['colptr'][j]-1,v['colptr'][j+1]-1):a[v['rowval'][k]-1][j]=Q(v['nzval'][k])
 return a
def exact(v):
 if not v.get('workspace'):return {'workspace':False}
 a=matrix(v);m,n=v['m'],v['n'];a=[row+[Q(-int(i==j)) for j in range(m)] for i,row in enumerate(a)]
 if not all(math.isfinite(x) for k in ('primal','rho','costs') for x in v[k]):return {'finite':False}
 x=list(map(Q,v['primal']));basis=[b-1 for b in v['basis']];nb=[j for j in range(n+m) if j not in basis];b=[[row[j] for j in basis] for row in a]
 rhs=[-sum(row[j]*x[j] for j in nb) for row in a]
 bounded=[Q(v['lower']['values'][j]) if v['states'][j]=='AT_LOWER' else Q(v['upper']['values'][j]) if v['states'][j]=='AT_UPPER' else Q(0) for j in range(n+m)]
 rhs_bounds=[-sum(row[j]*bounded[j] for j in nb) for row in a]
 xb=[x[j] for j in basis];rho=list(map(Q,v['rho']));cost=[Q(v['costs'][j]) for j in basis]
 residual=[rhs[i]-sum(b[i][j]*xb[j] for j in range(m)) for i in range(m)]
 dual=[cost[j]-sum(b[i][j]*rho[i] for i in range(m)) for j in range(m)]
 bound_violations=[max(Q(0),Q(v['lower']['values'][j])-x[j] if v['lower']['finite'][j] else Q(0),x[j]-Q(v['upper']['values'][j]) if v['upper']['finite'][j] else Q(0)) for j in range(n+m)]
 scale=[abs(rhs[i])+sum(abs(b[i][j]*xb[j]) for j in range(m)) for i in range(m)]
 ratios=[abs(residual[i])/scale[i] if scale[i] else Q(0) for i in range(m)]
 return {'finite':True,'basis':v['basis'],'rhs_from_nonbasic_point':list(map(str,rhs)),'rhs_from_bounds':list(map(str,rhs_bounds)),'rhs_agree':rhs==rhs_bounds,'primal_residual':list(map(str,residual)),'dual_residual':list(map(str,dual)),'primal_exact':not any(residual),'dual_exact':not any(dual),'bound_violation':list(map(str,bound_violations)),'bounds_within_primal_tolerance':max(bound_violations)<=Q(v['primal_tolerance']),'max_exact_relative_indicator':str(max(ratios)),'indicator_within_solve_tolerance':max(ratios)<=Q(v['solve_tolerance'])}
checks['original_fixture_matrix']=all(matrix(c['before_original'])==[[Q(x) for x in row] for row in A0] and matrix(c['before_phase'])==[[Q(x) for x in row+[row[5]]] for row in A0] for c in records)
checks['initial_basis_and_point']=all(c['before_phase']['basis']==[1,2,3,4,5,7] and c['before_phase']['primal'][:7]==[1,1,0,0,0,0,0] for c in records)
checks['default_options_policy']=all(c['options']['algorithm']==':primal' and c['options']['basis_refactorization']==':native' and c['options']['basis_update']==':'+c['manager'] and c['policy']['max_refinements']==str(c['max_refinements']) and c['policy']['solve_refinement']=='false' and c['policy']['hypersparse']=='false' for c in records)
checks['work_monotonic']=all(c['after_original']['iterations']>=c['after_phase']['iterations'] and c['after_original']['refactorizations']>=c['after_phase']['refactorizations'] for c in records)
fields=('basis','states','primal','costs','prices','lower','upper')
checks['failed_publication_preserved']=all(c['accepted'] or all(c['before_original'][k]==c['after_original'][k] for k in fields) for c in records)
checks['snapshot_roles']=all(e['role'] in ('phase','original','temporary') for c in records for e in c['events'])
summaries=[]
for c in records:
 summaries.append({'scalar':c['scalar'],'manager':c['manager'],'budget':c['max_refinements'],'accepted':c['accepted'],'phase':exact(c['after_phase']),'original':exact(c['after_original']),'events':[{'event':e['event'],'role':e['role'],'iterations':e['state'].get('iterations'),'refactorizations':e['state'].get('refactorizations'),'equations':exact(e['state'])} for e in c['events']],'kernels':{k:v for k,v in c['kernels'].items() if v},'counts':{k:v for k,v in c['counts'].items() if v}})
checks['finite_endpoint']=all(c['phase']['finite'] and c['original']['finite'] for c in summaries)
old=json.loads((d/'results/S6-W/green-1-pins.json').read_text());shared=[k for k in old['inventory'] if k in pins['inventory'] and ('/src/' in k or k.endswith(('Project.toml','Manifest.toml','LocalPreferences.toml','julia.sh','/bin/julia')))];checks['shared_runtime_source_environment']=all(old['inventory'][k]==pins['inventory'][k] for k in shared)
audit={'checks':checks,'all_passed':all(checks.values()),'pin_count':len(pins['inventory']),'shared_count':len(shared),'shared_paths':shared,'summary':[l for l in log.splitlines() if re.search(r'\|\s+\d',l)],'cases':summaries,'scope':'Exact equations of owned observations, not production quality replay, hidden trajectory/observer neutrality or x64 backend proof; refactor events precede solves and rho may be stale.'}
with (out/(name+'-audit.json')).open('x') as f:json.dump(audit,f,indent=2);f.write('\n')
for n in ('report.toml','pins.json','process.json','run.log'):shutil.copyfile(base/n,out/(name+'-'+n))
shutil.copyfile(root/'test/native_phase_transfer_tests.jl',out/(name+'-test.jl'));shutil.copyfile(d/'reproduce/phase_transfer_reachability.jl',out/(name+'-driver.jl'))
print(json.dumps({k:v for k,v in audit.items() if k not in ('cases','shared_paths')},indent=2));assert audit['all_passed']
