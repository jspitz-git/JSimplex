# S6-T: nearly singular no-recession test repair

Candidate test-only correction following independently accepted S6-S. Production,
options, tolerances, arithmetic precision and CI remain unchanged. Master7fea422;
review/integration pending. No claim of full-suite/x64 success.

The old cancellation-sensitive fixture allows tolerance-feasible Float64 points
with a strict objective difference (S6-N/Q/R); exact equality was not guaranteed
by the old numerical path. The new row-balanced construction retains two nearly
dependent rows, free columns, four nonzeros and the exact no-recession objective
contract. It is a different feasible set, not an equivalent transformation or
solver repair. Old original stress and all failed candidates remain preserved.

Changes only inside the existing testset:
- scale2^-21,delta2^-44,A=[s s;s-d s+d],symmetric bounds±[1,1+2^-23];
- six exact structural assertions once before the scalar loop: size/nonzeros,
  determinant2^-64,equal row sums,proposed bounds and exact optimal vertex rows;
- explanatory comment; original four types, public @inferred solve and every
  original postsolve assertion byte-identical. Exact equality is not weakened.

The determinant/invertibility and finite rows exclude recession. Exact objective
-2^44 at x=[-2^44-2^21,2^44], conditioninf2^24+1 and stationary signed dual were
independently verified in S6-S. Public qualification retained2/2/4 topology and
phase I/II; separate component had exact dyadic LU identity. Neither is a capture
of hidden factors or an x64 guarantee. S6-S was not rerun against the changed test.

## RED / GREEN

RED red-1: old matrix and old bounds with six new structural conditions. Extracted
prefix excludes the scalar loop, so zero solve calls. 2pass/4expected failures,
exit1,13audit gates,614independent pins. Failures are determinant,row sums,bounds,
strict-point rows. Raw/source/selected text retained.

GREEN green-1: exact current testset plus three inspected neighboring regression
sets in one process. 192/192 total: affected19, floating status17, dependent rows68,
objective cancellation88. Forty public solve calls, no helper dependency or old
control repetition. Exit0,14audit gates614pins,original oracle/source verified.
No production or neighboring testset bytes changed. Main user/env hashes match.

Both guards use Julia/BLAS1,heap2GiB,VM8GiB,minRAM6GiB,maxswap1GiB. All process/pin/
actual-source checks completed. Separate host absence391357/391358/391344 verified,
boot20de7dde-704e-41c8-bee7-b8511c0a86b0. Old RED processes also separately absent.

## Work and limits

No production work, allocations, retained memory, solves or invariant checks added.
Test adds fixed2x2 rational conversion/determinant/matvec and tiny arrays once per
testset, outside four-type loop. Bound-vector construction is tiny cold test work.
No material hot-path cost change; no benchmark/speedup warranted or claimed.

Full-suite historical failures in other families and actual CI platform remain
open. CI remains manually disabled. Fresh final numerical/work review and one
actual-master affected-testset check are required before authorized push.
Next bounded diagnostic plan:2026-10-12-primal-price-recovery-reachability.md.
Existing S6-U failure map merely aggregates twelve historical assertions per run.
