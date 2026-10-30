from pathlib import Path
import json,hashlib
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');D=W/'diagnostics/dual-recovery-devex-task3/2026-10-30'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fresh(n,b):
 with (D/n).open('xb') as f:f.write(b)
for src,dst in [('/tmp/devex-task3-review.md','REVIEW-INITIAL.md'),('/tmp/devex-task3-review.json','review-initial.json')]:fresh(dst,Path(src).read_bytes())
r=json.loads((D/'review-initial.json').read_text())
if r['accepted']:raise RuntimeError('expected preserved F1 rejection')
fresh('REPORT.md.before-review',(D/'REPORT.md').read_bytes())
source=(D/'simplex_recovery.jl').read_text()
a='''        stop() && return nothing
        # Refined weight buffers are independent of rho; callbacks may have
'''
b='''        stop() && return nothing
        _recovery_weight_scope(trial,algorithm) || return nothing
        # Refined weight buffers are independent of rho; callbacks may have
'''
if source.count(a)!=1:raise RuntimeError('unique source delta')
fixed=source.replace(a,b)
# Prospective regression is written before the corrected candidate text.
tests=(D/'recovery_devex_fallback_tests.jl').read_text()
a1='''    failure::Exception
end
function (o::Observe)(reason,ws)
'''
b1='''    failure::Exception
    retained_pricing::Union{Nothing,J.PricingState{Float32},J.PricingState{Float64}}
end
function (o::Observe)(reason,ws)
'''
a2='''    if reason==:correction_attempt
        if o.mutate==:nonfinite_core
'''
b2='''    if reason==:correction_attempt
        o.retained_pricing=ws.scratch.pricing
        if o.mutate==:nonfinite_core
'''
a3='Observe(0,0,(:none,:none,:none),true,:never,:none,failure)'
b3='Observe(0,0,(:none,:none,:none),true,:never,:none,failure,nothing)'
a4='''        for mode in (:nonfinite_core,:finite_primal,:finite_rho,:stale_mode)
'''
b4='''        # F1: an existing callback retained private pricing state, then a later
        # false stop changes it after classification. Reject, do not throw.
        for mutate in (false,true)
            f=fixture();before=snapshot(f.ws);post_calls=Ref(0)
            r=construct(f;stop=()->begin
                if !isnothing(f.builder.last) && f.builder.last.corrections==1
                    post_calls[]+=1
                    held=something(f.observer.retained_pricing)
                    mutate && (held.algorithm=:primal)
                end
                false
            end)
            @test post_calls[]==1
            @test snapshot(f.ws)==before && f.ws.refactorizations==1
            @test f.builder.calls==1 && f.builder.last.corrections==1
            if mutate
                @test r===nothing
            else
                @test r isa J._RecoveryTrialResult && r.devex_fallback
            end
            @test f.ws.progress.diagnostics.counts[:pricing_devex]==0
        end
        for mode in (:nonfinite_core,:finite_primal,:finite_rho,:stale_mode)
'''
replacements=[(a1,b1),(a2,b2),(a3,b3),(a4,b4)]
reviewed_tests=tests
for old,new in replacements:
 if reviewed_tests.count(old)!=1:raise RuntimeError('unique test delta')
 reviewed_tests=reviewed_tests.replace(old,new)
fresh('recovery_devex_fallback_tests-reviewed.jl',reviewed_tests.encode())
fresh('simplex_recovery-reviewed.jl',fixed.encode())
report=(D/'REPORT.md').read_text()
report+='''\n## Initial review F1 and canonical selection\n\nThe initial review rejected one source-confirmed callback-window finding. The existing post-classification stop can return false while changing a PricingState retained from the original correction callback. Core finite/quality checks alone do not validate its algorithm; the Task2 preparation guard would then throw ArgumentError. Canonical simplex_recovery-reviewed.jl now rechecks _recovery_weight_scope immediately after that stop, before core validation/preparation, returning nothing for this stale state. It adds one scalar eligibility check only on the already fallback-ready cold branch; no extra stop, solve, array scan, quality evaluation or new retained production memory. Original source/check/rejected review remain frozen.\n\nCanonical recovery_devex_fallback_tests-reviewed.jl adds a typed retained-pricing reference in the private observer probe, captures that actual trial-owned object during correction_attempt, then mutates only its algorithm in the later false stop. The prospective regression requires normal refusal, unchanged live payload, one charged factor and no fallback event; an otherwise identical neutral callback still requires success. Tests are saved before the reviewed candidate. Neither this test nor any original test has run. The extra test-only retained state/counter is explicit bounded diagnostic memory, not production state.\n\nThe future source overlay uses simplex_numerics.jl (unchanged Task2), simplex_recovery-reviewed.jl and simplex_pivot.jl. Include the reviewed Task3 tests after canonical Task1 and Task2 tests. Do not load superseded originals alongside the reviewed versions. source-check.json and initial review bindings to REPORT.md map ONLY to REPORT.md.before-review; every other original binding stays at its original file. Final review/closure separately bind the current report and canonical files. Runtime/cost admission remains Task4; this source correction is not an executed RED/GREEN result.\n'''
(D/'REPORT.md').write_text(report)
checks={'exact_single_scalar_guard':fixed.replace(b,a)==source,'original_checks_frozen':sha(D/'source-check.json')==r['bindings'][str(D/'source-check.json')],'original_source_frozen':sha(D/'simplex_recovery.jl')==r['bindings'][str(D/'simplex_recovery.jl')],'original_tests_frozen':sha(D/'recovery_devex_fallback_tests.jl')==r['bindings'][str(D/'recovery_devex_fallback_tests.jl')],'before_report_exact':sha(D/'REPORT.md.before-review')==r['bindings'][str(D/'REPORT.md')],'typed_test_retention':'retained_pricing::Union{Nothing,J.PricingState{Float32},J.PricingState{Float64}}' in reviewed_tests,'mutation_and_neutral_control':'for mutate in (false,true)' in reviewed_tests}
bindings={str(D/n):sha(D/n) for n in ('simplex_recovery.jl','simplex_recovery-reviewed.jl','recovery_devex_fallback_tests.jl','recovery_devex_fallback_tests-reviewed.jl','REPORT.md.before-review','REPORT.md','source-check.json','REVIEW-INITIAL.md','review-initial.json','simplex_numerics.jl','simplex_pivot.jl')}
fresh('review-fix.json',(json.dumps(dict(accepted=all(checks.values()),scope='F1 source-only correction and prospective regression; Julia UNEXECUTED',checks=checks,bindings=bindings),indent=2)+'\n').encode())
if not all(checks.values()):raise RuntimeError(checks)
print(json.dumps(dict(accepted=True,checks=len(checks),bindings=len(bindings))))
