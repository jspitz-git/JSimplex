# Direct LU policy adapter design decision

SOURCE/DESIGN ONLY; no Julia, candidate, driver, launcher, runtime probe or actual
production/test/environment/CI change. Current master26e2291 is published and has
accepted6,956 actual-master checks. The diagnostic checkoutcb75732 deliberately
retains its older src; the proposed overlay must use actual master, not that checkout.

All three direct prototypes (FT, SS, BG) already share `_export_basis_lu` and the
same DirectLowerBackend. Historical corrected GREEN19,557 covered Markowitz and
native lifecycles. The frozen wrapper lacks pivot_policy; its constructor uses the
two-argument `_factorize_basis`, its generic path calls the two-argument Factor,
and refactor rebuilds from backend/normalize only. On current master these routes
would silently choose default. This is a source-derived integration gap, not a new
runtime defect report or invalidation of the earlier tests.

The chosen adapter adds constant immutable enum intent, passes it before extraction,
keeps it in copies/refactors/empty/fallback paths and rejects nondefault Markowitz
before work. No factor-export rewrite, separate adapter per manager, new public
option or dynamic sparse storage. A test-only construction keyword delegates to
the real factory by default and allows a throwing counter to prove early rejection;
it is never retained or used in solve/update paths. Markowitz reuses the existing
sparse/core permutation extraction, not native control semantics.

Work ledger: per constructor/refactor one existing ordinary factorization, one
export, existing validation/normalization/packed construction; native orientation
may add a solve, Markowitz has no orientation solve. Markowitz extraction scans
its dense core twice and creates triplets/CSC. These are existing nonzero costs.
The adapter adds constant enum handling and the existing selected native policy's
private20-control setup, not another factorization. Copies retain enum and existing
scratch ownership. No new per-FTRAN/BTRAN/update scan, solve, vector copy or cached
owner. Whole direct-manager rebuilding and ordinary spare reuse differ and must
remain inside measured windows. Successful direct export releases ordinary backend
references; no claim of native free/GC follows from source reachability.

The new comparison uses matched native threshold_one or matched Markowitz default.
It preserves original input tokens and residual/selection rules but has new phase
names, source, admissions and raw paths. Native default remains an explicit
compatibility/correctness arm. Original cost1 failure and cost2 block remain intact;
no old schedule is resumed or relabelled. Equal policy does not restore native
combined-solve refinement or prove common numerical trajectories. Strategy remains
native-selected and is recorded, never assumed to be unsymmetric.

Spec and task plan are the deliverables. Next is offline candidate/tests plus
independent review, then separate concrete RED/GREEN admission. No benchmark is
required or performed for these documents. Four previous actual-master closure/
publication current continuation hashes map only to this step's before copies.
All other historical bindings remain unchanged.
