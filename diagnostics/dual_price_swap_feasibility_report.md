# Dual price repair: buffer-swap feasibility

This is an investigation, not a production change. A throwaway process-local
prototype replaced the whole-vector backup and copying in
`_try_refine_dual_prices!` and `_try_refine_dual_pivot!` with assignments to
`workspace.reduced_costs`. The already computed Float64 replacement becomes the
candidate; rejection reinstalls the original vector reference. No persistent
second buffer or new workspace field is needed.

## Ownership and failure behavior

Repository call sites read reduced costs through the workspace after these
repairs. The dual iteration retains aliases to rho, tableau and direction
scratch, which the prototype continues to update in place, but does not retain
an alias to reduced costs. The ratio test and feasibility check also read the
current workspace field. Result construction copies reduced costs. No internal
dependency on stable price-vector identity was found in this audit.

On acceptance, the prototype leaves a previously borrowed reference pointing to
the old prices. Such internal references must be reacquired from the workspace.
On rejection, pivot repair's existing `finally` reinstates the original reference,
including when a stop callback returns true or throws after candidate installation.
Callbacks reading the current workspace see candidate values as before; a callback
that instead captured the old vector would observe a change in alias behavior.

Price-only repair also restores selected working costs when it rejects the
candidate; that indexed backup remains necessary. Its log callback runs after
acceptance, and a logging exception currently leaves accepted prices installed.
The prototype preserves this behavior. It does not add broader transaction or
concurrency guarantees.

## Measurements

Julia 1.13.0 on aarch64, three samples after two warmups, fresh workspace setup
outside measurement, logging disabled. All measured compilation times are zero.
Diagonal problems force accepted price repair (release a harmful cost shift) or
accepted complete pivot repair. They measure one repair, not a complete solve.
The price count includes structural columns and slacks.

| Repair | Price count | Allocations before → prototype | Bytes before → prototype |
| --- | ---: | ---: | ---: |
| prices | 4 | 397 → 395 | 20,896 → 20,800 |
| pivot | 4 | 744 → 742 | 40,864 → 40,768 |
| prices | 128 | 6,039 → 6,037 | 390,752 → 389,616 |
| pivot | 128 | 14,260 → 14,258 | 914,224 → 913,088 |
| prices | 1,024 | 46,838 → 46,835 | 3,047,416 → 3,039,184 |
| pivot | 1,024 | 111,990 → 111,987 | 7,208,864 → 7,200,632 |

Swapping eliminates one vector copy allocation (two or three Julia allocation
events depending on size) and the copy into the live vector, plus copying back on
rejection. At 1,024 prices it saves 8,232 bytes: approximately 0.27% of price-only
repair byte traffic or 0.11% of complete pivot repair. Most of these paths' work
remains in fresh LU and independent 256/512-bit refinement calculations. These
measurements do not establish a runtime speedup or profile every remaining site.

A separate instrumented census counted entry into both repair functions over
16 dual solves: afiro/adlittle, all four basis update methods, refactorization
intervals 1/20, presolve disabled and scaling off. All solves reached OPTIMAL;
neither function was called in any run. This is evidence for low priority on
these fixtures, not a frequency estimate for ill-conditioned large models.

## Validation and recommendation

The throwaway prototype passed 144 targeted assertions across all four update
methods and dimensions 2/64. These check accepted price/cost repair, accepted
pivots, rejection after candidate installation, stop requests, thrown callbacks,
and restoration of original vector identity and contents. The unchanged baseline
passed its 120 applicable assertions; the additional prototype assertions check
that accepted repairs leave the old borrowed vector untouched.

The existing dual simplex test file also passed all 1,638 assertions with the
prototype installed in that process (1m38.9s). The complete production suite was
not rerun because production source is unchanged. `git diff --check` passes.

The swap is feasible and small, but is not a significant allocation target on the
measured workloads. Keep it below recurring refactorization and pivot costs in
priority. If applied later, retain the existing pivot `try/finally`, leave the
partial working-cost backup intact, and test callback behavior and borrowed-vector
identity explicitly. Do not generalize this to swapping rho or direction scratch
without handling the aliases held by the dual iteration.

## Reproduction

These probes override functions only in their own Julia process. They do not
change `src/dual_simplex.jl`.

```sh
julia --startup-file=no --compiled-modules=existing --project=dev diagnostics/dual_price_swap_feasibility_probe.jl before
julia --startup-file=no --compiled-modules=existing --project=dev diagnostics/dual_price_swap_feasibility_probe.jl swap
julia --startup-file=no --compiled-modules=existing --project=dev diagnostics/dual_price_repair_census.jl
```

Raw results: [baseline](dual-price-swap-before.toml),
[prototype](dual-price-swap-swap.toml), [call census](dual-price-repair-census.toml).
