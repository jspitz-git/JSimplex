# S6-N: nearly singular objective census

Status: diagnostic census complete and independently accepted (gpt-6-astra/high). No production
or permanent test change. CI stays disabled; this is not full-suite/x64 validation.

## Existing evidence and unchanged experiment

`results/S6-N/existing-failure-map.json` retains one solver_tests.jl:552 equality
failure from each historical CI run38149970679/38142752357. Their printed values
alone do not identify the scalar type. Accepted prior certificate evidence includes
`../primal-certificate-work/results/SUMMARY.md` (15689 broad semantic, 1304/1216
focused, 1680 exact differential) and `../adaptive-degeneracy/presolve-tolerance.md`
(recession checks). These are background, not a recorded point/type for this case;
none was rerun.

`reproduce/nearly_singular_objective_census.jl` extracts the exact original testset
and inserts model snapshots before, and read-only recording after, the unchanged
`@inferred solve(problem)`. Reversing that insertion reconstructs the original text.
All original assertions, constructors, options and four types remain unchanged.
Reconstructed default SolverOptions/policy are reported, not injected into solve.
Postsolve analytic certificate checks do not capture the actual internal witness.

Raw `.superpowers/simplex-core-architecture/S6-N/census-2`, portable
`results/S6-N/census-2-*`: 4 cases, **13 pass / 1 original equality failure**, exit1
preserved; all **22 diagnostic audit checks**,607 pins, actual source/test SHA,
model snapshots and ambient globals pass. Julia1.13.0 aarch64, BigFloat256 nearest,
Julia/BLAS1, heap2GiB/VM8GiB/RAM6GiB/swap1GiB guard. This is a diagnostic success,
not a passing original test. Process/elapsed includes compilation, no timing claim.

`census-1` is incomplete: 4pass/1 harness error (unqualified internal Basis), one
Float32 record; Float64 solve finished but recording failed, remaining types never
ran. Driver, raw log/report/process and pins retained. Its pins were independently
verified before qualifying the internal names. No accepted measurement was repeated.

## Exact stored problem

Let s=2^-20 and d=2^-43. All types receive the exact conversion of the Float32 matrix
A=[s s; s s+d], determinant s*d=2^-63. The free columns and rows y=A*x give
x2=(y2-y1)/d. For -1<=y1,y2<=1, x2<=2/d=2^44. The unique strict optimizer is
x=[-2^44-2^20,2^44], y=[-1,1], objective -2^44. The exact dual vector
lambda=[1/d,-1/d]=[2^43,-2^43] satisfies c-A'lambda=0 with the proper lower/upper
row signs. Invertibility and two bounded rows exclude any nonzero recession ray.

With independent original row tolerance t, feasibility allows -1-t<=yi<=1+t,
so c'x>=-2(1+t)/d. Moreover for ANY returned point, with r=y-[-1,1],

    c'x - (-2^44) = 2^43*(r1-r2).

This exact identity explains amplification by the near singular matrix. It does
not claim strict feasibility/optimality of a point outside the original bounds,
nor that the solver optimizes a globally relaxed LP. Original tolerances are
feasibility/complementarity acceptance criteria; internal solve-quality policy is
separate. No tolerance or precision change is justified by a small relative gap.

| Type | Status | Exact objective gap | Exact returned rows | Publication |
| --- | --- | --- | --- | --- |
| Float32 | NUMERICAL_ERROR | none | no returned point | no primal/objective |
| Float64 | OPTIMAL | -1/16 | [-1,1+2^-47] | tolerance-feasible, not strictly feasible |
| BigFloat | OPTIMAL | 0 | [-1,1] | strict optimum |
| Rational{BigInt} | OPTIMAL | 0 | [-1,1] | strict optimum |

Every case uses2iterations/1refactorization. Float32 reason is structural primal
failed original-model feasibility checks. Float64 printed objective is exactly
the historical CI evaluated value, but equality of this observed value does not
prove the historical CI scalar/path/backend cause.

For all three returned points the objective exactly equals c'x of the stored
primal. Original primal certification passes, as does the separately supplied
analytic witness through `_original_witness_certified` with synthetic basis
[1,2] and states BASIC,BASIC,AT_LOWER,AT_UPPER. Exact stationarity and distances
to the priced bounds are independently checked; for Float64 the only violation
is2^-47, below its unchanged default primal tolerance (Float64 representation of
1e-7). This explains acceptance using actual residuals, not relative error alone.
The synthetic witness is NOT the runtime witness, basis, or trajectory. Solver
source separately shows internal primal/optimality gates before publication and
the outer original-point gate; no diagnostic bypass was inserted.

## Work, memory and limits

No production execution frequency, solve, allocation or retained cache changes.
Diagnostic snapshots/rationalization/certificate checks occur only before/after
four tiny solves. No kernel speedup, allocation saving, measured overhead, x64
success or full project gate is claimed. Scalar type of the historical log alone
remains unknown; local Float64 reproduction is positive evidence only.

Original floating equality demands a strict optimizer despite a toleranced
acceptance contract. Do not silently replace it with `isapprox` or a loose status
list. A subsequent fixture proposal must retain the equality and recession intent
while eliminating this cancellation-sensitive construction, and must be qualified
separately. The original case/failure remains valuable preserved diagnostic evidence.

Independent review: S6-NEARLY-SINGULAR-REVIEW.md accepts the proof and evidence.
One P3 duplicate postsolve model snapshot is deferred without editing the pinned
driver or rerunning evidence. Production/test/workflow and all three preserved
main user-file hashes remain unchanged. No fresh production integration is needed.
