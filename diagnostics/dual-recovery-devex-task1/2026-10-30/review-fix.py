from pathlib import Path
import json,hashlib,shutil
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl')
D=W/'diagnostics/dual-recovery-devex-task1/2026-10-30'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def fresh(p,b):
    with p.open('xb') as f:f.write(b)
for src,dst in [('devex-task1-source-review.md','REVIEW-INITIAL.md'),('devex-task1-source-review.json','review-initial.json'),('devex-task1-source-review.provisional-before-author-finding.md','review-provisional.md'),('devex-task1-source-review.provisional-before-author-finding.json','review-provisional.json')]:
    fresh(D/dst,(Path('/tmp')/src).read_bytes())
fresh(D/'REPORT.md.before-review',(D/'REPORT.md').read_bytes())
old=(D/'refinement_outcome_tests.jl').read_text()
a='refine=true;poison=1;want=:nonfinite_quality;invalid=true;stops=1;expected_point=copy(x)'
b='x=T[0.5,0];refine=true;poison=1;want=:nonfinite_quality;invalid=true;stops=1;expected_point=copy(x)'
if old.count(a)!=1: raise RuntimeError('unique fixture anchor')
new=old.replace(a,b)
fresh(D/'refinement_outcome_tests-reviewed.jl',new.encode())
report=(D/'REPORT.md').read_text()
report=report.replace('`refinement_outcome_tests.jl` contains ordinary Test','Canonical `refinement_outcome_tests-reviewed.jl` contains ordinary Test')
report+='''\n## Review correction and canonical selection\n\nThe initial independent review rejected one prospective fixture (F1): the initial zero point in `nonfinite_wide_quality` made the compensated evaluator skip Inf*0. No numerical test was run. The canonical main tests are now `refinement_outcome_tests-reviewed.jl`, with only that fixture initialized to [0.5,0]. Initial ordinary quality is finite/unreliable (relative error 1/3); poisoning the diagonal before wide quality evaluates Inf*0.5 and supports the original hard-cause/zero-solve/one-stop expectations for both orientations. All original expectations and candidate numerical code remain unchanged. This is a source-derived argument, not an executed pass.\n\nThe original tests, 87-check/155-binding source proof and initial rejected review remain frozen. A provisional clean reviewer assessment that missed this issue is also preserved separately; it is not acceptance. Initial review bindings of REPORT.md resolve only to the byte-identical REPORT.md.before-review. Separate review-fix.json verifies the single-line correction, unchanged original bindings and prospective checks. The bounded reference comparison still imports the same test module name after including the canonical reviewed main tests. No additional driver or launcher is introduced.\n'''
(D/'REPORT.md').write_text(report)
record=json.loads((D/'source-check.json').read_text())
print('source keys',list(record))
checks={'unique_fixture_replacement':new.count(b)==1,'exact_inverse':new.replace(b,a)==old,'original_test_hash_preserved':sha(D/'refinement_outcome_tests.jl')==json.loads((D/'review-initial.json').read_text())['bindings'][str(D/'refinement_outcome_tests.jl')],'candidate_files_unchanged':all(sha(D/n)==json.loads((D/'review-initial.json').read_text())['bindings'][str(D/n)] for n in ('simplex_numerics.jl','simplex_recovery.jl')),'report_before_review_exact':sha(D/'REPORT.md.before-review')==json.loads((D/'review-initial.json').read_text())['bindings'][str(D/'REPORT.md')],'no_julia_executed':True}
bindings={str(D/n):sha(D/n) for n in ['refinement_outcome_tests.jl','refinement_outcome_tests-reviewed.jl','simplex_numerics.jl','simplex_recovery.jl','reference.jl','reference_comparison_tests.jl','source-check.json','REPORT.md.before-review','REPORT.md','REVIEW-INITIAL.md','review-initial.json']}
fresh(D/'review-fix.json',(json.dumps({'accepted':all(checks.values()),'scope':'offline single-fixture correction only; Julia UNEXECUTED','checks':checks,'bindings':bindings},indent=2)+'\n').encode())
if not all(checks.values()):raise RuntimeError(checks)
print(json.dumps(checks))
