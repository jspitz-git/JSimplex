"""Source/readtime inputs for planning, not launch pins. Never rerun."""
from pathlib import Path
import json,hashlib,subprocess
P=Path(__file__).resolve().parent;R=P.parents[3];W=Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,j):
 with p.open('x') as f:json.dump(j,f,indent=2);f.write('\n')
def need(v,m):
 if not v:raise RuntimeError(m)
def g(*a,cwd=R):return subprocess.check_output(['git',*a],cwd=cwd,text=True).strip()
need(g('rev-parse','HEAD')=='cb757325ff6fe34e94479f7e622d6620fa7c1c8a','Diagnostic HEAD')
need(g('rev-parse','master')==g('rev-parse','HEAD',cwd=W)=='26e2291745999f485a74f643298ca997d65c7205','Master')
sources=[W/'src'/n for n in ['JSimplex.jl','factorization.jl','triangular_factorization.jl','huangfu_hall_factorization.jl','markowitz_factorization.jl','triangular_rows.jl','triangular_indices.jl','triangular_spikes.jl','hypersparse_factorization.jl','options.jl']]
files=sources+[R/'diagnostics/direct-lu-markowitz/reproduce'/n for n in ['factor-export.jl','direct-factor.jl','fixtures.jl']]+[R/'diagnostics/simplex-core-architecture'/n for n in ['DIRECT-LU-GREEN-CORRECTNESS.md','DIRECT-LU-COST1.md','DIRECT-LU-PREPARATION.md']]
files += [R/'diagnostics/simplex-core-architecture/results/DIRECT-LU-TEST-REPAIR/correctness.jl']+[R/'diagnostics/simplex-core-architecture/results/DIRECT-LU-COST-PREPARATION'/n for n in ['inputs.json','inputs.toml']]
files += [R/'docs/superpowers'/n for n in ['specs/2026-10-14-direct-lu-markowitz.md','plans/2026-10-14-direct-lu-markowitz.md','plans/2026-10-15-native-pivot-policy.md','plans/2026-10-16-native-pivot-production-integration.md','specs/2026-10-16-direct-lu-policy-adapters.md','plans/2026-10-16-direct-lu-policy-adapters.md']]
V=P.parent/'NATIVE-PIVOT-MASTER-VALIDATION';files += [V/n for n in ['result-review.md','result-review.json','closure.json','publication.json']]
old=(R/'diagnostics/direct-lu-markowitz/reproduce/direct-factor.jl').read_text();native=(W/'src/factorization.jl').read_text();export=(R/'diagnostics/direct-lu-markowitz/reproduce/factor-export.jl').read_text()
checks=dict(old_wrapper_no_policy='pivot_policy' not in old,old_factory_default='ordinary=_factorize_basis(B,backend)' in old,old_generic_default='Factor(B,backend)' in old,three_initializers=all('function _init_direct_manager(::Type{'+n+'}' in old for n in ['ForrestTomlinFactorization','SuhlSuhlFactorization','BartelsGolubFactorization']),export_markowitz='_export_basis_lu(backend::MarkowitzBackend{Float64})' in export,export_native='_export_basis_lu(backend::UMFPACKBackend)' in export,current_policy_enum='@enum _NativePivotPolicy::UInt8' in native,current_policy_backend='const pivot_policy::_NativePivotPolicy' in native,current_policy_factor='_factorize_basis(B::AbstractMatrix{Float64}, ::Val{:native}, policy::_NativePivotPolicy)' in native)
need(all(checks.values()),'Literal source assumptions')
baseline={}
for label,root in [('diagnostic',R),('production',W)]:
 names=g('ls-files','src','test','.github','Project.toml',cwd=root).splitlines();baseline[label]={n:sha(root/n) for n in names}
save(P/'baseline.json',baseline)
files += sorted(q for q in P.iterdir() if q.is_file())
save(P/'source-inputs.json',dict(scope='Readtime planning source/evidence pins, not launch manifest',checks=checks,sha256={str(q):sha(q) for q in sorted(set(files))}))
print('Source assumptions',len(checks),'PASS;',len(set(files)),'readtime bindings')
