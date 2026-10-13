from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[4];D=Path(__file__).resolve().parent
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,s):
 with (D/name).open('x') as f:f.write(s)
old=(D/'candidate-tests-complete.jl').read_text()
extra='''# Mathematical residual computed exactly from actual stored input/output values.
function exact_residual_ok(A, x, rhs)
    Q = Rational{BigInt}
    a, v, b = Q.(A), Q.(x), Q.(rhs)
    residual = maximum(abs, a*v-b; init=zero(Q))
    eltype(A) <: Rational && return iszero(residual)
    matrix_norm = maximum((sum(abs(a[i,j]) for j in axes(a,2)) for i in axes(a,1)); init=zero(Q))
    scale = max(one(Q), matrix_norm * maximum(abs,v;init=zero(Q)),
                maximum(abs,b;init=zero(Q)))
    return residual <= 64 * Q(eps(eltype(A))) * scale
end
'''
new=old.replace('function star(::Type{T}, n) where T',extra+'function star(::Type{T}, n) where T')
a='''            b = J.MarkowitzBackend(Matrix{T}(I,3,3) + fill(one(T),3,3))
            @test b.sparse_pivots == 0
            out = zeros(T,3)
            J._backend_forward_solve!(out,b,fill(T(4),3))
            @test out == ones(T,3)'''
b='''            matrix = Matrix{T}(I,3,3) + fill(one(T),3,3)
            b = J.MarkowitzBackend(matrix)
            @test b.sparse_pivots == 0
            out = zeros(T,3)
            rhs = fill(T(4),3)
            J._backend_forward_solve!(out,b,rhs)
            @test exact_residual_ok(matrix,out,rhs)'''
if new.count(a)!=1:raise SystemExit('test fix selector')
new=new.replace(a,b);save('candidate-tests-reviewed.jl',new)
s=(D/'cost-schedule.md').read_text()
s=s.replace('-4 isolated upper reductions in a distinct timed window.', '- one first-use isolated upper reduction/reset in its own window, then\n  4 isolated upper reductions in a distinct steady timed window.')
s=s.replace('3840upper-only calls and3840explicitn-entry reset copies. Sum matrix dimensions\nper process960 ->76800 reset scalar assignments total.', '4800upper-only calls and4800explicitn-entry reset copies. Sum matrix dimensions\nper process960 ->96000 reset scalar assignments total.')
s=s.replace('9upper executions per visit (5full+4upper) ->82080', '10upper executions per visit (5full+1firstupper+4steadyupper) ->91200')
s += '''
## Review corrections R1/R2 (prospective, no measurement)

The allones solution is MATHEMATICAL, not a required exact floating endpoint of
LU. Require bitwise reference/candidate output equality including precision/sign
for every process-paired case. Separately, actual stored floating A,x,b must satisfy
an independent EXACT rational residual bound:
||A*x-b||inf <= 64*eps(T)*max(1,||A||inf*||x||inf,||b||inf).
Use the current specified BigFloat precision for eps; no raised solver precision.
Rational cases require exact zero residual. Upper-reduction publication still
requires exact sequential rounded reference parity. Nonfinite/signed-zero/flags
follow their explicit reference regressions; do not apply finite residual tests
to nonfinite cases. Freeze this bound now, never choose it from future output.

Both complete-forward and upper/reset wrappers use a first-use invocation with
repeat-count1 and the SAME callable signature as repeat-count4 steady windows.
No further warmup solve/reset allowed. Reference upper helper also gets its own
counted first use, since whole forward compilation does not compile that helper.
Scratch construction is a single FIRST-USE-ONLY attribution window per target
case, allowed to include compilation and initialization; never call it warmed or
require compile0 there. Kernel steady windows still require compile/recompile0.
Cold first-use and construction costs are recorded separately, not discarded or
subtracted. The additional960upper calls/resets do not change process/wall caps.
'''
save('cost-schedule-reviewed.md',s)
s=(D/'test-contract.md').read_text().replace('candidate-tests-complete.jl','candidate-tests-reviewed.jl')
s += '\nReview R1: dense-core floating equality is replaced by exact64eps scaled residual\nvalidation; Rational remains exact. Cost comparisons separately require original/\ncandidate bits. Initial complete test and its old dense equality remain preserved.\n'
save('test-contract-reviewed.md',s)
p=R/'diagnostics/simplex-core-architecture/MA-MARKOWITZ-UPPER-PREPARATION.md';save('report.before-review.md',p.read_text());s=p.read_text().replace('Canonical tests are candidate-tests-complete.jl','Canonical tests are candidate-tests-reviewed.jl').replace('cost-schedule.md freezes','cost-schedule-reviewed.md freezes').replace('4complete solves and4upper reductions per case plus first\nsolve. Totals960constructors/4800complete solves/3840upper calls/3840resetcopies\n(76800scalar assignments)/82080selected multiply-subtract pairs','4complete solves and4upper reductions per case plus first\nsolve and first upper/reset. Totals960constructors/4800complete solves/4800upper calls/4800resetcopies\n(96000scalar assignments)/91200selected multiply-subtract pairs')
s += '''
## Preserved review corrections

Initial independent review found two Important preparation issues: requiring
exact floating dense-LU allones output, and omitting the cold isolated-upper
wrapper from the work/compilation budget. Initial review, report and all candidate
texts/schedules remain unchanged at their original bindings. Canonical reviewed
texts fix both: exact64eps scaled residual for finite floating outputs, exact
Rational residual, separate mandatory reference/candidate bit equality; one
counted first-use upper/reset per case before4steady repeats. Scratch-creation
windows are explicitly first-use-only, may include compilation and cannot claim
warmed allocation cost. Complete solve production candidate is unchanged.

Initial source-check report hash maps ONLY to report.before-review.md; candidate,
initial complete tests and initial schedules remain at their original paths.
review-fix.json binds canonical reviewed tests/contracts/schedule and corrected
report separately. This is offline source review, no executed Julia correction.
'''
p.write_text(s)
checks={'old_dense_exact_assertion_present':a in old,'reviewed_dense_residual_check':b in new,'bound_frozen_64eps':'64 * Q(eps(eltype(A))) * scale' in new,'cold_upper_explicit':'one first-use isolated upper' in (D/'cost-schedule-reviewed.md').read_text(),'recount_upper4800':4800==20*48*5,'recount_reset_entries96000':96000==20*960*5,'recount_pairs91200':91200==20*456*10,'scratch_firstuse_explicit':'FIRST-USE-ONLY' in (D/'cost-schedule-reviewed.md').read_text()}
paths=[p,D/'candidate-tests-reviewed.jl',D/'cost-schedule-reviewed.md',D/'test-contract-reviewed.md',D/'report.before-review.md',D/'review.md',D/'review.json',D/'review-fix.py']
save('review-fix.json',json.dumps({'all_passed':all(checks.values()),'checks':checks,'sha256':{str(x.relative_to(R)):h(x) for x in paths},'scope':'offline source correction; no Julia RED/GREEN or numeric execution'},indent=2)+'\n')
print(checks)
if not all(checks.values()):raise SystemExit(1)
