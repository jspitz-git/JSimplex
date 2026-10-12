# S6-S: row-balanced nearly singular fixture qualification

Diagnostic qualification, not a permanent repair. Production, tests, tolerances,
precision, backend controls and CI are unchanged. Base diagnostic3baf29b,
master7fea422. No accepted old solve, trace, replay, corpus or cost rerun.

## Contract and exact construction

The original regression requires an invertible, nearly dependent two-row bounded
model with free columns and no recession ray. Its status/publication assertions
and exact objective equality remain unchanged. S6-N preserves the original
cancellation stress and its strict equality failure. This proposal is a different
feasible set, not an equivalent transformation or repair of the solver.

Construct in Float32, convert to the original four types:
s=2^-21,d=2^-44,delta=2^-23;
A=[s s;s-d s+d],bounds±[1,1+delta],c=[0,-1],free columns.
All entries/bounds are exactly Float32 representable. Four nonzeros, determinant
2^-64, infinity condition2^24+1. For y=A*x,
x2=(y2-(1-delta)*y1)/(2d); unique strict optimum-2^44 is attained at
x=[-2^44-2^21,2^44],y=[-1,1+delta]. Signed dual
[(1-delta)/(2d),-1/(2d)] is stationary. Invertibility and bounded rows exclude
recession. Independent Python Fraction/Float32 checks and Julia exact records agree.

## Four public solves

`qualify-1`:13/13 original assertions,exit0,612 independently checked pins.
All Float32,Float64,BigFloat,Rational{BigInt} return OPTIMAL with the exact strict
point/objective, zero exact row violations, two iterations and one refactorization.
The unchanged public `@inferred solve(problem)` is preserved. Only constructor
substitutions and pre/post recording are made to the extracted testset; reverse
substitution asserts byte equality with the original. All original oracle statements
remain. Default options/policy/tolerances match saved S6-N per scalar; model and
ambient BigFloat precision/rounding remain unchanged. Original primal and separately
supplied analytic dual/basis certificates pass; no runtime witness is captured.

Logs retain2rows/2columns/4nnz after presolve and phase I/II for all four cases.
This establishes the visible topology/phase summary and work counts, not hidden
trajectory or identity of public-solve factor objects.

The initial audit preserves `all_passed=false`:30/31 checks passed. Its broad
`/src/` comparability filter included an external SparseArrays umfpack.jl file
pinned by S6-R but not this launch. The separate comparability supplement verifies
all517 shared source/test/environment/runtime/launcher pins and the additional
current file hash against R. It explicitly does not retroactively add a launch
pin. All other30 gates pass. No auditor or numerical run was repeated/overwritten.

## Separate component

`factor-1`:6/6,exit0,19/19audit gates,615 independent pins. The input is the saved
candidate Float64 matrix/model. One production scale_problem, one fresh native
basis factorization, one ordinary FTRAN and one BTRAN; no solver/workspace/eta/copy
or refactor lifecycle replay. Default policy selects ordinary unrefined kernels.
Supported owned L/U/p/q/Rs arrays are extracted AFTER solves; controls unchanged.
This launch explicitly pins the local SparseArrays source file as well.

Actual row factors=[2^-21,2^-21],column factors=[1,1],
B=[1 1;1-delta 1+delta],rhs=[-2^21,2^21*(1+delta)],dualrhs=[0,-1].
p=q=[1,2],Rs=[1/2,1/2],L=[1 0;1-delta 1],U=[1/2 1/2;0 delta].
Exact `L*U-(Rs.*B)[p,q]`, primal and dual residuals are all zero. Primal matches
new public endpoint. This verifies the conditional dyadic argument for this new
component; it is not capture of hidden public factors or proof for another backend.

## Work, preservation and limitations

Four new tiny public solves with cold compilation; diagnostic postsolve model
snapshots/rational conversions and analytic certificates are fixed2x2 work.
One separate scaling/factorization and two basis solves plus owned metadata copies.
No production allocation/retention/cost change; no benchmark or speedup claim.
No extra full solver, old control, corpus or measurement. No source/test changes.
Raw/portable records and source snapshots retained under results/S6-S and
.superpowers/simplex-core-architecture/S6-S. Initial false audit remains explicit.

Last separate host check:389862runner/389863child/389852driver absent,noJulia,
boot20de7dde-704e-41c8-bee7-b8511c0a86b0. CI remains disabled. Actual x64/full-suite
success, broader S6 and end-to-end last-bit sensitivity are unproved.

Final independent numerical/work review pending. Only after acceptance proceed to
2026-10-12-nearly-singular-fixture-repair.md, a separate permanent RED/GREEN plan.
