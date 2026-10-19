# Direct BG export/import specialization design

Planning-only continuation of allocation-provenance commit39beb6ff4a9f287dbbfc4c2a3b821d47ce374d0d. No implementation, Julia, compiler query or measurement in this step. The previous candidate's performance rejection remains valid.

## Decision and evidence

Choose a distinct candidate that makes the existing helper call chain explicitly parametric through positional cores. Keep the keyword-facing diagnostic interfaces, algorithms and storage representation. This is a bounded compiler-specialization hypothesis, not an established inference diagnosis: the accepted full-rate profile identifies materialized objects but did not inspect typed IR.

The alternatives are (a) annotations alone on the current keyword chain, which gives less explicit control over forwarded callable specialization, and (b) splitting production and test algorithms, which risks semantic drift. The chosen single-body cores preserve injectable tests while making callable/owner types explicit. Arena/U-layout changes, cache-policy retuning, removing the wrapper, and a different normalization algorithm are outside this design.

Primary source evidence: results/DIRECT-BG-EXPORT-WORKSPACE-ALLOCATION-PROVENANCE-REVIEWED/{REPORT.md,attribution.json,result-review.md}. Native sparse32/dense32/sparse96 net event increases +5/+9/+1 are reconciled. Per lifecycle there are6 CSC boxes at export84,4 CSC/policy boxes at factor63,3 import tuples and2 constructor objects; dense native adds12 Int64 boxes at export8/84. Three matches closures exist on both sides, with no Core.Box records. Fourteen reference-only outer timer-result records and two inner lifecycle return tuples are distinct harness effects. Equal native GC/profile residuals are not a native allocation ledger. Preserve the ordinary dense96/native +41 anomaly and variable native byte totals.

Julia's manual describes explicit type parameters for forwarded callable specialization and function barriers. This motivates the hypothesis, not a promise about these installed call sites: https://docs.julialang.org/en/v1/manual/performance-tips/#Be-aware-of-when-Julia-avoids-specializing (consulted2026-10-19; online documentation is not an installed-runtime pin).

## Frozen scope and invariants

- Standalone Float64/Int packed DIRECT BG; native threshold_one and Markowitz default. Master26e2291745999f485a74f643298ca997d65c7205 stays unchanged. No production routing, HH, other precisions/managers, new dependency, threading or global compiler settings.
- P0=16*(l+u)+8*(n+1), B=min(1048576,fld(P0,16)); cache charge512+8*cld(n,64), optionally32*n. Checked arithmetic, exact-size reuse, release on dimension/budget changes and failure; no new high-water retention.
- Keep extraction, validation, normalization, fallback, floating operation order, scaling tests, every numerical safeguard, allocation order, exception identity, busy guard and one-point publication unchanged. Keep all input representation support/rejection rules.
- Preserve copy/shared-prefix ownership; old/new factors coexist until successful publication; copies start without workspace. Do not remove constructor owner/wrapper or matches closures merely because they allocate.
- No new retained fields, mutable result holder, cache, vector, matrix, backend or global state. No new full scans, basis solves, copies, conversions or repeated validation. The importer still returns the same tuple; the compiler may or may not eliminate its heap materialization.
- All historical scripts/raw/reviews/stages/STATUS/roadmap remain frozen. Current authoritative continuation is this new plan plus the cited results, not the older STATUS next-action text. CI remains off and automation paused.

## Single-body kernel boundary

Create only a later sibling diagnostics/direct-bg-export-specialized/reproduce. Rename `_bgx_` to `_bgxs_`, BGExportWorkspace to BGSpecializedExportWorkspace, BGExportFactor to BGSpecializedExportFactor and _BGXBuildOwner to _BGXSBuildOwner throughout the four candidate files and adapted tests. Do not overwrite old methods or types.

For each helper listed in the plan, move its existing body into one positional `*_core` function. The keyword facade forwards defaults exactly once and has no mutable storage or additional checks. The core explicitly binds owner, allocator and forwarded callable types with positional `where` parameters. Native/Markowitz backend overloads and unsupported fallback remain distinct. The actual arithmetic/control-flow body exists only once.

Use `@inline` only on the thin forwarding facades and the import core, where the tuple is created. Do not blanket-inline the orientation, build or refactor core; no `@generated`, `@eval`, `Val` of dimensions/nnz/values, forced return conversions or new `::Any` containers. The original normalization Bool remains a runtime Bool. Compiler specialization grows with concrete owner/backend/hook types, not every n/nnz. Record preparation/startup compile cost separately from warmed execution; added code size is a risk, not zero work.

Both the ordinary path and injected failure path use the same cores. Callable adapters retain the old keyword hook contracts, including arbitrary test allocator and exporter callables. Do not bypass an injected hook, run it twice, move it past a guard, or specialize only the benchmark driver.

## Work, memory and acceptance

Source-level numeric work and all array allocation requests/payloads must be identical to the previous workspace candidate on success and failure. The existing cache cap, retained graphs, private old+new publication peak and diagnostic storage obligations carry forward unchanged. Additional runtime metadata objects are not assumed absent; they are measured. Code specialization/compilation may increase and must be reported with cold wall/resource observations.

Use the same packed DIRECT reference and frozen four fixtures for performance. Old workspace results are historical context only, not a multiplied ratio or contemporary timing control. Every first-process cell must retain the prior gates: paired median whole time<=0.95reference, median bytes and events nonincrease, every warm/measured final and probe factor graph<=1.10reference, measured compile/recompile0, at least3/7 faster, exact outputs/modes/input preservation/residual checks. An allocation-only success is a partial result, not performance acceptance. A second reversed-order process is allowed only after all8 first cells pass and fresh concrete admission; both processes plus10/14 faster are needed for component qualification. No production promotion without the still-separate ordinary-BG comparison.

Do not tune annotations, fixture order, cache budget or gates after seeing a failed cost result. Stop this fixed candidate and preserve evidence. A pure timeout may receive a separately admitted identical longer run under the standing user instruction; correctness/error/pin/compile failures are not timeouts. Initial300/292, longer600/592, no multi-hour run. This planning step launches nothing.
