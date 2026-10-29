# Independent source and admission review — initial binding

Decision: **do not launch the unchanged initial source** until the important anchor/claim mismatch below is resolved and the source pins are refreshed. After that narrow correction, the source/work/guard review found no additional blocker to exactly one fixed guarded attempt, with a shared ceiling no greater than 1800 seconds. This is admission to collect diagnostic evidence, not acceptance of results, numerical skip logic, SS update reuse, production integration, or a speedup.

Scope: read AGENTS.md, PLAN.md, driver.jl, graph.jl, run.py, command.json, the three guard sources, inputs/library/source pins, vendor provenance and relevant KLU APIs, prior anchor metadata and host-before-review.json. No Julia process, native call, old driver, or old script was executed. Independent Python only parsed new Python sources, hashed files, inspected TOML/JSON and /proc. No production/src/test/environment/master edit is part of this review.

## Finding requiring correction

PLAN promises exact L/U/F entry totals and block sizes/counts at states 0/80/160 in each history. The initial driver instead checks `L_nnz + U_nnz == sum(lu)`, the separate F total, block count and maximum dimension. An L-count increase and equal U-count decrease would pass this purported exact L/U equivalence. The accepted prior metadata has separate L/U counts but no full block-size vector. Assert each count separately and describe the available size check as maximum block dimension; do not claim full-size equivalence. Preserve this initial assessment and refresh/reverify immutable pins after the correction.

Minor: `inputcolumn` applies `copy` to already-owned ordinary indexed vector slices. This duplicates the entering row/value arrays once per profile, O(nnz entering column), without improving ownership. It is unnecessary work/allocation in this cold diagnostic, and removing the two outer copies is appropriate. It does not create a production performance regression or call for a timing benchmark.

## Numerical and structural assessment

- The combined private `_extract!` call is supported by the pinned vendored API: it calls native sort once and exports L/U/F/P/Q/R/Rs together. The empty-F branch supplies all-or-none F triplets correctly and sets its empty column pointers before incrementing. The driver converts all exported index arrays from zero-based exactly once. Unsorted F rows do not matter to the block CSR.
- The factor identity probe uses `z = point[Q]` and `(B*point)[P] ./ Rs`, matching the vendored relation `(L*U+F) = diag(Rs)^(-1) * B[P,Q]`. Finite positive scales, finite coefficients, permutations, nonempty blocks, nonzero U diagonal and block structure are checked. This deterministic probe validates a necessary extraction identity for one vector; it does not qualify a solver or skip implementation.
- A stored F slot has source column block and earlier target row block. FTRAN uses that graph, seeded by exact-nonzero entering-column rows mapped through P. BTRAN uses the reversed graph, seeded by the original leaving basis-column slot mapped through Q. It does not incorrectly map that seed through P. All stored duplicate/zero slots retain traversal cost; zero values do not propagate reach. Exhaustive 3-vertex DAG closure tests cover both directions and all seed subsets, plus explicit zeros/duplicates and change cases.
- L/U stored counts include the exported unit L diagonal. Subtracting one per active row omits those implicit L operations while retaining U diagonal divisions. The native-column block-only model counts all F column slots in reached blocks. The separately labeled transpose edge-aware model counts reverse dependency visits and requires a reverse index. Neither weight is measured instructions/flops or proof that native routines already skip those blocks. Dense clearing/gather/scatter, scans and correctness obligations remain outside the weights.
- Current-coordinate change classification correctly separates diagonal/above/below blocks. Its fixed-maps/scales qualification and possible row-sum scale changes are explicit. Canonical minimum-column tokens compare column memberships, not row ownership, numeric factors or scale equality. Fresh factorization at each state is essential diagnostic work; it does not authorize reusing an old graph through an update chain. Signed zeros and other numerical skip obligations remain open.

## Work, allocations and retained memory

The only affected frequency is this bounded offline diagnostic: 3 actual captured histories × 161 successive bases = **483** fresh factorizations and **483** combined exports/native sorts; **483** full identity probes, **966** actual RHS reach profiles, **zero basis solves**, and **zero benchmark windows**. Each basis also assembles/hashes the sparse matrix, copies zero-based factor input in the vendor constructor, allocates primitive exports, checks permutations with two sorts, scans factor structure/finite values, builds forward/reverse CSR in O(blocks + F slots), traverses the two RHS reaches, and sorts the sparse column-difference union. The identity performs B, U, L and F matrix-vector actions. These scans, copies and checks are diagnostic work rather than projected per-pivot production savings.

No unnecessary **material** work or retained-memory growth was found for the stated diagnostic beyond the minor duplicate copies above. Native factors and exported arrays are local to `profile`; only scalar/string dictionaries and the current/previous column-token vectors escape. Explicit GC every eight states bounds pending local-factor accumulation, subject to finalizer behavior; it is not evidence of native free completion. The 5,000,000 combined stored-slot check follows export and does not bound native allocation by itself; existing 8 GiB VM, RAM/swap monitoring and the time guard remain necessary. Only one captured history is current at a time. Primitive witness conversion is transient, output is capped at 512 MiB, and no full matrices/factors are retained in the 483 result dictionaries.

Forward plus reverse graph typed payload is `16*(blocks+1) + 18*Fslots` bytes with 64-bit offsets/targets and byte flags. The reported row/column maps and dimensions/weights add `16*n + 16*blocks` bytes. This excludes array headers, native factors, exported arrays, masks/queues and diagnostic transient arrays. Persistent reverse indexes are O(n + blocks + Fslots) memory and must be invalidated/maintained; the extra edge-aware model is not free. No production hot path changed, so a before/after benchmark is unnecessary for this source-only review and no runtime benefit is inferred.

## Guard and immutable evidence

All **43 of 43** initial inventory bindings matched their resolved paths and SHA-256. Vendor KLU.jl/wrappers, all three guards, library pins and inputs are byte-identical to the prior accepted `diagnostics/klu-umfpack/2026-10-29` copies; `prior-results.toml` is byte-identical to its results-1.toml. The source inventory pins the fixed launch command, runtime, scripts, inputs, environment files and libraries. Python AST parsing succeeded for run.py and all three new guard copies.

The host record covered all **713** historic groups on the same boot. An independent /proc-only snapshot during review found the exact same historical group set, no Julia/group/session conflict, MemAvailable **22,701,612 KiB**, swap used **0 KiB**. A new immediate preflight is still required at launch. The fixed command uses existing compiled modules, Julia/BLAS one thread, heap hint 2 GiB, the pinned project/runtime and fresh witness directory. Existing sole-owner lock, live-Julia check, 8 GiB VM cap, available-RAM >= 6 GiB / swap <= 1 GiB guard, owned PID/start-ticks/session handshake, parent-death SIGKILL and bounded cleanup remain unchanged. Admission must bind run.py with exactly the reviewed command, expected exit 0 and a shared deadline <=1800 seconds; no second run or workload increase is approved here.

Initial SHA-256 bindings:

- source-pins.json: `5e9d061f861b803d96e5be51f6aa2311ef65f9850d359f2bb893347921b3bcb8`
- driver.jl: `8d835fba66dc3a6b777ea2be64dfa7558daf8f1b5ac6436d35db8bfc50136eb5`
- graph.jl: `48ba012d1aad00cb32bfbc48c91fc937f3408aca2634cb0e346a527fbb00d0ce`
- PLAN.md: `09dd5ad1ac1ac0ac5e3b9e9c2bcf21e631f84bc01a6198017a2d7e076647fc5b`
- command.json: `cacb0ea4125eb6e5cd32f424973d3a8e0440222b53d17f9bb0bd472f944c88e4`
- run.py: `dcc84f235fbcb9f2a55ba3e97fa14f628880b7c66617141c06b5914154596691`
- guard/entry_gate.py: `6b1f569959d53c2d37faa0e8f6a8ebda6887ef8b6e5602db8e0b15ae5f530ff9`
- guard/guard_reviewed.py: `92f1c19ded9615f8a1f8cab70bf5209d8dc9db734e9592c3bbf3f5852ee9aa67`
- guard/supervisor_reviewed.py: `f983198c245079eafa712d1b4752a6ac56456aa91058fc469245fa77759bf0ec`

Postrun acceptance still requires actual counts/exit/tests/loaded library hashes, all nine corrected anchors, unchanged pins, full group/session closure and independent Python recomputation from every fresh witness, followed by independent results/work/memory review. An archived version-matched native triangular source analysis supplied later must be independently hash-bound before it supports stronger weight claims; it changes no executable source here.
