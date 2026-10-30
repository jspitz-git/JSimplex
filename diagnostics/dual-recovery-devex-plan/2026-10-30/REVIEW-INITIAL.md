# Independent dual-recovery Devex design/plan review

Not accepted pending R1. Scope is plan preparation only; no Julia, candidate edit, test execution, or numerical admission occurred.

## R1 — explicit failed-row norm gate (P2)

Task2 line61 permits a finite-unreliable row with an eligible cause and finite retained direction, while line60 and spec line15 forbid zero/overflow norms from becoming fallback-ready. Current `src/simplex_recovery.jl:145` returns immediately on unreliable refinement, before the dot/check at146–147. Thus a literal implementation can accept a zero direction (finite-unreliable unchanged quality with zero correction) or finite huge direction with overflowed squared norm. The work ledger line101/spec line29 only names a finite-direction scan.

Require one `dot(direction,direction)` and the original finite/positive guard on otherwise eligible unreliable rows before fallback readiness, preserve reliable arithmetic/order, avoid duplicate norm calculation, and charge the added O(m) reduction in both ledgers. Explicit zero/overflow finite-unreliable controls should pin this boundary.

## Source findings and work/memory

- `recompute!` writes basic-cost dual prices to owned scratch.rho (`src/simplex.jl:473`); weight rebuild allocates separate local rhs/direction (`src/simplex_recovery.jl:138`) and refinement owns separate quality buffers (`src/simplex_pivot.jl:293`). The requested post-weight core check can reuse rho without a solve; deliberately mutating callbacks remain outside the rollback promise.
- `SimplexWorkspace.factorization::F` (`src/simplex.jl:194`) requires the cold test factory to return the live concrete F. The plan explicitly accommodates a genuine factor once plus a declared wrapper and no production overwrite.
- `_unreliable_pricing!` only changes owned scalar state; `reset_devex!` resets all weights/reference, and `_auto_framework_reset!` suppresses the reset observer while recovery_active (`src/simplex_pricing.jl:213–225`). The plan correctly avoids callback-emitting `_reject_auto_weight!` and `_switch_dual_pricing_to_devex!`.
- `_copy_pricing_state!`, `_copy_pricing_pool!`, the private recovery arrays and delayed `_publish_recovery!` support the proposed cancellation/ownership policy. Existing observers are prepublication and callback-free records can be added after adoption.
- Explicit algorithm forwarding from retry through repair and its restore fallback, plus retained unspecified strict wrappers, covers the precision-transfer and independent-driver exclusions.
- No unnecessary normal-path scans, solves or retained arrays are proposed. The norm reduction above is necessary to satisfy the stated numerical boundary and must be accounted for. Compilation/boxing/allocations and changed Devex trajectory remain unmeasured and are correctly deferred to concrete admission. No speedup or free-allocation claim is accepted.

Source pins: all20 hashes independently matched. HEAD/source decision and master baseline matched. Manual checks and bindings are recorded in the companion JSON. All source review conclusions remain conditional on future candidate implementation and runtime evidence.
