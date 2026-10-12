# S6-R: original-bound factor-component replay

Status: bounded component replay and exact post-exit audit complete; final review
pending. No production/test/CI or backend-control change. No full solver, workspace,
accepted census, old trace, long reference or cost benchmark rerun.

## Result and integrity

Two local Float64 cases: fresh factorization of captured B and initial -I factor /
copy / refactor to B. Each performs one production ordinary FTRAN and one BTRAN:
four basis solves total.12/12diagnostic assertions,exit0,21audit gates,613pins.
517existing source/test/runtime/environment/launcher pins match accepted S6-Q;
model-derived inputs/options/policy/threads match. Same Julia1.13.0aarch64,
Julia/BLAS1,heap2GiB/VM8GiB/minRAM6GiB/maxswap1GiB. Source input and local
SparseArrays umfpack.jl contract file pinned. Model/rhs/control preserved.
Raw .superpowers/simplex-core-architecture/S6-R/replay-1 and portable
results/S6-R/replay-1-* retained. Source driver and copied driver match.

Both cases reproduce the exact saved S6-Q primal and raw rho values, with identical
recorded L/U/p/q/Rs/control arrays. No eta updates. The copy path starts from -I,
shares the original numeric object, gives its candidate no spare, then refactors
privately. Source consequently calls fresh lu(B); old -I factor remains separate.
No symbolic reuse or historical numeric-object identity is demonstrated.

Original-bound scaled B=[1 1;1 1+2^-23], derived primal RHS[-2^20,2^20], costs
for BTRAN[0,-1]. The original trace's final scratch RHS belongs to BTRAN and was
not used as primal input. Saved policy hypersparse=false/solve_refinement=false
selects ordinary forward/transpose kernels; skipped wrapper bookkeeping and
refinement checks perform no additional numerical solve in this configuration.
No workspace needed in this bounded replay. This is not generic wrapper coverage.

## Exact factor representation and application decomposition

Supported SparseArrays properties are read AFTER both numerical solves. Their
contract is L*U==(Rs.*B)[p,q], interpreted here via exact rational arithmetic to
measure floating representation error rather than assert bitwise exact algebra.
The local Julia defaults retain UMFPACK scaling_mode1 and refinement_steps0;
controls are unchanged. The recorded new component factors have:

- p=q=[1,2], Rs=[1/2,281474959933441/562949953421312].
- L21=281474959933441/281474976710656, L diagonal1.
- U11=U12=1/2, U22=16777215/281474976710656.
- Exact L*U-(Rs.*B)[p,q] is zero except entry(2,2)=-2^-72.

Thus the exact factorization identity DOES NOT hold for these stored floats.
It is explicitly false in the audit, not a failed diagnostic gate hidden as pass.
The strict rational solution is[-2^44-2^20,2^44]. Let xf be exact application of
stored rationalized Rs/L/U/p/q to exact b, and x the recorded Float64 result.
For objective c=[0,-1], the exact telescoping decomposition is:

- c'*(xf-xstrict)=-1048576/16777215 (factor-representation contribution).
- c'*(x-xf)=1/268435440 (floating application contribution).
- Sum=-1/16, exactly the component and saved full-solve objective gap.

Recorded primal equation residual=[0,2^-27]; recorded dual stationarity
residual=[0,-2^-48]. Row scaling converts the primal residual to original2^-47.
This separates stored-factor representation from total application error in these
NEW component cases. It is not attribution to one internal machine operation,
not proof of the old solver/CI hidden factor metadata, and not a diagnosis of all
nearly singular models. Metadata retrieval/rounding of RHS application is included
in this mathematical representation split; no special UMFPACK control was changed.

## Work/memory and next step

No production scans/solves/allocations/retention changed. Fixed2x2 diagnostic does
three factorizations (fresh B; -I then fresh B through refactor),one factor copy,
four basis solves, one supported metadata extraction after solves per case,
small owned snapshots and offline exact rational calculations. No repeated warm
samples, timing/speedup or retained-memory benchmark claim. No opaque pointers
serialized. No promotion or full-suite/x64 success claimed.

Runner388033/start23154640,child388034/start23154718,driver388025 separately absent,
noJulia,boot20de7dde-704e-41c8-bee7-b8511c0a86b0 after exit.

The evidence supports a separate row-balanced fixture hypothesis: equal binary
row norms can avoid THIS recorded non-dyadic row scaling/factor representation
path while preserving a full two-row nearly singular problem and exact optimum.
Qualification must verify topology, new backend metadata and all original assertions;
it is not assumed successful or equivalent to the old feasible set. See next plan
2026-10-12-nearly-singular-row-balanced-fixture.md. Permanent test edit requires a
later RED/GREEN plan; no control/tolerance/precision/solver change is authorized.
