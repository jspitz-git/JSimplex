from pathlib import Path
from fractions import Fraction as F
import sys,json,tomllib,hashlib,importlib.util,re,shutil
sys.dont_write_bytecode=True
root=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');d=root/'diagnostics/simplex-core-architecture';name=sys.argv[1];b=root/'.superpowers/simplex-core-architecture/S6-U'/name;o=d/'results/S6-U'
r=tomllib.loads((b/'report.toml').read_text());p=json.loads((b/'process.json').read_text());pins=json.loads((b/'pins.json').read_text());log=(b/'run.log').read_text()
s=importlib.util.spec_from_file_location('guard',d/'reproduce/guarded_run.py');g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
checks={'exit':p['reason']=='exit0' and p['returncode']==0 and p['pins_unchanged'],'guard_pins':g.pins_match(pins),'independent_pins':all(hashlib.sha256(Path(k).read_bytes()).hexdigest()==v['sha256'] and str(Path(k).resolve())==v['resolved'] for k,v in pins['inventory'].items()),'source':r['source']==str(root/'src/JSimplex.jl'),'threads':r['julia_threads']==r['blas_threads']==1,'globals':r['globals_preserved']}
paths=set(pins['files'])
for tree in pins['trees']:paths.update(str(v) for v in Path(tree).rglob('*') if v.is_file())
checks['inventory_membership']=paths==set(pins['inventory'])
src=(root/'test/legacy_primal_direction_price_tests.jl').read_text();mark='@testset "A repeated price disagreement cannot renew the recovery budget" begin'
checks['test_hash']=hashlib.sha256(src.encode()).hexdigest()==r['test_sha256']
checks['exact_original']=r['original_source']==mark+src.split(mark,1)[1].split('\n@testset',1)[0]
helper='function native_price_roundoff_fixture'
checks['exact_helper']=r['helper_source']==helper+src.split(helper,1)[1].split('\n@testset',1)[0]
# Invert only the explicitly declared diagnostic additions. No oracle rewriting.
added=('events=Dict[]','push!(events,','event==:primal_prices_corrected && push!','before=snapshot(ws)','initial_counts=','initial_kernels=','initial_event_count=','push!(RECORDS,')
recovered=''.join(line for line in r['observed_source'].splitlines(keepends=True) if not line.strip().startswith(added)).replace(';kernel_timing=true,observer=',';observer=')
checks['exact_oracle_after_removing_recording']=recovered==r['original_source']
checks['twenty_original_assertions']=re.search(r'\|\s+20\s+20\s+',log) is not None and 'Test Failed' not in log and 'Error During Test' not in log and r['original_source'].count('@test ')==5
records=r['records'];checks['four_managers']=[a['manager'] for a in records]==['pfi','forrest_tomlin','suhl_suhl','bartels_golub']
sequence=['pricing','pivot_proposed','correction_attempt','primal_prices_corrected','primal_prices_corrected','pricing','pivot_proposed','pivot_rejected','pricing']
exact=[]
for a in records:
 before=a['before'];after=a['after'];events=a['events'][a['initial_event_count']:];A=[[F(v) for v in row] for row in a['A_rows']];B=[[row[j-1] for j in before['basis']] for row in A]
 def residual(state):return [F(state['costs'][j-1])-sum(B[i][k]*F(state['rho'][i]) for i in range(6)) for k,j in enumerate(state['basis'])]
 proposals=[]
 for e in events:
  if e['event'] not in ('correction_attempt','pivot_rejected'):continue
  st=e['state'];j=st['selected_entering']-1;x=list(map(F,st['direction']))
  proposals.append({'boundary':e['event'],'entering':j+1,'selected_row':st['selected_row'],'cached_price':str(F(st['prices'][j])),'exact_implied_price':str(F(st['costs'][j])-sum(F(st['costs'][idx-1])*x[k] for k,idx in enumerate(st['basis']))),'exact_direction_residual':[str(A[i][j]-sum(B[i][k]*x[k] for k in range(6))) for i in range(6)]})
 exact.append({'manager':a['manager'],'initial_dual_residual':[str(v) for v in residual(before)],'published_dual_residual':[str(v) for v in residual(events[3]['state'])],'proposals':proposals})
 prefix=a['manager']+':'
 checks[prefix+'sequence']=[e['event'] for e in events]==sequence and events[3]['boundary']=='before_original_callback' and events[4]['boundary']=='after_original_callback'
 checks[prefix+'publication_injection_only']=all(events[3]['state'][k]==events[4]['state'][k] for k in events[3]['state'] if k!='prices') and events[3]['state']['prices'][6]==0 and events[4]['state']['prices'][6]==-1 and all(x==y for i,(x,y) in enumerate(zip(events[3]['state']['prices'],events[4]['state']['prices'])) if i!=6)
 checks[prefix+'budget_oracle']=a['status']=='NUMERICAL_ERROR' and a['message']=='primal reduced cost disagrees with its direction' and a['counts']['primal_prices_corrected']==a['counts']['correction_attempt']==1 and after['iterations']==0 and not after['rejected_entering']
 checks[prefix+'point_basis_unchanged']=all(before[k]==after[k] for k in ('primal','costs','basis','states','iterations','refactorizations','updates'))
 checks[prefix+'residual_improved']=any(residual(before)) and not any(residual(events[3]['state'])) and after['rho']==[1,1,0,0,0,0]
 checks[prefix+'work']=a['iteration_kernels']['ftran']==6 and a['iteration_kernels']['btran']==2 and a['iteration_kernels']['pricing']==3 and a['iteration_kernels']['refactorization']==0 and a['iteration_counts']['pivot_proposed']==2 and a['iteration_counts']['pivot_rejected']==1 and a['iteration_counts']['pricing_scored_entries']==5 and a['iteration_counts']['pricing_scanned_entries']==63
 checks[prefix+'native_policy']=a['options']['algorithm']==':primal' and a['options']['basis_update']==':'+a['manager'] and a['options']['pricing']==':steepest_edge' and a['options']['basis_refactorization']==':native' and a['policy']['max_refinements']=='3' and all(a['policy'][k]=='false' for k in ('hypersparse','pivot_validation','solve_refinement','recovery','incremental_primal','incremental_primal_pivots'))
 checks[prefix+'rejection_boundaries']=len(proposals)==2 and [x['entering'] for x in proposals]==[13,7] and all(x['selected_row']==-2 for x in proposals)
checks['manager_options_policy_equal']=all(a['policy']==records[0]['policy'] and {k:v for k,v in a['options'].items() if k!='basis_update'}=={k:v for k,v in records[0]['options'].items() if k!='basis_update'} for a in records)
map_=json.loads((o/'existing-failure-map.json').read_text());checks['historical_failure_map']=len(map_['records'])==2 and all(len(a['entries'])==12 and sorted(x['line'] for x in a['entries'])==sorted([214,215,216]*4) for a in map_['records'])
result={'all_passed':all(checks.values()),'checks':checks,'pin_count':len(pins['inventory']),'exact':exact,'scope':'Current observed Float64 four-manager path with original oracle. Initial/published dual residuals are owned snapshots, not private fresh BTRAN capture. No x64 cause, observer neutrality, full-suite, timing or speedup claim.'}
o.mkdir(exist_ok=True)
with (o/(name+'-audit.json')).open('x') as f:json.dump(result,f,indent=2);f.write('\n')
for n in ('report.toml','process.json','pins.json','run.log'):
 dst=o/(name+'-'+n);assert not dst.exists();shutil.copyfile(b/n,dst)
for src_,suffix in ((d/'reproduce/primal_price_recovery_census.jl','driver.jl'),(root/'test/legacy_primal_direction_price_tests.jl','test.jl')):
 dst=o/(name+'-'+suffix);assert not dst.exists();shutil.copyfile(src_,dst)
print(json.dumps({'all_passed':result['all_passed'],'gates':len(checks),'pins':result['pin_count'],'failed':[k for k,v in checks.items() if not v]},indent=2));assert result['all_passed']
