# S6-K: supplied-tolerance status census

Diagnostic conclusion: the original primal-kind test expects an invalid
infeasibility certificate under the current independent row/column tolerance
contract. No production or permanent test changes are made.

## Existing evidence reconciled

Both historical CI runs have exactly30 failures at bigfloat_integrity_tests.jl:282,
NUMERICAL_ERROR versus INFEASIBLE. Earlier adaptive-degeneracy reports already
established that a strictly inconsistent LP may have a tolerance-feasible point,
and that rejection of an inconclusive certificate need not find that point.
Accepted16099 semantic checks and104 real-model configurations are not rerun.
See ../adaptive-degeneracy/simplex-infeasibility-tolerance.md and presolve-tolerance.md.
The old Float64 1024-row witness differs from this supplied BigFloat fixture.

## Exact contradiction of the old oracle

The fixture requires x >= g and fixes the column at zero, with g=2^-24 and
primal tolerance t=g-2^-80. It is strictly inconsistent, and g>t, but the tolerance
contract allows each original row and column violation independently. The point
x=g/2 has row violation g/2 and column violation g/2, both strictly less than t.
The exact margin t-g/2 is 2^-25-2^-80, positive. No rounding assumption is involved.
Therefore INFEASIBLE is not a valid tolerance-envelope conclusion for this model.
The current conservative NUMERICAL_ERROR does not publish an invalid proof or a
feasible solution; it does not establish the missing feasibility-recovery feature.

## Current-source evidence

The census selects only kind=:primal from the original source loop. This is the
fixture branch name; actual options.algorithm is :dual in all30 cases. The solve
call and every original assertion are unchanged. Only a post-solve record call is
inserted. A reversible text check reconstructs the original selected testset.
No second solve, paired observer, or production override is used.

Julia1.13.0 AArch64;30 cases =3 ambient precisions(24,53,256) x5 rounding modes
x2 refactor intervals. All30 return NUMERICAL_ERROR with message
"row combination does not certify infeasibility at primal tolerance", zero
iterations and one refactor. No primal/objective is published. Stored options
retain256 bits and exact t, and exact model values stay unchanged. Ambient globals
are restored. All30 independently rationalized witness values equal g/2 and the
production original-space primal certificate accepts each witness.

The unmodified oracle has270pass/30fail, exit1; all failures are exactly the old
INFEASIBLE assertion. This failed test result is preserved, not labeled a pass.
All19 diagnostic audit gates pass: expected exit, immutable source/pins and manifest,
actual source/test hash,30 unique cases, only status failures, model/options/globals,
no publication, independent exact witness and production witness acceptance.
Raw .superpowers/simplex-core-architecture/S6-K/census-1; portable results/S6-K.
Runner379310/child379311/driver379301 separately absent, noJulia, boot
20de7dde-704e-41c8-bee7-b8511c0a86b0. Final independent review accepts diagnostic scope without blockers; see
S6-PRECISION-STATUS-REVIEW.md. Minor duplicated diagnostic rationalization is
deferred without changing accepted source or rerunning evidence.

## Source-path and scope

solver.jl preserves supplied options, scopes automatic policy construction to owned
input precision, and leaves solve arithmetic at ambient precision. This census
records actual options; it does not intercept or reconstruct the runtime policy.
presolve_tolerance.jl rechecks strict presolve infeasibility against original
independent allowances and otherwise retains the original LP. The returned message
identifies the dual row-combination certificate's inconclusive outcome. No phase
event trace or exact historical x64 backend path is claimed.

No production scans, solves, allocations or retained-memory change. Diagnostics
perform30 original solves once and one small post-solve certificate per case;
records retain O(30(n+m+nnz)) exact selected values. This is bounded evidence,
not a runtime benchmark or a full S6/CI pass. CI remains disabled.

Next separate S6-L plan qualifies a strictly contradictory fixture with a robust
margin, retaining INFEASIBLE and supplied-tolerance values rather than relaxing the
status assertion. The existing separate options tests retain precision/value
coverage. Qualification must precede any permanent fixture edit.

The proposed robust-margin replacement cannot detect rounding t to g. Existing
stored-option tests do not prove end-to-end last-bit status sensitivity; that
broader precision obligation remains open beyond this fixture repair.
