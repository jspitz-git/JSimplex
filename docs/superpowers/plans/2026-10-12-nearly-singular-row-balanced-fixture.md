# S6-S: qualify a row-balanced nearly singular fixture

> Use superpowers:executing-plans inline. Diagnostic qualification only; no test edit.

S6-R reproduced the old point through new production FTRAN components and measured
nonzero stored LU representation residual under non-dyadic second-row scaling.
This motivates equal binary row norms rather than another unobserved guess. It does
not license backend control changes, tolerance/precision increases or weakened
assertions. Old cancellation stress and its failing strict oracle remain preserved.

Proposed Float32 construction (converted to the same four original scalar types):
s=2^-21,d=2^-44,delta=d/s=2^-23;
A=[s s;s-d s+d], row_lower=[-1,-(1+delta)], row_upper=[1,1+delta],
free columns,c=[0,-1],same default SolverOptions/public solve and original assertions.
All coefficients/bounds are exactly representable in Float32. Four entries remain
nonzero; both positive row sums are2s. Determinant2*s*d=2^-64 and infinity condition
number2^24+1. For y=A*x, x2=(y2-(1-delta)*y1)/(2d). The strict unique optimum
-2^44 occurs at y=[-1,1+delta],x=[-2^44-2^21,2^44]. Invertibility and bounded rows
exclude a recession direction. Dual[(1-delta)/(2d),-1/(2d)] is stationary with
proper row signs. This is a DIFFERENT feasible set and determinant from the original,
not an algebraically equivalent repair. It remains a two-row near-dependence case.

If production scaling yields [1 1;1-delta 1+delta] and UMFPACK uses p=q=[1,2],
row scale1/2, then L21=1-delta and U22=delta are exactly binary. With scaled RHS
[-2^21,2^21*(1+delta)], exact factor application yields the stated optimum. These
are conditional arithmetic predictions, NOT captured runtime metadata or a pass.

- [x] Reconcile no-recession regression intent and independently verify exact
  determinant/condition/strict optimum/dual and Float32 representability.
- [x] One bounded four-type diagnostic extracted testset with ONLY the proposed
  constructor substitutions and recording. Preserve all original status, publication,
  rational OPTIMAL and exact objective equality assertions, including public
  @inferred solve(problem). No old census/trace/replay repeat.
- [x] Record exact returned point/objective/residuals, model/options/policy/globals,
  presolve topology and work counts. Original 2rows/2columns/4nnz route is a gate;
  a removed row or materially different phase route cannot silently substitute for
  nearly-dependent full-basis coverage. Preserve any failure/reject unsupported.
- [x] If full-solve qualification supports the candidate, use the already captured
  small source matrix for a separately identified bounded factor metadata check
  with unchanged defaults. Verify actual L/U/p/q/Rs and exact residual, rather than
  assuming equal row sums guarantee every solve path. Distinguish new component
  metadata from hidden public-solve factors. No control mutations/opaque pointers.
- [x] Exit/process/source/pins and independent final numerical/work review. A passing
  candidate still needs a SEPARATE permanent RED/GREEN implementation plan with
  structural contract checks and neighboring regression/integration gates. Keep
  original strict equality and all tolerances/options/precisions unchanged.

One guarded Julia/BLAS1,heap2GiB,VM8GiB,minRAM6GiB,maxswap1GiB. Prior388033/388034/
388025 must be separately absent on verified host boot before edits/launch. Preserve
raw failures, userfiles and old environments. No forbidden large inputs/aliases,
accepted corpus/reference/cost reruns or CI enablement. No full-suite/x64 claim.

Completed: evidence90811de, fresh gpt-6-astra review no findings. Qualification13/13,
component6/6. Initial comparability false preserved with517-pin/current-external
supplement; component19gates615pins. See S6-ROW-BALANCED.md/review. Next separate
2026-10-12-nearly-singular-fixture-repair.md; production/test/CI unchanged.
