# `runtime.mps`: first failing basis at iteration 23,202

The Windows audit in commit `650d2ee` used Julia 1.13.0 with one Julia
thread and six BLAS threads. It checked a fresh sparse LU after each pivot
from 23,156 onward. The LU first failed after pivot 23,202; the basis at
23,201 still factorized. That pivot replaced slack 57,247 in basis row
25,632 with slack 57,784. The updated Suhl–Suhl factorization reported
a tableau pivot of `-6.761199819713067e-7`, a zero dual step, and a
primal step of `1.9581594892750013e9`.

I reconstructed the two basis matrices from the audit CSV, the same MPS
file (SHA-256 `d0ac16e1a52a7d3411cbac28616bba9d3beb0c0edbdb2d72ab0477ce075f6c68`),
presolve, and scaling. For the old basis and the entering slack column:

| Solve | Tableau element in row 25,632 | Residual infinity norm |
| --- | ---: | ---: |
| Fresh Float64 LU | `7.024451075124088e-48` | `7.09e-17` |
| Fresh Float64 QR, rank 28,453 at tolerance `1e-12` | `-4.839765663383502e-25` | `2.16e-16` |
| Float64 LU with 512-bit residual refinement | `-3.38e-111` | `1.38e-103` |

The refined result is consistent with a zero tableau element; it is not
an exact-arithmetic proof. The new basis has a smallest Float64 LU `U`
diagonal of `1.07e-18`; sparse QR estimates rank 28,452 at tolerance
`1e-12`. On Windows fresh LU reports a singular matrix. On this Linux
machine it completes, but the resulting basis is severely ill-conditioned.

I also replayed the 45 logged basis replacements after the preceding
refactorization, starting from the reconstructed basis at iteration
23,156. With the same Suhl–Suhl update implementation on aarch64, the
updated factors report `4.76e-7` for that next tableau element and the
direction has residual infinity norm `2.63e-3` against the old basis.
Thus the wrong nonzero pivot is reproducible without the Windows LU
failure. The exact sign depends on the floating-point path.

This evidence points to error accumulated in the updated factorization
as the immediate cause of the invalid pivot. Near-zero dual steps show
degeneracy in the same region, but perturbing the costs would only
change which pivots are tried.

## Refactorization before the pivot

The Windows counterfactual in commit `f17464a` rebuilt the same basis
at iteration 23,201 before choosing the next pivot. Immediately before
the rebuild, the updated direction had pivot `-6.761199819713067e-7`
and residual infinity norm `0.003909944934112411`; a fresh LU direction
had pivot `-0.0` and residual `1.7869969230581004e-17`. The rebuild
kept dual infeasibility at zero. The next pivot still used row 25,632,
but entered column 8,590 with tableau pivot `-62.27918240194156`.
The resulting basis passed fresh LU.

The production guard therefore checks the basis equation `Bd = a`
before accepting a pivot no more than ten times the dual ratio test's
coefficient cutoff. If its residual is too large relative to the row
terms and pivot size, the solver rebuilds the basis and repeats that
iteration once. A second failed check returns `NUMERICAL_ERROR`. This
guards the observed false pivot without forcing early refactorizations
for full-sized pivots whose residuals are tiny relative to their size.
The guard rejects the replayed false direction (`4.76e-7` pivot,
`2.63e-3` residual) on this machine. A local run with the guard still
reached 23,201 iterations in 84.5 seconds, matching the prior trace
and elapsed time to that point.

## Guarded Windows audit

Commit `7b798dd` contains the audit with the guard enabled. The run used
one Julia thread and six BLAS threads as before. At iteration 23,202,
the refactorization count rose from 464 to 465; basis row 25,632
replaced slack 57,247 with structural column 8,590. Fresh LU succeeded.
Fresh LU also succeeded for each subsequent basis through iteration
23,205, including the basis after entering column 3,639 at iteration
23,205. The audit ended at its requested iteration limit in 164.7
seconds, with no failed basis in that window. It did not run the LP to
optimality. The next audit extends the check through iteration 23,255.
On aarch64, that extended script completed all 100 basis checks from
23,156 through 23,255 with fresh LU success in 84.6 seconds; the local
pivot sequence differs from the Windows sequence.

Commit `7918dd5` contains the extended Windows audit. Fresh LU succeeded
for all 100 checked bases through iteration 23,255, including the
scheduled refactorization at iteration 23,252. It stopped at the audit
cap after 157.7 seconds with no failed basis; this is not an LP
termination result. The next check uses
`diagnostics/runtime_reduced_continuation.jl` to continue the reduced LP
to 30,000 pivots or a 600-second deadline without per-pivot fresh LU.
On aarch64, that script reached the 30,000-pivot cap in 115.3 seconds
with 600 refactorizations, zero dual infeasibility, and primal
infeasibility `6.933145208769426e7` across 4,883 basic variables.
The `TIME_LIMIT` status at the cap was requested by the diagnostic
callback and is not an LP classification.

## Reduced LP continuation on Windows

Commit `81eefd8` contains the Windows continuation log. The guarded solver
passed the former bad basis at iteration 23,202 and reached iteration
23,778, but then returned `NUMERICAL_ERROR: dual feasibility lost`.
The final stored reduced costs had one dual violation of
`0.8277722799969447`; the workspace had made 477 refactorizations.
The log does not say whether that price is a Float64 error, whether
iterative refinement failed, or whether the freshly rebuilt basis is
truly dual infeasible. The reduced LP was not solved.

The continuation script now traces each pivot from iteration 23,750
through 23,825 and, if this error occurs, saves the basis and variable
state to `diagnostics/runtime_reduced_failure_state.tsv`. It then builds
the basis independently, checks fresh sparse LU, refines `Bᵀy = c_B`
in 256 and 512 bits, compares the resulting prices with the stored
Float64 prices, and reports whether the production price guard accepts
them. These measurements are diagnostic only and do not change the
production solver.

On local aarch64 Linux, the script reached the requested iteration
23,800 with zero dual infeasibility in 86.5 seconds. At iteration
23,778 it had 476 refactorizations and 21 pending updates; the Windows
failure had already performed a 477th refactorization. The pivot
sequences therefore differ, so the Windows basis must be audited on
that machine. The local run verifies the trace but does not reproduce
the Windows failure.

## Audit of the saved Windows failure state

Commit `ba4c59d` contains the failure snapshot but no trace log. The
snapshot can be checked without rerunning the simplex by executing
`julia --project=. diagnostics/runtime_snapshot_audit.jl` from this
worktree. On aarch64 Linux, reconstruction of the scaled reduced model
reproduces the saved primal infeasibility
`(1.7477607549564644e10, 4966)` and dual infeasibility
`(0.8277722799969447, 1)`. The sole nonfixed dual violation is
structural variable 24,212 at its lower bound. Many other stored prices
have the opposite sign but belong to fixed variables and are correctly
excluded from the solver's dual feasibility check.

Fresh sparse LU of the saved basis succeeds. Independent refinement of
`Bᵀy = c_B` converges after four corrections in 256 bits and eleven in
512 bits. Both calculations give the reduced cost of variable 24,212
as approximately `-0.8062975028414638`, far outside the `1e-7` dual
tolerance. The maximum difference between the two complete price
vectors is below `7.4e-30`. The saved Float64 price `-0.8277722799969447`
has a noticeable magnitude error, but its negative sign is correct.
The production refinement guard therefore correctly rejects this
saved bound state. The new trace below shows that this state was
transient; it does not show that the last completed pivot was invalid.

Commit `a4b97b9` adds the Windows trace and the complete audit output.
The last completed pivot, at iteration 23,778, replaced slack 46,097
with structural column 26,904 in basis row 14,482. The trace still
reported zero stored dual infeasibility after the pivot, with 27 pending
basis updates. The Windows 512-bit audit independently confirms the
price `-0.8062975028414638` in the saved basis.

`diagnostics/runtime_last_pivot_audit.jl` reverses that final basis
replacement and recomputes the preceding basis using the saved working
costs. It obtains a price of `-2.6156077463` for variable 24,212,
`0.6276039051` for entering column 26,904, tableau coefficients
`25.6150139915` and `-8.8851996877` respectively, and a dual step
of `-0.0706347552`. These values predict the final refined price
`-0.8062975028`. Variable 24,212 has bounds `[0, 4.1]`; its negative
price is feasible when it stands at the upper bound. Under the saved
costs, its breakpoint at the last completed pivot was `0.1021122904`,
later than the entering variable's breakpoint `0.0706347552`.

## Transient bound flip and fix

Commit `d4d24ea` records the missing state. At iteration 23,778,
variable 24,212 was **still at its upper bound** (`4.1`), with stored
price `-0.8196478569`, working cost zero, and zero dual infeasibility.
The solver then attempted another iteration. The final log has the
same iteration count and basis, but one more refactorization and the
variable at its lower bound (`0.0`) with price `-0.82777228`.

`_dual_iteration!` applied all proposed bound flips before checking the
entering direction. A small or inaccurate pivot can cause a fresh
factorization and a retry. In that path, the factorization was rebuilt
*after* the flip and the solver tested dual feasibility before the
compensating pivot had occurred. A flipped boxed variable can be
temporarily dual infeasible in this interval. The resulting
`dual feasibility lost` was therefore caused by checking this partial
iteration, not by a completed pivot. `recompute!` does not change bound
states, and the iteration counter did not advance; this matches the
observed state change in the Windows log.

The fix validates the entering direction before applying proposed
bound flips. The flip solve uses a separate scratch vector to preserve
the already validated entering direction. A one-row, two-column
regression reproduces the old failure: before the fix, it returned
`NUMERICAL_ERROR` after a flip and refresh without completing a pivot;
after the fix, it refactorizes and completes the pivot. The full test
suite passes 13,613/13,613 tests. A local aarch64 continuation of the
reduced `runtime.mps` reached the diagnostic cap of 30,000 iterations
with zero dual infeasibility in 116.6 seconds; it did not solve the LP.
The Windows path still needs a continuation run with this fix.

## Harmful cost shift at iteration 26,421

Commit `be27e3c` contains the next Windows continuation and its saved
failure state. With the bound-flip fix, the solver passed iteration
23,778, then stopped at iteration 26,421 with `dual feasibility lost`.
The basis had just been refactorized (530 refactorizations, no pending
updates). The only dual violation was structural variable 16,884 at
its upper bound, with stored reduced cost `4.0277399193655583e-7`.
Independent 256-bit and 512-bit calculations agree on a positive price
of about `4.0277400195329477e-7`, so this is a real violation under
the *working* costs rather than an inaccurate Float64 price.

The saved working cost of that nonbasic variable is
`4.027740303750042e-7`, while its original scaled cost is zero. The
solver had perturbed costs. Restoring this one cost changes its reduced
price to approximately `-2.84e-14`, within the `1e-7` dual tolerance;
all other prices remain feasible. Replaying the saved Windows state
locally confirms that the dual infeasibility falls from
`(4.0277399193655583e-7, 1)` to `(0.0, 0)`.
`diagnostics/runtime_snapshot_audit.jl` now reconstructs the
perturbation flag from the saved working costs and reports
`PRODUCTION_REFINE_ACCEPTED=true` on this state.

The dual-price refinement path now releases an offending nonbasic cost
shift only when the workspace is perturbed, the original cost differs,
and independently refined prices at 256 and 512 bits both become
feasible with a margin after release. If any price still violates the
tolerance, the path leaves working costs and prices unchanged. A
synthetic regressions exercise upper and lower bounds, rejection when
there was no perturbation or the original cost remains infeasible,
and simultaneous shifts in a basis with a nonzero dual multiplier.
The full suite at the time of the fix passed 13,622/13,622 tests. A
Windows continuation with this change is still needed
to see whether the reduced LP advances beyond iteration 26,421.

## Next Windows loss at iteration 29,720

Commit `2626ade` shows that the cost-release guard passed the former
26,421 failure. The run then stopped at 29,720 with two stored Float64
dual violations totaling `1.8132712296049078`; the basis had 597
refactorizations and no pending updates. An independent 512-bit solve
of the saved basis agrees with the 256-bit solve but identifies three
*different* nonbasic variables at their lower bounds, with prices
approximately `-1.98697`, `-1.50116`, and `-3.01881`. Thus the fresh
Float64 LU prices are inaccurate and the saved basis is also genuinely
dual infeasible under its current working costs.

Those three variables have working costs essentially equal to their
original costs. Restoring all original costs on this basis creates
thousands of dual violations, so the previous cost-release rule does
not apply. The available final-state snapshot cannot identify which
preceding pivot or intermediate refactorization first lost dual
feasibility. The solver correctly rejects this state instead of
accepting inaccurate Float64 prices.

The continuation diagnostic can now save the last two distinct
iterations whose *stored* prices are feasible, using
`RUNTIME_CAPTURE_START` and `RUNTIME_CAPTURE_END`. Alternating files
`runtime_reduced_capture_a.tsv` and `runtime_reduced_capture_b.tsv`
preserve their bases, states, costs, and prices for an independent
before-and-after audit. This is diagnostic instrumentation only.

Commit `bb00de8` repeats the same 29,720 failure with the same prices
and basis counters. Its log still traces the old 23,750–23,825 window
and contains no `STORED_FEASIBLE_SNAPSHOT` record; the commit also has
no capture files. The capture environment settings were therefore not
active for that run. The diagnostic script now defaults to tracing and
capturing iterations 29,690–29,730 and prints `DIAGNOSTIC_CONFIG` at
startup. A plain invocation after updating the branch will produce the
two rolling capture files if it follows the same path.
