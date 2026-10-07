# Historical numerical failures and guard overhead audit

Read-only investigation on 2026-10-07 while the medium cleanup validation runs.
No additional Julia process was launched and no solver, tolerance, factor,
pricing, or pinned reproduction script was changed. `evidence.json` records
report paths, hashes and extracted outcomes. This is a diagnosis and measurement
plan, not a tested numerical or performance repair.

## Provenance matters

The completed interval sweep used experimental solver `33e27d4` and harness
`b38d32b`. Current master is `50fdc02`; the running memory repair is `9c3ca17`.
They are not interchangeable baselines. In particular, the experimental branch
contains the direct-BG fresh-row validation / native candidate reselection
repair, while master contains the recent native terminal-certificate and
postsolve reconstruction repairs. The sweep did not contain those recent
certificate repairs. A shared error message does not prove a shared root cause.

## Remaining failure groups

| Group | Stored evidence | What is established | What remains unknown |
|---|---|---|---|
| Direct SS/native1600, runtime | Three identical failures: first phase II begins at 257; terminal certificate fails at 69853; original-LP retry phase II begins at 71124 and fails at 79013 | First failure is terminal phase-II certification before postsolve; the retry fails during phase II with bounded feasibility recovery exhausted | Which primal/dual/complementarity clause rejected the first certificate; whether the new witness correction repairs it |
| Original SS/native1600, runtime | Original-LP restart after 5713 iterations; all three runs ultimately certify at 98100 | A recovered numerical incident, not a failed final result | The precise initiating numerical defect needs a captured state |
| FT/SS fixed histories | 120 failed attempts = 40 configurations repeated three times; 156 failing probes: 102 unit BTRAN and 54 dense FTRAN, zero entering probes | Aged representations lose accuracy independently of phase transfer/postsolve; fresh reference LU remains accurate | First harmful update and contributions of factor growth, triangular solve rounding and transformation application |
| Greenbea, BG broad controls after the direct-BG repair | Original/default-direct/METIS-direct fail at 9336/8995/9031; all first reject terminal certification and later exhaust recovery | Shared across original and direct factors; both failures occur after phase II starts, not at phase I/II entry | Whether it shares medium's witness defect; reports have no terminal vectors to prove this |
| Pilotnov, PFI/Markowitz80 | Baseline and pruned search both fail at 663: small pivot dual price could not be certified | Failure precedes accepting a small pivot; pruning did not introduce it | Which internal rejection in the price stabilizer fired |

Do not confuse the last row with the *direct-BG/native pilotnov* regression,
which was already diagnosed and repaired in the experimental branch. That repair
has an independent native-row/candidate-reselection cause and combined ablations.
Pilot87's rejected historical objective comparison was a reference-data problem,
not another unresolved solver failure.

### Strongest factor-update hypothesis

On runtime-40000, all six FT/SS arms (original native/Markowitz and direct native)
with interval 1280 or 1600 first fail a sampled check at exchange 1120. Their
unit-BTRAN relative residuals are 1.70e-10 to 3.94e-10, while fresh LU gives
2.39e-17 on the same basis and RHS. The entering probe remains exact there;
checking only the newly installed column would miss the defect. Checkpoints are
80 exchanges apart, so 1120 is not necessarily the first inaccurate update.
Direct SS also fails the fast0507 tape at exchange 640 with interval 320 (chain
age 320), so this is not exclusively a thousand-update phenomenon.

Original and direct FT/SS share `_eliminate_triangular_row_spike!` in
`src/triangular_factorization.jl`. It divides the moved-row entry by the current
upper diagonal without a magnitude-based interchange. `_prepare_spike!` checks
the simplex pivot, not every subsequent elimination multiplier. BG instead
compares the two local entries and swaps before dividing, bounding each finite
local multiplier's magnitude by approximately one. Long unpivoted elimination
chains and amplification are therefore a specific hypothesis worth testing,
not proof of an indexing bug or evidence that all errors are accumulated in U.
No small nonzeros are dropped by this elimination (only exact zeros).

First reproduce the shortest failure (direct SS, fast0507, interval320), inspect
every exchange from 561 through640, and record maximum multiplier, upper-value
growth, diagonal scales and FTRAN/BTRAN residuals. Check factor reconstruction
and solve application separately. Repeat the same failing basis with fresh LU,
BG and a single native residual correction. Preserve the scheduled replay: an
extra refactorization cannot be counted as success on the original tape.

## Guard overhead: concrete opportunities

### 1. Repeated primal certification work (highest confidence)

`_finish_legacy_primal_point!` tests reconstruction, then calls
`_restore_legacy_primal_point!`, which tests the unchanged reconstruction again.
The latter must remain safe for other callers, but an internal already-checked
path can avoid this duplicate. Short-circuiting means a failed bound check does
not always perform the expensive equation scan twice; measure both outcomes.

`_legacy_primal_point_certified` then calls model feasibility and row consistency
separately. Both compute `_primal_row_bounds(A, primal)` for the same stored
point; they use different bounds and must both remain certified. They also copy
the structural primal vector, allocate activity intervals, and can independently
invoke the selected-row fallback. Reusing a single activity enclosure and native
compensated evaluation for both bound sets is a promising arithmetic-preserving
change. Cache validity must end whenever primal values, model or active bounds
change; reuse only inside one certification call first.

This path is demonstrably frequent: the completed medium **primal handoff
cleanup** reports 18422 pivots and 18422 `primal_point_preserved` events, with
OPTIMAL and original primal feasibility. This is not a fresh full solve timing.
The running memory repair already removes most arbitrary-precision allocation
from this path, but does not remove the repeated matrix traversals above.

### 2. Dual small-pivot rescue still converts whole matrices

`_stabilize_small_dual_pivot!` runs for Float64 pivots of magnitude at most 1e-6.
It constructs B and a fresh native LU, then calls `_refined_dual_prices` at
256 and512 bits. Each call converts all of A.nzval to BigFloat; the inner basis
refinement additionally converts B.nzval and can use up to32 corrections.
This is active independently of the adaptive precision-boosting option.
It is bounded per invocation but can recur at many different small pivots.

The gate alone does not first try a native compensated price certificate.
A native-first test preserving the small-pivot amplified-error requirement is
therefore a concrete candidate. Do not replace it by ordinary price sign or a
relative residual: division by a small pivot amplifies sub-tolerance price error.
The existing fallback also validates *all* nonfixed nonbasic price signs;
checking only the entering price would change its contract.

Other exceptional paths (`_try_refine_dual_prices!`, direction and full-pivot
refinement) also construct fresh LU and converted arrays. Reuse within one
unchanged recovery transaction could remove repeated setup. Cross-iteration
reuse requires explicit basis/cost invalidation. None is changed in this audit.
Pilotnov/Markowitz663 is the most compact stored failure for instrumenting each
stabilizer rejection reason before proposing an alteration.

### 3. Ordinary residual guards traverse the basis every iteration

Dual FTRAN direction validation scans current basis columns, and updated-factor
BTRAN validation scans them again. These are O(nnz(B)) safeguards, distinct from
terminal certification. Full tableau pricing already traverses A before the
BTRAN check; a failed/corrected row may cause pricing again. Moving row validation
before pricing could avoid discarded work on the rare failure path.

The BTRAN residual starts its selected dot product at -1 while pricing starts
at zero. Simply reusing `tableau_row[basic] - 1` changes floating accumulation;
it is not an arithmetic-preserving substitution. Shared traversal or workspace
reuse needs paired residual/decision checks. FTRAN and BTRAN checks are not
mutual substitutes: replay evidence above specifically shows BTRAN failures
with a perfect entering-column solve. Do not switch these guards off to claim
a speed improvement.

### 4. Terminal witness repair is not an ordinary pivot cost

The recently added `native_certificate_recovery.jl` repair runs only after a
failed final certificate and performs one native correction and independent
recertification. In contrast, primal point preservation can run at every pivot.
Optimize the frequently exercised paths first rather than assuming all routines
named "certificate" have the same frequency.

## What timing evidence does and does not support

The interval sweep reports whole-call time, compilation, GC, allocations and
refactorization counts, but no separate guard timers or stabilizer invocation
counts. It cannot establish the percentage of time spent in checks. Historical
sampling profiles show `_refined_dual_prices` on real runtime paths, but their
solver revisions and trajectories differ; flat inclusive stack counts cannot
be summed into a current overhead percentage. In the three failed direct-SS
runtime runs GC is only1.38--1.52% of call time: GC alone does not explain them.
BigFloat arithmetic cost is not included solely in GC time.

Fixed-history kernel measurements deliberately exclude independent validation.
For example HH/native runtime-30000 costs2.463s at160 versus10.635s at1600,
while BG/native costs9.124s versus49.542s. Thus the long-interval slowdown has a
factor-operation component even without simplex checks; it cannot all be blamed
on corrective mechanisms. These kernel totals are not a full-solve operation mix.

## Sequential follow-up after existing validation

1. Finish the current memory repair verification first; keep one Julia process.
2. Capture greenbea terminal clauses on the current master repairs and compare
   with the experimental dual kernel explicitly. Use a fresh isolated diagnostic
   state; do not silently combine the two branches.
3. Instrument pilotnov/Markowitz663's stabilizer branches and FT/SS's shortest
   failing tape as described above; only then choose numerical repairs.
4. Profile guard frequency, exclusive time and allocations separately for
   normal pivots, recovery, certification and cleanup. Use unchanged guard-on
   production as baseline, not disabled safety checks.
5. First optimize duplicate primal activity calculations and scratch allocation.
   Require identical ordered decisions, final certificates and all relevant
   cancellation/FTZ regressions. Measure native-first dual rescue separately
   because it can change numerical decisions even at unchanged tolerances.

No new speedup, fix of the listed failures, or full medium validation is claimed
by this static audit. Raw failed results remain untouched.
