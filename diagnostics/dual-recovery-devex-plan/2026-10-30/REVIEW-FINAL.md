# Independent final dual-recovery Devex design/plan review

Accepted for plan preparation. No open material findings. This acceptance authorizes no implementation, Julia execution, numerical launch, production promotion or runtime claim.

## Findings resolved

R1: Task2 now requires the original `dot(direction,direction)` finite-positive guard on an otherwise eligible finite-inconclusive row. This rejects zero/underflow, overflow and nonfinite direction components under the unchanged real Float32/64 IEEE/no-fastmath semantics. Reliable rows retain their original single dot and order. Both ledgers charge the new failure-only O(m) reduction and exclude the redundant standalone finite-direction scan. The earlier finding and exact original documents remain preserved.

R2: Separate weight and refinement causes distinguish an invalid norm from an actual refinement terminal cause. Metadata-only `not_observed` now explicitly covers a legacy refinement that ran without detailed cause collection as well as a skipped refinement. It makes no false work claim and does not force outcome construction on strict legacy paths. The exact norm-fixed intermediate documents and review remain preserved.

## Source and plan assessment

- `recompute!` stores basic-cost dual prices in owned scratch.rho (`src/simplex.jl:473`). The weight loop uses independent local rhs/direction (`src/simplex_recovery.jl:138`), and refinement uses separate owned buffers (`src/simplex_pivot.jl:293`). The planned post-weight core revalidation can reuse rho without a solve or factorization. Existing correction callbacks can invalidate core values, so the new revalidation remains necessary.
- The explicit actual algorithm from retry, forwarded through repair and its restore fallback, and unspecified strict wrappers fit the source call chain. Independent driver repair and `simplex_precision.jl:218` remain strict. Nonfloat and mismatched pricing-state gates are explicit.
- `factorization::F` (`src/simplex.jl:194`) requires the private factory seam to return the live concrete type. One genuine factor wrapped by a declared test type is coherent; no production overwrite or backend substitution is needed.
- Complete Devex reset, `_unreliable_pricing!`, owned pricing-state/pool copies and `recovery_active` reset suppression (`src/simplex_pricing.jl:224`) support private preparation with no new callbacks. The plan correctly excludes callback-emitting switch/reject helpers.
- Existing recovery observers run before adoption; the proposed marked cold result exposes pending mode to those observers and records the two pricing events callback-free after adoption. Stops/throws retain live solver-owned state and original wrapping/identity while consumed work and original diagnostics remain consumed. Arbitrary user mutation of live memory remains outside the rollback promise.
- Tests cover branch provenance, partial DSE prefixes, mode gates, stop/throw publication, retained strict consumers, actual Devex pivot and original certificates. Factor-output controls are explicitly test instrumentation, not native-backend numerical evidence.

## Computational work and memory

No unnecessary work or retained memory is proposed. Required fallback-only work consists of one self-dot reduction, full finite/core validation with existing RHS/gather/quality scratch costs, full Devex reset and pool retirement. Zero new factorization or basis solve is permitted there. Default refinement retains one common numeric body, no extra array pass/solve/sink/persistent field, and no constructed outcome in false result mode. Cold metadata is fixed-size and must die with publication/discard; boxing must be disclosed.

Actual compiler boxing, warmed allocations/timings and later Devex trajectory remain unmeasured. The planned separate normal-path/reference/fallback measurements and original numerical safeguards are appropriate. No speedup follows from avoided weight rows alone.

All20 source pins match independently; all71 tracked production source files equal master. Initial and intermediate document bytes were independently matched to preserved snapshots. The companion JSON records the final checks and exact current/preserved bindings. Only Python/static source checks ran.
