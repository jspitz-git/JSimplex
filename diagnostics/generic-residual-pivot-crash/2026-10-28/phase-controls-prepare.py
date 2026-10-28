from pathlib import Path
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-residual-pivot-crash/2026-10-28');O=D.parents[1]/'generic-sum-rational-growth/2026-10-28'
s=(O/'prepare-phase.py').read_text().replace(str(O),str(D)).replace("O=D.parents[1]/'generic-bounds-norm-infeasibility/2026-10-27'","O=D.parents[1]/'generic-sum-rational-growth/2026-10-28'")
s=s.replace('generic_sum_rational_growth_tests.jl','generic_residual_pivot_crash_tests.jl').replace('SRG_','RPC_').replace('Sum rational growth','Residual pivot crash')
s=s.replace('common_ready.py','common_final.py').replace('launch-ready.py','launch-final.py').replace('contract-ready.json','contract-final.json').replace('pins-ready.json','pins-final.json').replace('admission-ready.json','admission-final.json').replace('from common_ready import','from common_final import')
s=s.replace(".replace('892','2992').replace('900','3000')",".replace('892','3592').replace('900','3600')").replace('shared_limit_seconds=3000,guard_limit_seconds=2992','shared_limit_seconds=3600,guard_limit_seconds=3592')
s=s.replace("if arm!='RED' and 'C' in c.read('test-gates.json')['accepted_variants']:","if arm!='RED':")
s=s.replace("['refactorization_policy_tests.jl','refactorization_safety_tests.jl','refactorization_timing_tests.jl','refactorization_factor_tests.jl','refactorization_failure_tests.jl']","['factorization_tests.jl','factorization_allocation_tests.jl','huangfu_hall_precision_tests.jl','triangular_stability_tests.jl','bartels_golub_rotation_tests.jl','simplex_start_tests.jl','simplex_start_exact_tests.jl','simplex_start_state_tests.jl','simplex_start_guard_tests.jl']")
compile(s,str(D/'prepare-phase.py'),'exec');(D/'prepare-phase.py').write_text(s)
s=(O/'phase-audit-complete.py').read_text().replace('SRG_','RPC_').replace('Sum rational growth','Residual pivot crash').replace('2992','3592').replace('3000','3600')
compile(s,str(D/'phase-audit.py'),'exec');(D/'phase-audit.py').write_text(s)
s=(O/'stage.py').read_text().replace(str(O),str(D)).replace('generic_sum_rational_growth_tests.jl','generic_residual_pivot_crash_tests.jl')
compile(s,str(D/'stage.py'),'exec');(D/'stage.py').write_text(s)
s=(O/'commit-integrate-publish.py').read_text().replace(str(O),str(D)).replace('codex/generic-sum-rational-growth','codex/generic-residual-pivot-crash')
a=s.index(" message='");b=s.index(" (D/'commit-message.txt')",a)
s=s[:a]+" message='Reduce accepted residual pivot and crash scalar temporaries\\n\\nApply independently accepted complete-function multiprecision scalar savings with unchanged arithmetic, ownership, pivot policy and numerical safeguards. Add ordinary correctness and allocation regressions.\\n'\n"+s[b:]
compile(s,str(D/'commit-integrate-publish.py'),'exec');(D/'commit-integrate-publish.py').write_text(s)
for n in ['publication_checks.py','finalization_checks.py']:(D/n).write_bytes((O/n).read_bytes())
(D/'phase-controls-prepare.py').write_bytes(Path(__file__).read_bytes());print('new phase integration publication controls prepared UNEXECUTED')
