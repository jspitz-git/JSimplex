from pathlib import Path
from fractions import Fraction as F
import sys,json,tomllib,hashlib,importlib.util,re,shutil
sys.dont_write_bytecode=True
root=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');d=root/'diagnostics/simplex-core-architecture';name=sys.argv[1];b=root/'.superpowers/simplex-core-architecture/S6-V'/name;o=d/'results/S6-V'
r=tomllib.loads((b/'report.toml').read_text());p=json.loads((b/'process.json').read_text());pins=json.loads((b/'pins.json').read_text());log=(b/'run.log').read_text();rs=r['records']
s=importlib.util.spec_from_file_location('guard',d/'reproduce/guarded_run.py');g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
checks={'exit':p['returncode']==0 and p['reason']=='exit0' and p['pins_unchanged'],'guard_pins':g.pins_match(pins),'independent_pins':all(hashlib.sha256(Path(k).read_bytes()).hexdigest()==v['sha256'] and str(Path(k).resolve())==v['resolved'] for k,v in pins['inventory'].items()),'source':r['source']==str(root/'src/JSimplex.jl'),'threads_globals':r['julia_threads']==r['blas_threads']==1 and r['globals_preserved']}
paths=set(pins['files'])
for tree in pins['trees']:paths.update(str(x) for x in Path(tree).rglob('*') if x.is_file())
checks['inventory_membership']=paths==set(pins['inventory'])
src=(root/'test/legacy_primal_direction_price_tests.jl').read_text();marker='@testset "A repeated price disagreement cannot renew the recovery budget" begin'
original=marker+src.split(marker,1)[1].split('\n@testset',1)[0]
checks['test_original']=r['test_sha256']==hashlib.sha256(src.encode()).hexdigest() and original==r['original_source']
checks['five_original_assertions']=r['original_assertions']=='\n'.join(x for x in original.split('\n') if x.strip().startswith('@test ')) and r['original_assertions'].count('@test ')==5
checks['assertions124']=re.search(r'\|\s+124\s+124\s+',log) is not None and 'Test Failed' not in log and 'Error During Test' not in log
checks['twelve_cases']=[(a['manager'],a['mode']) for a in rs]==[(m,x) for m in ('pfi','forrest_tomlin','suhl_suhl','bartels_golub') for x in ('exact','seed','subject')]
u=tomllib.loads((d/'results/S6-U/census-1-report.toml').read_text())
checks['unchanged_options_policy']=all(a['options']==next(x for x in u['records'] if x['manager']==a['manager'])['options'] and a['policy']==u['records'][0]['policy'] for a in rs)
C=list(map(F,[1,1,0,0,0,0]));bad=C.copy();bad[2]=F(1,2**40)
identity=[[F(i==j) for j in range(6)] for i in range(6)]
def matvec(A,x):return [sum(v*F(t) for v,t in zip(row,x)) for row in A]
def work(calls,hits):
 bs=[x for x in calls if x['kind']=='btran'];return {'cost':sum(x['cost_rhs'] for x in bs),'correction':sum(not x['cost_rhs'] for x in bs),'btran':len(bs),'ftran':sum(x['kind'] in ('ftran','ordinary_ftran') for x in calls),'hits':hits}
exact=[]
flags={k:True for k in ('matrix_point','prices','forwarded_identity','work','status_events','unchanged_selected','subject_oracle','negative_sensitive','negative_selected','publication')}
for a in rs:
 A=[[F(x) for x in row] for row in a['A_rows']];before=a['before'];after=a['after'];mode=a['mode'];calls=a['calls'];c=a['work']
 expectedA=[identity[i]+[F(i==j) for j in range(2,6)]+[-F(i==j) for j in range(2,6)]+[F(0)] for i in range(6)]
 flags['matrix_point'] &= A==expectedA and before['basis']==list(range(1,7)) and list(map(F,before['costs']))==C+[F(0)]*15 and matvec(A,before['primal'][:15])==[F(1)]*6
 rho=C if mode=='exact' else bad
 expectedPrices=[F(0)]*6+[-sum(A[i][j]*rho[i] for i in range(6)) for j in range(6,15)]+rho
 flags['prices'] &= list(map(F,before['rho']))==rho and list(map(F,before['prices']))==expectedPrices
 flags['forwarded_identity'] &= all(x['rhs']==x.get('raw',x['output']) and (list(map(F,x['output']))==bad if x.get('injected',False) else x['rhs']==x['output']) for x in calls)
 flags['work'] &= c==work(calls,sum(x.get('injected',False) for x in calls)) and c==({'cost':0,'correction':0,'btran':0,'ftran':0,'hits':0} if mode=='exact' else {'cost':1,'correction':0,'btran':1,'ftran':1,'hits':0} if mode=='seed' else {'cost':1,'correction':1,'btran':2,'ftran':2,'hits':1})
 flags['unchanged_selected'] &= all(before[k]==after[k] for k in ('primal','costs','basis','states','iterations','refactorizations','updates')) and after['iterations']==0 and not after['rejected']
 flags['status_events'] &= a['status']==('OPTIMAL' if mode=='exact' else 'NUMERICAL_ERROR') and a['counts']['correction_attempt']==a['counts']['primal_prices_corrected']==(1 if mode=='subject' else 0)
 if mode=='subject':
  flags['subject_oracle'] &= all(a['old_oracle']) and list(map(F,after['rho']))==C
  bs=[x for x in calls if x['kind']=='btran'];res=[c-v for c,v in zip(C,bad)]
  flags['subject_oracle'] &= bs[0]['cost_rhs'] and bs[0]['injected'] and not bs[1]['cost_rhs'] and not bs[1]['injected'] and list(map(F,bs[1]['rhs']))==res and list(map(F,bs[1]['output']))==res
  pub=[e['state'] for e in a['events'] if e['event']=='primal_prices_corrected'];flags['publication'] &= len(pub)==2 and all(pub[0][k]==pub[1][k] for k in pub[0] if k!='prices') and pub[0]['prices'][6]==0 and pub[1]['prices'][6]==-1 and all(x==y for j,(x,y) in enumerate(zip(pub[0]['prices'],pub[1]['prices'])) if j!=6)
  neg=a['negative'];flags['negative_sensitive'] &= neg['extra_return'] is False and all(neg['old_oracle']) and neg['new_budget_oracle'] is False and neg['work']=={'cost':2,'correction':1,'btran':3,'ftran':2,'hits':1} and neg['calls'][:-1]==calls and neg['calls'][-1]['rhs']==neg['calls'][-1]['raw']==neg['calls'][-1]['output']==list(map(float,C)) and not neg['calls'][-1]['injected']
  flags['negative_selected'] &= neg['after']==after and neg['new_events']==0
  exact.append({'manager':a['manager'],'declared_dual_residual':[str(v) for v in res],'correction_rhs':[str(F(x)) for x in bs[1]['rhs']],'corrected_residual':[str(c-(v+z)) for c,v,z in zip(C,bad,res)],'old_oracle_after_extra':neg['old_oracle'],'new_budget_oracle_after_extra':neg['new_budget_oracle']})
checks.update(flags)
result={'checks':checks,'all_passed':all(checks.values()),'pin_count':len(pins['inventory']),'exact':exact,'scope':'Twelve new diagnostic iterations; four extra negative boundary invocations after frozen subject records. New identity fixture, not original matrix/CI cause. Negative check is not a mutated production control-flow trajectory. Unused adapter lifecycle forwarding remains unexercised.'}
o.mkdir(parents=True,exist_ok=True)
with (o/(name+'-audit.json')).open('x') as f:json.dump(result,f,indent=2);f.write('\n')
for n in ('report.toml','process.json','pins.json','run.log'):
 dst=o/(name+'-'+n);assert not dst.exists();shutil.copyfile(b/n,dst)
for src_,suffix in ((d/'reproduce/primal_price_boundary_qualification.jl','driver.jl'),(root/'test/legacy_primal_direction_price_tests.jl','test.jl')):
 dst=o/(name+'-'+suffix);assert not dst.exists();shutil.copyfile(src_,dst)
print(json.dumps({'gates':len(checks),'pins':result['pin_count'],'all_passed':result['all_passed'],'failed':[k for k,v in checks.items() if not v]},indent=2));assert result['all_passed']
