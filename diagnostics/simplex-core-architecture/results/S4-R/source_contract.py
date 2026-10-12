from pathlib import Path
import hashlib,json,subprocess
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture';E=D/'results/S4-R'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:(R/p).read_text()
s=read('src/solver.jl');w=read('src/simplex.jl');f=read('src/factorization.jl');h=read('src/huangfu_hall_factorization.jl');o=read('src/options.jl');p=read('src/simplex_pivot.jl');r=read('src/simplex_recovery.jl');root=read('src/JSimplex.jl');pre=read('src/precompile.jl')
q=json.loads((D/'results/S4-Q/cost-1-pins.json').read_text());host=json.loads((E/'host-before.json').read_text())
checks={}
checks['public_entry_original_diagnostics_nothing']='return _solve_diagnosed(problem, nothing; relax_integrality, options)' in s
entry=s[s.index('function solve(problem::'):s.index('function _solve_diagnosed')]
checks['public_entry_no_factory_keyword']='factor' not in entry.split('end',1)[0]
checks['options_closed_manager_and_backend']='basis_update must be :pfi, :forrest_tomlin, :bartels_golub, :suhl_suhl, or :huangfu_hall' in o and 'basis_refactorization must be :native or :markowitz' in o
checks['factory_dispatch_by_options']='_basis_factorization(B, Val(M), Val(R))' in f
checks['hh_factory_real_constructor']='return HuangfuHallFactorization(B,Val(R))' in h
checks['concrete_workspace_factor']='mutable struct SimplexWorkspace{T<:Real,F,M,R,D}' in w and 'factorization::F' in w
init=w[w.index('function _initialize_workspace_state'):w.index('function _finish_workspace_initialization!')]
checks['factor_precedes_workspace']=init.index('_basis_factorization(initial_basis, typed_options)')<init.index('workspace = SimplexWorkspace(')
checks['initial_recompute_no_refactor']='recompute!(workspace)\n    _simplex_event!(workspace, :refactor_initial)' in w
checks['recompute_original_dispatch']='refactorize!(workspace.factorization, B)' in w
checks['other_real_refactor_dispatch']='refactorize!(workspace.factorization, basis_matrix(workspace))' in s and 'refactorize!(ws.factorization,basis_matrix(ws))' in p
checks['native_reuse_disabled']='lu!(F,convert(SparseMatrixCSC{Float64,Int},B);reuse_symbolic=false)' in h
checks['staged_factor_shared']='ws.factorization,scratch,' in p
checks['recovery_factory_and_finally']='_basis_factorization(B,ws.options)' in r and 'finally\n        ws.refactorizations += 1' in r
checks['original_model_copy_self_reference']='continuous_problem = JSimplex.relax_integrality(problem)' in s
checks['original_feasibility_and_objective']='_original_primal_feasible(continuous_problem, primal' in s and '_restored_objective(problem, primal)' in s
checks['projection_not_iteration_budget']='Those reconstruction exchanges do not consume the simplex iteration budget.' in s
checks['root_includes_moi_precompile']='include("moi.jl")' in root and 'include("precompile.jl")' in root
checks['precompile_contains_public_and_native_work']='@setup_workload begin' in pre and 'result = solve(problem; options)' in pre and '_factorize_basis(matrix, Val(:markowitz))' in pre
clone=(D/'reproduce/hh_history_cost_clone.jl').read_text()
inv=clone.replace('_s4q_refactor_lu!','_hh_refactor_lu!').replace('_s4q_refactor_backend','_hh_refactor_backend').replace('_s4q_refactorize!','refactorize!').replace('reuse_symbolic=_same_umfpack_pattern(F,convert(SparseMatrixCSC{Float64,Int},B))','reuse_symbolic=false')
checks['Q_inverse_still_exact']=inv==h[h.index('_hh_refactor_lu!(F::Float64UMFPACK'):h.index('function copy_basis_factorization(f::HuangfuHallFactorization')]
checks['all_Q558_pins_unchanged']=len(q['inventory'])==558 and all(sha(x)==v['sha256'] for x,v in q['inventory'].items())
comparisons={}
for stage,name in [('G','publication'),('I','assembly')]:
 pins=json.loads((D/f'results/S4-{stage}/{name}-1-pins.json').read_text())['inventory']
 for rel in ['src/huangfu_hall_factorization.jl','src/factorization.jl','src/simplex.jl','src/solver.jl']:
  x=str(R/rel);comparisons[f'{stage}:{rel}']=sha(x)==pins[x]['sha256']
checks['GI_selected8_source_matches']=all(comparisons.values())
checks['user6_unchanged']=len(host['user_hashes'])==6 and all(sha(x)==v for x,v in host['user_hashes'].items())
checks['source_test_CI_equal_master']=not subprocess.check_output(['git','diff','master','--','src','test','.github'])
checks['host_full_previous_groups_absent']=host['matches']==[] and host['pids_present']==[]
paths=set(q['inventory'])
paths.update(str(x.resolve()) for x in [E/'source_contract.py',E/'host-before.json',D/'S4-PUBLIC-CONTROLLER-REUSE-CONTRACT.md',R/'docs/superpowers/plans/2026-10-12-hh-public-controller-reuse-contract.md',R/'docs/superpowers/plans/2026-10-12-hh-isolated-module-loading-contract.md',D/'S4-BORROWED-ASSEMBLY-CONTRACT.md',D/'S4-HISTORY-LIFECYCLE-COST-MEASUREMENT.md',D/'S4-HISTORY-LIFECYCLE-COST-MEASUREMENT-REVIEW.md',D/'results/S4-Q/ledger.md',D/'results/S4-Q/cost-1-report.toml',D/'results/S4-G/publication-1-pins.json',D/'results/S4-I/assembly-1-pins.json'])
paths.update(str((R/x).resolve()) for x in ['src/JSimplex.jl','src/precompile.jl','src/moi.jl'])
result=dict(checks=checks,all_passed=all(checks.values()),comparisons=comparisons,sha256={x:sha(x) for x in sorted(paths)},scope='Read-time literal-source predicates and preserved evidence; not Julia parsing/call-graph completeness/runtime execution',numerical_calls=0,native_calls=0,decision='Public qualification unsupported by current seam evidence; source-only loading audit next')
with (E/'source-contract.json').open('x') as out:json.dump(result,out,indent=2);out.write('\n')
print(json.dumps({'checks':checks,'hashes':len(paths),'all_passed':result['all_passed']}));assert result['all_passed']
