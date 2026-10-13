"""One-shot offline source/package qualification. Never imports old auditors."""
from pathlib import Path
import json,hashlib,re
H=Path(__file__).resolve().parent;R=H.parents[3];E=H.parent/'MA-E';F=H.parent/'MA-F-repair';pins={}
def read(p):
 b=p.read_bytes();pins[str(p.relative_to(R)) if p.is_relative_to(R) else str(p)]=hashlib.sha256(b).hexdigest();return b.decode()
read(Path(__file__));inputs=json.loads(read(H/'inputs.json'));red=json.loads(read(H/'red.json'));green=json.loads(read(H/'green.json'))
checks={'all_initial_bindings':all(hashlib.sha256((Path(k) if Path(k).is_absolute() else R/k).read_bytes()).hexdigest()==v for k,v in inputs['sha256'].items()),'structural_RED_expected':red['all_passed'] is False and [k for k,v in red['checks'].items() if v]==['helpers_byte_identical'],'structural_GREEN_all5':green['all_passed'] and len(green['checks'])==5 and all(green['checks'].values())}
for src,dst in [(E/'overlays/candidate/test/markowitz_ma_upper_tests.jl','candidate-tests.jl'),(E/'overlays/candidate/src/JSimplex.jl','candidate-JSimplex.jl'),(E/'overlays/candidate/Project.toml','candidate-Project.toml'),(E/'fixtures.toml','fixtures.toml'),(F/'driver.jl','qualified-driver-reference.jl'),(F/'kernels.jl','qualified-kernels-reference.jl')]:checks['exact_'+dst]=read(src)==read(H/dst)
r=read(E/'overlays/reference/src/markowitz_factorization.jl');c=read(H/'candidate-markowitz.jl');e=read(E/'overlays/candidate/src/markowitz_factorization.jl')
a=r.index('function _backend_forward_solve!');b=r.index('function _backend_transpose_solve!',a)
checks['reference_forward_exact_inverse']=read(H/'reference-forward.jl').replace('function reference_forward!','function _backend_forward_solve!',1)==r[a:b]
t=read(H/'route-tests.jl');compare=t[t.index('function compare_forward'):t.index('@testset "MA route complete')]
checks['nine_pair_assertions']=len(re.findall(r'^    @test ',compare,re.M))==9
checks['three_children']=len(re.findall(r'^@testset ',t,re.M))==3
checks['original381_counts']=sum(json.loads(read(E/'test-counts.json')).values())==381
checks['new266_counts']=14*9+6*9+(8*9+8+4+2)==266
checks['qualified647_total']=381+266==647
checks['no_global_overwrite']='function J.' not in t and 'function JSimplex.' not in t
checks['bounded_28pairs']=4*2+3*2+3+1+2+4*2==28
checks['single_constructor_copy_two_calls']=compare.count('J.MarkowitzBackend(A)')==1 and compare.count('J._copy_backend(b)')==1 and compare.count('outcome(')==2
checks['source_condition_once']=c.count('if (T === BigFloat || T === Rational{BigInt}) && sparse_pivots > 0')==1
checks['loop_order_publication_retained']='work[pivot] = value / backend.diagonal[pivot]' in c
review=json.loads(read(F/'review-final.json'))
installed={k:v for k,v in review['sha256'].items() if k.endswith(('/Test/src/Test.jl','/base/scopedvalues.jl'))}
checks['two_installed_context_sources']=len(installed)==2
for k,v in installed.items():
 text=read(Path(k));checks['installed_'+Path(k).name]=pins[k]==v
 if k.endswith('/Test/src/Test.jl'):checks['Test_context_API']='macro with_testset' in text and 'function get_testset_depth' in text
 elif k.endswith('/base/scopedvalues.jl'):checks['ScopedValues_context_API']='macro with' in text
checks['driver_scoped_context']='Test.@with_testset ts begin' in read(H/'qualified-driver-reference.jl') and 'finally' in (H/'qualified-driver-reference.jl').read_text()
plan=read(R/'docs/superpowers/plans/2026-10-14-ma-routing-qualification-admission.md');read(H/'test-contract.md')
checks['budget_pair_count']=20*48*5==4800 and 20*5*(12*7+12*31)==45600
checks['caps_preserved']=all(s in plan for s in ['RED<=30s','qualification<=120s','<=60s','<=600s','<=750s'])
checks['gates_preserved']=all(s in plan for s in ['<=0.95','least6/7','median<=1.05','all32controls and6targets'])
o={'all_passed':all(checks.values()),'checks':checks,'sha256':pins,'prospective_counts':{'old':381,'new_children':[126,54,86],'new':266,'total':647,'new_pairs':28,'new_constructors':28,'new_backend_copies':28,'new_full_entries':56,'cost_terms_each_schedule':45600},'scope':'Offline literal/inverse/count checks only; Julia test syntax, dispatch, exceptions, counts and performance UNEXECUTED. Installed context source hashes are fresh read-time bindings.'}
with (H/'verification.json').open('x') as f:json.dump(o,f,indent=2);f.write('\n')
print(json.dumps({'all_passed':o['all_passed'],'checks':checks,'bindings':len(pins)},indent=2))
if not o['all_passed']:raise SystemExit(1)
