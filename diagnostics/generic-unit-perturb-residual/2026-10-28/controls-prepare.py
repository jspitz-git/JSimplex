from pathlib import Path
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-unit-perturb-residual/2026-10-28');O=D.parents[1]/'generic-residual-pivot-crash/2026-10-28'
for name in ['prepare-phase.py','phase-audit.py','stage.py','commit-integrate-publish.py','publication_checks.py','finalization_checks.py']:
 s=(O/name).read_text().replace(str(O),str(D)).replace('generic_residual_pivot_crash_tests.jl','generic_unit_perturb_residual_tests.jl').replace('Residual pivot crash','Unit perturb residual').replace('RPC_','UPR_').replace('codex/generic-residual-pivot-crash','codex/generic-unit-perturb-residual')
 s=s.replace('common_final.py','common_reviewed.py').replace('from common_final import','from common_reviewed import').replace('launch-final.py','launch-reviewed.py').replace('contract-final.json','contract-reviewed.json').replace('pins-final.json','pins-reviewed.json').replace('admission-final.json','admission-reviewed.json')
 if name=='prepare-phase.py':
  s=s.replace("O=D.parents[1]/'generic-sum-rational-growth/2026-10-28'","O=D.parents[1]/'generic-residual-pivot-crash/2026-10-28'")
  a=s.index(" for extra_file in [");b=s.index(']:',a)
  s=s[:a]+" for extra_file in ['simplex_perturbation_tests.jl','primal_perturbation_tests.jl','primal_perturbation_integration_tests.jl','lp_refinement_tests.jl','lp_refinement_integration_tests.jl']"+s[b+1:]
 if name=='commit-integrate-publish.py':s=s.replace('Reduce accepted residual pivot and crash scalar temporaries','Reduce unit-weight pricing and perturbation and residual temporaries')
 compile(s,str(D/name),'exec');(D/name).write_text(s)
(D/'controls-prepare.py').write_bytes(Path(__file__).read_bytes())
print('phase/integration controls prepared, unexecuted')
