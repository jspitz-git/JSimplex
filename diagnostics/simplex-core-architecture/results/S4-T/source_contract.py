from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture';E=D/'results/S4-T';S=D/'results/S4-S';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
prior=json.loads((S/'source-contract.json').read_text());fix=json.loads((S/'review-fix.json').read_text());host=json.loads((E/'host-before.json').read_text());lp=json.loads((E/'exact-lp.json').read_text());checks={}
# Match old hashes against current bytes or exact preserved pre-review text, never rewrite prior inventory.
preserved=[S/'report-before-keyword.md',S/'next-plan-before-keyword.md'];preserved_hashes={sha(p) for p in preserved}
changed={p:h for p,h in prior['sha256'].items() if sha(p)!=h}
checks['S586_bound_584_current_plus_two_preserved']=len(prior['sha256'])==586 and len(changed)==2 and set(changed.values())==preserved_hashes
q=json.loads((D/'results/S4-Q/cost-1-pins.json').read_text())['inventory'];checks['all558Q_unchanged']=len(q)==558 and all(sha(p)==v['sha256'] for p,v in q.items())
checks['user6_unchanged']=len(host['user_hashes'])==6 and all(sha(p)==h for p,h in host['user_hashes'].items())
checks['full_previous_groups_absent']=not host['matches'] and not host['pids_present']
checks['src_test_CI_equal_master']=not subprocess.check_output(['git','diff','master','--','src','test','.github'])
checks['eleven_exact_lp_checks']=len(lp['checks'])==11 and all(lp['checks'].values())
checks['launch_unsupported']=lp['launch_supported'] is False
src=lambda p:(R/'src'/p).read_text()
checks['public_observer_nothing']='_solve_diagnosed(problem,nothing;' in src('solver.jl') or '_solve_diagnosed(problem, nothing;' in src('solver.jl')
checks['phase_returns_initial_if_no_artificials']='isempty(artificial_rows) && return initial, 0, initial' in src('primal_simplex.jl')
checks['scheduler_uses_chain_interval']='length(ws.factorization.updates) >= interval' in src('refactorization_policy.jl')
checks['prepared_forward_route']='prepare_update=true' in src('primal_simplex.jl')
checks['original_certificate_recovery_preserved']='return _try_native_certificate_recovery(workspace, primal, dual,' in src('dual_simplex.jl')
checks['production_reuse_false']='reuse_symbolic=false' in src('huangfu_hall_factorization.jl')
checks['root_loads_precompile']='include("precompile.jl")' in src('JSimplex.jl')
pc=Path('/home/jspitz/.julia/packages/PrecompileTools/QUxvR/src/workloads.jl');checks['both_verbose_guards']=pc.read_text().count('if $iscompiling || $PrecompileTools.verbose[]')==2
work=src('precompile.jl');checks['workload_loops_bound']=all(s in work for s in ['map((Float64, Float32))','(:pfi, :bartels_golub, :forrest_tomlin, :suhl_suhl, :huangfu_hall)','algorithm in (:primal, :dual), presolve in (false, true)','for (problem, objective) in ((upper, -10), (lower, 5))','result = solve(upper)','for T in (Float64, Float32)'])
checks['conditional_public_entries82']=2*(5*2*2*2+1)==82
paths=set(prior['sha256']);paths.update(str(p.resolve()) for p in [*S.iterdir(),*E.iterdir(),D/'S4-ISOLATED-PUBLIC-LP-WORK-CONTRACT.md',R/'docs/superpowers/plans/2026-10-12-hh-isolated-bootstrap-contract.md'] if p.is_file())
obj=dict(checks=checks,all_passed=all(checks.values()),sha256={p:sha(p) for p in sorted(paths)},scope='Current read-time hashes, source predicates and conditional rational LP ONLY; no runtime qualification',launch_supported=False,julia_calls=0)
with (E/'source-contract.json').open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
print(json.dumps(dict(checks=checks,hashes=len(paths),all_passed=obj['all_passed'])));assert obj['all_passed']
