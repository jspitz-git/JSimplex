# MA-D: private Markowitz upper candidate preparation

2026-10-13. OFFLINE preparation only, baseline diagnostic3e6c351 and master6f68e24.
No Julia/query/parser/import/compile/Pkg/numerics/launcher or actual src/test/env/CI
changes. Candidate is UNEXECUTED and not accepted for production or performance.

## Delivered package

results/MA-D/candidate-markowitz.jl is complete source with one loop call replacement
and private helpers; helpers.jl/original-upper-loop.jl/inverse.json provide exact
whole-source inverse. candidate-JSimplex.jl adds only direct MA import;
candidate-Project.toml adds the direct UUID and exact =1.8.1 compat. No dependency
resolution/install was attempted. candidate-runtests.jl adds only the test include.
Canonical tests are candidate-tests-reviewed.jl; original candidate-tests.jl is
preserved with its initial preparation binding. Both remain unexecuted.

Generic hardware loop preserves original arithmetic. Exactly two specialized
entries cover BigFloat and Rational{BigInt}. BigFloat compares effective/global
rounding before MA; mismatch invokes the untyped original method. Scalar scratch
is lazy, private per call, reused across eligible rows only; first subtraction
reads the borrowed seed without premature rounding, final ordinary division
publishes independent storage. No backend layout/cache/pool changes.

Eligibility checks paired lengths, finite seed, diagonal bounds/assignedness
before speculative diagonal read, coefficient/work assignment/bounds and finite
values. False uses original row arithmetic and original final diagonal lookup.
No exception catch/retry or skipped zero. Malformed diagonal plus earlier 0*Inf
must keep the original DivideError precedence. Scratch never mutates borrowed
scalars, including work entries initially aliased to RHS or rational BigInt leaves.

## Prospective correctness

Six named testsets cover dispatch/fallback, actual scalar and BigInt-leaf aliases,
independent output retention, ordered arithmetic/cancellation/mixed precision,
scoped/nested rounding, nonfinite/exception/partial-publication cases, MPFR flags,
precision changes, large->small rational inputs and small public PFI copy/refactor/
in-place lifecycles. Source presence of tests is not executed coverage.

Original-source RED will be two explicit missing-helper assertions, remaining
new tests guarded. Future admission must count actual test entries/assertions and
exclude incidental errors/broken tests. No Julia RED has run. The original row
loop is independently transcribed in the test module, not shared candidate logic.
Python oracle.py separately implements exact Rational and sequential binary
rounding for finite values without exponent limits; eight exact synthetic checks
pass. Signed zeros/nonfinite/exponent limits/MPFR flags are deliberately outside
that mathematical oracle and covered by explicit original-arithmetic regressions.
No hidden trajectory/observer-neutrality/native-memory claims.

## Fixtures, schedule and work

fixtures.json freezes8 matrices/storage combinations and6 scalar configurations,
48 cases, dimensions8/32. Long-upper-row star and dense-core-only controls use
exact dyadic entries with known allones solution; sparse and dense storage both.
Star prospective S=n-2,K=n-1,E=1 follows singleton-column priority then density
cutoff at2. These counts must be asserted on actual constructed backends; no
post-output fixture tuning if they fail. Hardware E=0 by dispatch.

cost-schedule-reviewed.md freezes3warm+7measured alternating process pairs,20serialcost
processes,48cases each,4complete solves and4upper reductions per case plus first
solve and first upper/reset. Totals960constructors/4800complete solves/4800upper calls/4800resetcopies
(96000scalar assignments)/91200selected multiply-subtract pairs,640separate scratch
setup measurements. Counts are source-derived, not complete internal GMP/backend
work. Per-process60s and cost-global600s cap; prospective qualification<=120s is
separate. No process or allowance reservation exists. Exact qualification test
counts, wrappers, manifests and audit are MA-E admission obligations.

Complete-solve timings include lazy scratch/eligibility/output division. Upper
attribution includes identical explicit resets on both sides and cannot be
subtracted into a pure kernel cost. Startup, first solve, scratch setup and steady
calls remain separate. Each new process must compile measurement wrapper with its
first-use call using the same signature before its measured repeats; no extra
hidden solve warmups. Fresh processes do not inherit warm compilation from earlier
pairs. Record compile/GC/outliers/process confounding and all raw samples.

Target kernel adds O(K) read-only eligibility, checks and one local2BigFloat or
12BigInt scratch set per eligible call; no extra production solve/vectorcopy or
persistent memory. Ordinary division remains an allocation. Rational MA integer
GCD/division work differs from Base GMP rational arithmetic; no speedup follows
from equal high-level counts or MA-A. Native limb growth and retention are not
bounded by Julia graph size. Extra work is explicit and must earn its cost in a
later complete-solve measurement; no performance acceptance is made here.

## Continuation and evidence

MA-C current continuation hashes map only to MA-D STATUS.md.before-MA-D and
roadmap.md.before-MA-D, all older mappings unchanged. Fresh host refs/boot/full44
groups AND sessions/noJulia and protected settings/environments verified. Initial
preparation.json binds initial test text, helpers, candidates and fixture generator
before execution. Canonical test extension is separately bound, never retroactively
substituted for the initial test hash. All raw/evidence retained.

Next MA-E prepares a concrete offline admission package and exact assertion/process
budgets. A subsequent admitted short run uses standing human permission without
asking again; no unspecified launch from this report. Automation paused, CI off,
HH reuse disabled, stopped routes closed. Broader plan and MA integration open.

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
