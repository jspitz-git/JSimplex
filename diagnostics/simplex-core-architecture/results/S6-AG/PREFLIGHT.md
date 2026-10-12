# S6-AG source provenance preflight

Base e123b17/master3c0af5c.517shared source/test/runtime/environment pins matchAF.
One new PFI control only; no AF driver reuse/execution. Native default NumericalPolicy
has pivot_validation/recovery/refinement/hypersparse false. Public dual_iteration!
(dual_simplex.jl:693) wraps stop and calls entry; entry:710 returns _dual_iteration!.
_core (simplex_pivot.jl:422) directly returns unchecked when native; no candidate/retry
on this exact-row no-entering path. Actual no pivot_rejected events required.

Unchecked assigns rho to pipeline destination scratch.rho (dual_simplex.jl:1148).
Native real exact unit solve gives row2; default Dantzig introduces no weight solve.
No-eligible branch:1234 recomputes once, recursively returns unchecked(true).
Last unit BTRAN overwrites that same scratch.rho; no eligible branch:1252 supplies
this rho and below to _infeasibility_certified. Floating dispatch:743 calls
_floating_infeasibility_certified(:777), which only reads rho/workspace. It has no
callback, factor or scratch writes. False produces unique saved terminal message.
That return propagates through recursive unchecked, core, measure, entry and public
return without changing rho. _measure_basis_iteration!(:365) changes only timing/
refactor-policy state in finally (or directly returns f()), never scratch.rho.
No diagnostics observer is installed, and stop returns false. Post-return capture
is therefore source-bound to this new call's final certificate input, not to AF's
uncaptured private rho or any historical CI run. No certificate helper called again.

Work prediction from source/AF: one ordinary refactor and its primalFTRAN/costBTRAN,
two unitBTRANs =>1FTRAN3BTRAN1refactor; setup separately recorded. No correction/reject/
pivot event or publication. No direct adapter/quality/component helper calls.
Offline audit reconstructs captured CSC and binary64 formula _add_product_bounds
without calling Julia. Compare exact B'rho=e2, ordered firstcolumn interval and
actual infinite upper bound. No automatic inferred acceptance of AF or test repair.
