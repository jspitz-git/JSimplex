from pathlib import Path
import json,hashlib
R=Path.cwd();E=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-WORKSPACE-PLAN'
S=R/'docs/superpowers/specs/2026-10-18-direct-bg-export-workspace.md';P=R/'docs/superpowers/plans/2026-10-18-direct-bg-export-workspace.md'
bindings={};checks={}
def read(p):
 p=Path(p);p=p if p.is_absolute() else R/p
 b=p.read_bytes();bindings[str(p)]=hashlib.sha256(b).hexdigest();return b.decode()
def need(k,v):checks[k]=bool(v)
sp=read(S);pl=read(P);read(E/'host.json');read(R/'AGENTS.md');read(Path(__file__).resolve())
base=R/'diagnostics/direct-lu-policy-adapters/reproduce'
direct=read(base/'direct-factor.jl');export=read(base/'factor-export.jl');hh=read(R/'src/huangfu_hall_factorization.jl');mark=read(R/'src/markowitz_factorization.jl')
for n in ['fixtures.jl','lifecycle-tests.jl','policy-tests.jl']:read(base/n)
for n in ['triangular_factorization.jl','triangular_indices.jl','triangular_rows.jl','bartels_golub_rows.jl']:read(R/'src'/n)
seal=json.loads(read(R/'diagnostics/simplex-core-architecture/results/DIRECT-LU-POLICY-ADAPTER-COST-PREPARATION/runs/cost1-300/sealed.json'))
stage=R/'.superpowers/sdd/2026-10-16-direct-lu-policy-adapters/driver-stages/green/src'
for n in ['direct-factor.jl','factor-export.jl','huangfu_hall_factorization.jl','markowitz_factorization.jl','triangular_factorization.jl','triangular_indices.jl','triangular_rows.jl','bartels_golub_rows.jl']:
 p=stage/n;read(p);v=seal['inventory'][str(p)];need('sealed_'+n,bindings[str(p)]==v['sha256'] and str(p.resolve())==v['resolved'])
need('explicit_triangular_difference',bindings[str(stage/'triangular_factorization.jl')]!=bindings[str(R/'src/triangular_factorization.jl')] and 'differs from that historical stage' in sp)
for n in ['direct-factor.jl','factor-export.jl']:need('reference_'+n,bindings[str(base/n)]==bindings[str(stage/n)])
for n in ['huangfu_hall_factorization.jl','markowitz_factorization.jl']:need('current_source_'+n,bindings[str(R/'src'/n)]==bindings[str(stage/n)])
report=read(R/'diagnostics/simplex-core-architecture/results/DIRECT-LU-POLICY-ADAPTER-COST1/REPORT.md')
read(R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-SPLIT-COST1/REPORT.md')
read(R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-IMPORT-RESERVE-PLAN/review.md')
need('original_result_all24','All24cells miss both' in report)
need('normalization_temporary','values=similar(U.nzval)' in direct and 'copyto!(U.nzval,values)' in direct)
need('copy_to_packed','copy(@view U.nzval[nzrange(U,j)])' in direct)
need('complete_refactor','candidate=_direct_lu_factor_with_exporter' in direct)
need('extract_fresh_workspace',export.count('HHExtractWorkspace()')==2)
need('permutation_scratch','seen=falses(n)' in export)
need('markowitz_ignores_extract_workspace','function _hh_extract_parts(F::MarkowitzBackend{T},::HHExtractWorkspace)' in hh)
need('orientation_inner_two_vectors','permuted=Vector{Float64}(undef,n);transformed=similar(permuted)' in hh)
need('orientation_outer_two_vectors','work=Vector{Float64}(undef,length(p)); auxiliary=similar(work)' in export)
need('unit_scaling_early_return','all(==(1.0),scaling) && return false' in hh)
need('markowitz_existing_private_spare','_construct_markowitz(B,backend.workspace,D,backend.spare)' in mark)
for key,terms in {
 'ownership':['active inner identity','no workspace','Reentrant','finally','no rollback promise'],
 'numeric':['same CSC column/slot order','nonzero-to-zero','signed-zero','No reordering/coalescing/zero-dropping'],
 'work':['2*u stores','8*sum(u_t)','zero new full scans','one backend solve'],
 'memory':['A_old+A_new+E_t+W_t','NOT a proof','actual reachable graph','no second active factor'],
 'scope':['Backend reuse and dynamic U are outside scope','No implementation or numerical allowance'],
}.items():
 text=sp+'\n'+pl
 need(key,all(x.lower() in text.lower() for x in terms))
need('no_candidate',not (R/'diagnostics/direct-bg-export-workspace').exists())
need('tasks',all(x in pl for x in ['## Task1','## Task2','## Task3','scratch_budget_boundaries','normalization_rejection_first_middle_last','private_publish_failure_matrix','copy_refactor_diverge','dimension_fallback_transition']))
need('future_gates',all(x in sp for x in ['all8','0.95reference','1.10reference','ordinary BG','300/inner292','600/592']))
need('no_placeholders',all(x not in sp+pl for x in ['TBD','TODO','FIXME']))
examples=[]
for n,l,u in [(0,0,0),(1,1,1),(32,63,63),(32,528,528),(96,191,191),(96,4656,4656),(10000,500000,500000)]:
 p=16*(l+u)+8*(n+1);b=min(1048576,p//16);seen=8*((n+63)//64);cs=512+seen
 keep_seen=n>0 and cs<=b;keep_orient=keep_seen and cs+32*n<=b;charge=cs+(32*n if keep_orient else 0) if keep_seen else 0
 need('budget_'+str(n)+'_'+str(l),0<=charge<=b<=1048576)
 examples.append(dict(n=n,l=l,u=u,P0=p,budget=b,seen=keep_seen,orientation=keep_orient,charge=charge,normalization_payload_saved_per_event=8*u,scope='Synthetic size arithmetic only, not measured factors or allocations'))
need('successful_store_formula',all(3*u-u==2*u for u in [0,1,63,528,4656]))
a=dict(scope='Planning-only new offline checks; no Julia, no old checker rerun',all_passed=all(checks.values()),checks=checks,readtime_sha256=bindings,synthetic_budget_examples=examples)
with (E/'author-check.json').open('x') as f:json.dump(a,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=a['all_passed'],checks=len(checks),bindings=len(bindings),failed=[k for k,v in checks.items() if not v])))
if not a['all_passed']:raise SystemExit(1)
