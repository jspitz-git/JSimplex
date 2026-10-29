from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent;W=D.parents[2];checks={};bindings={}
def read(p):
 p=Path(p);b=p.read_bytes();bindings[str(p)]=hashlib.sha256(b).hexdigest();return b.decode()
before=read(D/'REPORT.before-review.md');after=read(D/'REPORT.md');source=read(W/'src/simplex.jl');recovery=read(W/'src/simplex_recovery.jl')
checks['original_understated_ledger_preserved']='validation/count/fill O(m+nnzB)' in before
checks['full_state_work_verified']='fill!(is_basic, false)' in source and 'for index in eachindex(basis.states)' in source
checks['corrected_domain_and_total_bounds']='validation/count/fill O(N+m+nnzB)' in after and 'O(mN+m^2+m*nnzB)' in after
checks['configurable_refinement_bound']='m*policy.max_refinements' in after
checks['hidden_nonfinite_provenance']='Even a returned finite/unreliable SolveQuality is insufficient provenance' in after and 'all(isfinite,correction) || return quality' in recovery and 'trial_quality.finite || return quality' in recovery
checks['original_sources_no_edit']=all((W/'src'/p.relative_to(W/'src')).read_bytes()==(Path('/home/jspitz/JSimplex.jl/src')/p.relative_to(W/'src')).read_bytes() for p in (W/'src').rglob('*.jl'))
if not all(checks.values()):raise RuntimeError(checks)
(D/'review-fix.json').write_text(json.dumps(dict(accepted=True,checks=checks,bindings=bindings),indent=2)+'\n');print(json.dumps({'checks':len(checks),'bindings':len(bindings),'accepted':True}))
