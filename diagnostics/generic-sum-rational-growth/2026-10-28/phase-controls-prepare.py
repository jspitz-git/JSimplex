from pathlib import Path
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-sum-rational-growth/2026-10-28');O=D.parents[1]/'generic-bounds-norm-infeasibility/2026-10-27'
s=(O/'RED-run/prepare.py').read_text()
s=s.replace("D=Path('"+str(O)+"')","D=Path('"+str(D)+"')").replace("O=D.parents[1]/'generic-ratio-monitor/2026-10-27'","O=D.parents[1]/'generic-bounds-norm-infeasibility/2026-10-27'")
s=s.replace('generic_bounds_norm_infeasibility_tests.jl','generic_sum_rational_growth_tests.jl').replace('Bounds norm infeasibility ARM','Sum rational growth ARM').replace('BNI_SOURCE','SRG_SOURCE').replace('BNI_COMPLETED','SRG_COMPLETED')
s=s.replace("c.read('comparison-2/contract.json')","c.read('contract-ready.json')").replace("c.read('comparison-2/pins.json')","c.read('pins-ready.json')")
oldline=next(v for v in s.splitlines() if v.startswith('common=(D/'))
s=s.replace(oldline,"common=(D/'common_ready.py').read_text().replace('contract-ready.json','contract.json').replace('pins-ready.json','pins.json')")
oldline=next(v for v in s.splitlines() if v.startswith('launch=(D/'))
s=s.replace(oldline,"launch=(D/'launch-ready.py').read_text().replace('from common_ready import','from common import').replace('contract-ready.json','contract.json').replace('pins-ready.json','pins.json').replace('admission-ready.json','admission.json').replace('892','2992').replace('900','3000')")
old="expected=c.read('test-gates.json')['expected_RED_failures'] if arm=='RED' else 0"
new="""if arm!='RED' and 'C' in c.read('test-gates.json')['accepted_variants']:
 for extra_file in ['refactorization_policy_tests.jl','refactorization_safety_tests.jl','refactorization_timing_tests.jl','refactorization_factor_tests.jl','refactorization_failure_tests.jl']:
  if extra_file not in files:files.append(extra_file)
expected=c.read('test-gates.json')['expected_RED_failures'] if arm=='RED' else 0"""
assert old in s;s=s.replace(old,new)
compile(s,str(D/'prepare-phase.py'),'exec');(D/'prepare-phase.py').write_text(s)
s=(O/'RED-run/audit.py').read_text().replace('BNI_SOURCE','SRG_SOURCE').replace('BNI_COMPLETED','SRG_COMPLETED').replace('Bounds norm infeasibility ','Sum rational growth ')
compile(s,str(D/'phase-audit.py'),'exec');(D/'phase-audit.py').write_text(s)
s=(O/'stage.py').read_text().replace('generic-bounds-norm-infeasibility/2026-10-27','generic-sum-rational-growth/2026-10-28').replace('generic_bounds_norm_infeasibility_tests.jl','generic_sum_rational_growth_tests.jl')
s=s.replace("changes=c.read('changes.json');names=set()","changes=[v for v in c.read('changes.json') if v['variant'] in c.read('test-gates.json')['accepted_variants']];names=set()")
compile(s,str(D/'stage.py'),'exec');(D/'stage.py').write_text(s)
s=(O/'commit-integrate-publish.py').read_text().replace('generic-bounds-norm-infeasibility/2026-10-27','generic-sum-rational-growth/2026-10-28').replace('codex/generic-bounds-norm-infeasibility','codex/generic-sum-rational-growth')
s=s.replace("message='Reduce multiprecision bound, norm and certificate temporaries\\n\\nReuse invocation-private comparison zeros only in BigFloat/RationalBigInt Boolean bound guards. Create the BigFloat direction cap only on positive overflow. Use zero-free comparisons and conditional endpoint magnitudes in the BigFloat infeasibility certificate while retaining all interval widenings, tolerances, guards, arithmetic order and ownership. Add ordinary whole-function correctness and allocation regressions.\\n'","message='Reduce accepted multiprecision sum certificate and growth temporaries\\n\\nApply only independently accepted whole-function scalar savings in BigFloat interval sums, exact RationalBigInt certification and PFI growth measurements. Preserve original arithmetic order, enclosures, numerical thresholds, ownership and refactorization policy. Add ordinary correctness and allocation regressions.\\n'")
s=s.replace("'fresh51wholefilesGREEN'","'freshwholefilesGREEN' ")
compile(s,str(D/'commit-integrate-publish.py'),'exec');(D/'commit-integrate-publish.py').write_text(s)
for n in ['publication_checks.py','finalization_checks.py']:(D/n).write_bytes((O/n).read_bytes())
(D/'phase-controls-prepare.py').write_text(Path(__file__).read_text());print('new phase/stage/integration controls prepared UNEXECUTED')
