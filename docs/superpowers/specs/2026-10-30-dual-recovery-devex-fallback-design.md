# Explicit Devex fallback after an inconclusive recovery weight

User-approved scope: prepare a concrete plan for the source-assessed Devex alternative. This document specifies that plan; it admits no implementation or numerical launch.

## Goal and chosen approach

A private recovery trial whose basis, primal values and basic-cost dual prices are valid may finish using Devex when a finite steepest-edge weight solve is numerically inconclusive. It must never publish an unreliable steepest-edge norm or hide cancellation, exceptions or nonfinite work. The first scope is Float32/Float64 recovery reached from an actual dual transactional retry.

We considered weakening the componentwise weight check, further amplitude-based cleanup, and declining steepest-edge in favor of existing Devex. The source assessment rejected the first two as unsupported or experimentally insufficient. The selected approach retains strict checks and changes pricing mode explicitly. Different later pivots and runtime are expected possibilities; this is not a successful steepest-edge qualification or a promised speedup.

## Scope and architecture

1. Add opt-in call-local refinement outcome metadata, including terminal cause and whether any nonfinite correction/trial/quality proposal was observed at the refinement-kernel level. Existing internally recovered residual-evaluation range fallbacks retain their own unchanged quality contract; this flag does not reinterpret their private intermediates. Keep SolveQuality, its tolerances, arithmetic, cleanup policy and existing public return type unchanged. One common numeric body specializes on a compile-time result mode; the default returns only SolveQuality and must add no array pass/solve/scratch or retained state.
2. Thread an explicit actual algorithm from `_retry_simplex_step!` through repair and its checkpoint-restore fallback. Default/unknown/primal callers stay strict. Do not enable the fallback for the shared precision-transfer consumer, independent feasibility-driver repair, direct legacy restore/repair calls, multiprecision/exact types or ordinary refactorization. Do not infer the route from options or pricing history.
3. Only finite, unchanged/not-improving/limit-exhausted weight attempts with no nonfinite provenance can propose Devex. A stop, exception, invalid value/basis, invalid norm or unknown status cannot. Before marking an inconclusive row eligible, compute the original self-dot and require a finite positive squared norm; a finite vector alone does not exclude zero/underflow or norm overflow. For these real Float32/64 vectors this guard also rejects nonfinite components under unchanged IEEE/no-fastmath semantics, avoiding a redundant separate finite-direction pass. Revalidate core basis/primal/basic-price state after the failed attempt before considering the new mode; existing refinement callbacks can have run.
4. Reset the entire owned Devex framework, discarding any partial DSE prefix. Reuse existing scalar transitions, arrays and pool invalidation. Do not add mode fields to SimplexWorkspace/SimplexScratch or persistent per-row metadata.
5. Carry the pending fallback as a fixed-size cold result next to the private trial. Existing recovery observers retain their order and receive a workspace whose new mode is visible. No new observer or logger calls are introduced. On commit only, record existing pricing_weight_rejected and pricing_devex events without invoking observers; then retain the existing recovery records. Stop/throw before publication leaves live solver-owned values/mode/reference/factor unchanged; consumed work and existing diagnostics are not rolled back. Arbitrary user callbacks that themselves mutate live memory are not promised rollback or neutrality.

## Invariants and acceptance

Keep all solve/pivot/primal/dual/certificate tolerances and numerical policies, basis checks, selected-row and direction residual checks, pivot agreement, ratio-test cutoff, infeasibility proof and original-model certification. The old homogeneous-cleanup failure and prior complete-weight failures remain frozen and rejected.

A successful DSE rebuild stays DSE. A successful new fallback produces finite all-one initial Devex weights and the new basis reference, the correct fixed/auto/temporary mode state, invalidated candidate pool, and no published partial DSE values. Stale/mismatched pricing algorithm state is ineligible. Nothing is accepted from a final finite quality alone: the refinement outcome must preserve hidden nonfinite correction/trial/cleanup information.

The plan must test reason provenance, every mode gate, a failure after a valid prefix, stop and original exception identity, failed final publication, callbacks during refinement that invalidate core values, normal DSE success, unchanged precision/primal/default routes, an actual Devex pivot and independent original certificates. Standard Test only; fixed counters for declared test factor outputs are allowed, no custom test recorder/manual Test stack or production method overwrite.

## Work and memory

For m rows and N=m+n variables, original rebuild attempts k initial BTRANs, up to k*policy.max_refinements corrections, per-row validation/assembly O(N+m+nnzB), residual checks and dot norms. A fallback retains all consumed work and can avoid the remaining m-k weight rows. It adds, once at fallback, one self-dot reduction with its finite-positive scalar guard, full core revalidation (including primal RHS construction O(N+nnzA), basis validation/assembly and two original quality checks), an O(N+m) Devex reset and pool retirement. There is no new factorization or basis solve in that revalidation. Existing checks may allocate bounded O(N+m+nnzB) scratch; exact allocations must be measured, not called free.

Outcome metadata is call-local and fixed-size; default result-mode specialization must not construct it. Cold trial-result metadata and any compiler boxing must be disclosed. No inverse estimate, error array, graph cache, new retained vectors, additional retry/precision budget or hidden solve is permitted. Later Devex trajectory cost is unknown. Tests and short measurements must distinguish unchanged normal-path cost, failure handling and full public trajectories.

## Delivery boundary

Current deliverables are this design, an implementation plan and independent review only, with no Julia. Next preparation is an isolated candidate and ordinary tests, source-reviewed before concrete guarded RED/GREEN admission. Production commit/integration/master verification remain separate later steps under standing authorization and required review; this plan does not itself promote or launch a candidate.
