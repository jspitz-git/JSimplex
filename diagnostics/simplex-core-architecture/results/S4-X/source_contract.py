import json,hashlib
from pathlib import Path
root=Path.cwd();r=root/'diagnostics/simplex-core-architecture/results/S4-X'
files=['dual_simplex.jl','simplex_pivot.jl','simplex_recovery.jl','legacy_dual_correction.jl','legacy_dual_prices.jl','simplex_driver.jl','simplex_precision_recovery.jl','simplex_pricing.jl','dual_ratio.jl']
s={n:(root/'src'/n).read_text() for n in files}
checks={
 'dual_phase_installed':'workspace.options = _phase_options(original_options,:dual)' in s['dual_simplex.jl'],
 'auxiliary_uses_factor_copy':'factorization = copy_basis_factorization(workspace.factorization)' in s['dual_simplex.jl'],
 'auxiliary_inherits_counts':'workspace.iterations = auxiliary.iterations' in s['dual_simplex.jl'],
 'handoff_second_factor_copy':'trial.factorization = copy_basis_factorization(workspace.factorization)' in s['dual_simplex.jl'],
 'handoff_retains_failed_refactor_count':'max(workspace.refactorizations, trial.refactorizations)' in s['dual_simplex.jl'],
 'retry_fixed_formula':'big(policy.max_pivot_candidates)^2*(big(policy.max_recovery_rounds)+1)' in s['simplex_pivot.jl'],
 'retry_preforward_increment':s['simplex_pivot.jl'].index('attempts += 1')<s['simplex_pivot.jl'].index('result = let refresh_now='),
 'recursive_recovery_guard':'if policy.recovery && recovery_rounds < policy.max_recovery_rounds' in s['simplex_pivot.jl'],
 'staged_mismatch_throws':'_is_staged_workspace(workspace) &&\n                    throw(_PivotRejection' in s['dual_simplex.jl'],
 'discard_rebuild_after_deadline':'even if the caller\'s deadline has just expired' in s['simplex_pivot.jl'],
 'legacy_refine_32_corrections':'for correction in 0:32' in s['simplex_recovery.jl'] and 'correction == 32 && return nothing' in s['simplex_recovery.jl'],
 'legacy_initial_solve_before_loop':s['simplex_recovery.jl'].index('solution = BigFloat.(_refinement_basis_solve')<s['simplex_recovery.jl'].index('for correction in 0:32'),
 'prices_two_precision_calls':'_refined_dual_prices(workspace, factor, B, 256' in s['dual_simplex.jl'] and '_refined_dual_prices(workspace, factor, B, 512' in s['dual_simplex.jl'],
 'native_tableau_staged_guard':'policy.max_refinements>0 && _is_staged_workspace(ws)' in s['legacy_dual_correction.jl'],
 'restore_then_primal_phase':'workspace.options = _phase_options(phase_options,:primal)' in s['dual_simplex.jl'],
 'policy_failure_recovery_bypass':'!(policy.precision_boosting || policy.lp_refinement)' in s['simplex_precision_recovery.jl'],
 'altered_model_requires_driver':'!_original_costs_active(ws) || !_original_bounds_active(ws)' in s['simplex_driver.jl'],
 'dantzig_auto_recursion_excluded':'ws.options.pricing == :auto && _weight_pricing(ws,:dual) == :steepest_edge || return true' in s['simplex_pricing.jl']}
assert all(checks.values())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
w=json.loads((root/'diagnostics/simplex-core-architecture/results/S4-W/source-contract.json').read_text())['sha256']
paths=[Path(p) for p in w if '/src/' in p or '/test/' in p or '/.julia/' in p or Path(p).name in ['Manifest.toml','LocalPreferences.toml','settings.json','Project.toml']]
paths+= [root/'diagnostics/simplex-core-architecture'/p for p in ['S4-PUBLIC-CONTROLLER-ATTEMPT-CONTRACT.md','S4-PUBLIC-CONTROLLER-ATTEMPT-CONTRACT-REVIEW.md','results/S4-W/attempt-ledger.json','results/S4-W/review-fix.json','results/S4-S/manifest.json','results/S4-T/exact-lp.json']]
paths+=[root/'docs/superpowers/plans/2026-10-12-hh-postsolve-dual-work-contract.md']
pins={str(p):sha(p) for p in sorted(set(paths))}
ranges={'dual_simplex.jl':[(97,181),(940,1124),(1126,1210),(1342,1406),(1820,1963),(2052,2156),(2203,2300)],'simplex_pivot.jl':[(42,118),(178,270),(306,432)],'simplex_recovery.jl':[(514,565)],'legacy_dual_correction.jl':[(107,188)],'simplex_driver.jl':[(267,320)]}
ex=[]
for name,spans in ranges.items():
 lines=(root/'src'/name).read_text().splitlines(keepends=True)
 for lo,hi in spans:ex.append({'file':'src/'+name,'first_line':lo,'last_line':min(hi,len(lines)),'file_sha256':sha(root/'src'/name),'text':''.join(lines[lo-1:hi])})
for name,value in [('source-contract.json',{'checks':checks,'all_passed':all(checks.values()),'sha256':pins,'complete_public_budget_qualified':False,'scope':'Literal source checks and local entry bounds only; no execution or whole call graph proof'}),('source-excerpts.json',ex)]:
 with (r/name).open('x') as f:json.dump(value,f,indent=2);f.write('\n')
(r/'search-note.md').write_text('Read-only source searches guessed absent transactional_pivot.jl, simplex_pricing_support.jl and simplex_ratio.jl; rg exited 2, stopping the remaining sequential reads under set -e. A subsequent exploratory rg also tried absent basis_refinement.jl with stderr suppressed and || true; it was a search only, not a validation gate. Actual files were then located with rg --files/rg over src. No Julia, evidence mutation or publication followed a failed validation.\n')
print(json.dumps({'checks':len(checks),'pins':len(pins),'excerpts':len(ex),'all_passed':True}))
