# P011 allocation-boundary diagnostic preparation

OFFLINE, UNEXECUTED. The user's request authorizes a separate diagnostic driver and independent source review, explicitly forbidding Julia. No parser, import, macro expansion, compilation, test or measurement was executed. This is not RED/GREEN qualification, candidate correction or launch admission.

## Question and source basis

RED2 saved 11,759 passes and one unexpected P011 failure, with no byte count. Its unit-level failure guard stopped before the six expected N026 failures. Preserve all original files and that failed result. Installed pinned Base timing.jl wraps the qualified expression `K._bgb_eligibility(f,1)` in a zero-argument closure before Base.allocated. The original test reassigns captured f later. Boxing, inference, result escape and compilation are hypotheses, not measured causes. P011's n32 branch returns a dimension rejection before scans/workspace creation. A zero source counter is not zero GC allocation.

## Prepared driver

`driver.jl` imports the repaired ordinary staged JSimplex, the unchanged candidate panel, frozen recorder and frozen panel-test definitions. It never calls the frozen test entry point, factor adapter, lifecycle, numerical stream, solver or old driver. It defines two reduced diagnostic paths:

- original: qualified `@allocated K._bgb_eligibility(f,1)` (and a separate @allocations counterpart), direct warm call and later reassignment of f to an existing n64 replacement;
- concrete: `concrete_call(f::Carrier)::Decision`, with the unchanged eligibility body called via Base.allocated/allocations, without closure capture of a reassigned local.

These are intentionally different measurement boundaries. The original-shaped probe is NOT the full original run_task1_tests compiled caller: missing surrounding tests/try scopes and different warm history may affect lowering/inference. A difference supports further investigation; it does not prove the actual historical P011 allocation or justify changing its oracle. Reassignment's identity marker is diagnostic, not proof that a compiler retained a box.

Each record has inner_bytes and inner_events from TWO SEPARATE eligibility executions, plus outer @timed time/bytes/events/GC/compile/recompile for each wrapper. Never equate the inner event count to the same invocation as inner bytes, or subtract outer from inner counters. A third, separately labelled consumed_result execution stores the full decision into a typed Ref; its overhead is not the P011 boundary. This proves an observed full decision, not that dead-code elimination was absent in either discarded-result measurement. No automatic zero-allocation acceptance, cause classification or speedup assertion.

## Fixed schedule and observations

Exactly 12 records: first original/concrete, warm concrete/original, then four alternating sample pairs original/concrete, concrete/original, original/concrete, concrete/original. Every record has two calls in byte wrapper (direct warm plus measured), two in event wrapper and one consumed call: 60 eligibility invocations in the source schedule, all n32 dimension reject. This is not an observed entry count: compiler elimination of discarded warm work remains possible. No adaptive warmup, retries, GC(), threshold relaxation, @eval, invokelatest, compiler query or module overwrite. First records are first probe calls, not independently cold processes. Timed compile/recompile and GC values are preserved, even nonzero; such samples cannot establish steady-state zero allocation or a timing improvement.

The explicit decision oracle checks all six fields: start1,count0,acceptedfalse,reason dimensions,finitetrue,20zero counters. Every Carrier field and all TriangularRowCache fields are snapshotted before/after; all mutable owners reachable through these fixture fields are compared by identity. Unexpected sparse or prepared cache refuses. Both n32 input and n64 reassignment replacement must remain unchanged. All correctness observations are outside the inner allocation interval.

## Preparation, work and memory ledger

One n32 zero matrix/Carrier, one n64 denseband matrix/Carrier, one typed Decision Ref. Carrier construction has O(n^2) fixture work, including row incidence searches, and is OUTSIDE inner windows. n32/n64 input matrices have 1,024/4,096 Float64 entries; n64 packed structure has 2,143 stored entries. These are source counts, not measured allocations. No factorization, FTRAN/BTRAN, update/refactor, workspace tile, larger LP or native solve is requested.

Two state captures per Carrier (before/after), with copies of column indices/values, row incidence, order/positions and cache fields; retained owner references and copied values are cold diagnostic O(n+nnz) memory. Duplicate references are deliberately retained for identity roles, not a unique graph byte count. Each inner rejection has O(1) source work; measured GC counters determine compiler/runtime allocation. No new production work or retained production memory is introduced.

Separate load.toml, setup.toml, snapshot-before.toml and snapshot-after.toml preserve time/GC bytes/events/compile/recompile. Loading is measured at top level from the first executable source line, not process start: Julia startup, parsing/compilation before that line, final formatting/serialization/exit and guard overhead are not a complete import/process budget. Output dictionaries, sample dispatcher overhead, checks, and serialization are outside individual wrapper windows. Future admission must preserve outer inclusive elapsed/resources; do not call recorded stages a complete process cost decomposition.

Each record is saved before correctness assertions. raw.toml finally preserves complete/fatal and completed record prefix. Top-level load errors can precede raw output and must remain failures with process logs. Nonzero inner counts are diagnostic data, not runtime success of P011. Output must be a reserved, empty directory; existing outputs are refused. No launcher/reservation/output directory is created in this preparation.

## Required future boundary

Before any execution: separately prepare an exact-source manifest, guarded launcher and strict output auditor; independently admit the concrete run on the repaired stage. Bind driver, all included source, actual Julia runtime and environment, fixed schedule and output schema. Use 300s maximum and existing single Julia/BLAS thread, heap/VM/RAM/swap guards; fresh host refs and all 274 historical groups AND sessions. This document is not an executable launch command or permission to rerun RED2.

Auditor must require all 12 named records in fixed order, correct nonnegative finite metrics, all decision/input/owner checks, complete raw/no fatal, exact loaded package path, process/guard exit and unchanged pins. Distinguish first/warm/sample and inner/outer counters; unexpected failure preserves data. All numerical correctness gates remain unchanged. If the reduced original-shaped probe does not reproduce allocation, diagnosis remains inconclusive. If only the concrete path is zero, investigate call-context lowering before proposing a separate P011 test amendment. If both allocate, investigate unchanged kernel/result materialization before modifying it. No result automatically accepts RED, GREEN or Task3 performance.

## Review and verification scope

Python source-contract checks and exact hashes are preparation evidence only, never Julia syntax/runtime proof. The independent review must assess scope fidelity, metric nesting, preparation coverage, fixed call budget, input ownership and preservation of original evidence. Global STATUS/roadmap and the original plan remain frozen; continuation is recorded only in the local task ledger with before bytes preserved.
