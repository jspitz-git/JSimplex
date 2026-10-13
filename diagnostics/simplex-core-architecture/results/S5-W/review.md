# S5-W independent offline numerical/work/memory review

Verdict: ACCEPTED

Critical: none.
Important: none.
Minor: none.
Unresolved findings: []

Acceptance covers the S5-W source oracle and the separately gated S5-X OFFLINE candidate-preparation plan. All new runtime outcomes remain UNQUALIFIED. This is not numerical admission, execution evidence, a solver-defect finding, proof of nonexecution, or permission to create/run a launcher. Separate closure and publication remain required.

## Scope and independent evidence

I read current STATUS, the S5-W plan, oracle report, S5-X plan, original fixture, actual initialization/crash/reconstruction/diagnostic/guard/catch/default source, and the V evidence and accepted review. All executable checks were newly written inline read-only Python/shell commands. Saved W/V/U/T and older collectors/auditors were read only as text or hashed, never run or imported. No Julia query/parser/import/compile/native operation, new LP arithmetic, numerical driver, launcher, test, benchmark, source/environment/cache/CI edit occurred. This review is the only file written by the reviewer.

- Independently streamed and matched all **189 W evidence bindings** and all **8 author bindings**. The 19 literal source checks, 14 entry checks and 8 author checks agree with actual source and evidence; Boolean flags were not treated as runtime proof.
- Independently matched V's **166 evidence bindings**, 21 source checks, 9 author checks/7 bindings and 12 closure checks/24 bindings. Checked its seven publication predicates against the frozen closure, original source excerpts, staged membership and publication artifacts. All 26 listed content hashes match current files and the original commit; all **27 published paths**, including the manifest itself, have byte-identical original Git blobs at `48771ac`. Authored publication whitespace is clean with only the already preserved excerpt exceptions excluded.
- Reconstructed **24 lexical testset slices** from actual files, matched their text/hash/start lines, and matched **48 original log rows** including normalized counts, historical head and failure conclusion. Each run, `38142752357` and `38149970679`, separately has **511 selected PASS**; both entire runs remain **failed**. These are selected groups including adjacent coverage, not 511 fallback assertions or current full-suite success. Read both historical Git heads and compared all **32 whole files** directly against current bytes; all match. Checked four exact source excerpts and all four literal fallback test references, each an event-count assertion.
- Freshly rehashed **U master1512**, **GREEN1489**, **T891** and **U closure123**. Historical OLD test hashes resolve only to U/original-test.jl; older STATUS/roadmap hashes resolve to U/before-U, and later U-closure continuation hashes resolve to V/before-V. No historical binding was rewritten. V's accepted review and report copy match.
- The W original final-factorization testset is byte-exact in actual source and its frozen file, SHA-256 `dd0e7254b08e93063eeb467956761b45ab8fec1b1f086fd03ddef82a18f25d71`. Its six original assertions remain intact: expired, INITIAL return identity, iterations2, refactorizations>=2, slack indices[3,4], and no crash_accepted. The proposed throwing case correctly preserves these as historical coverage rather than pretending a return can coexist with its exception.
- Fresh host inspection found none of all 20 recorded process groups and no Julia process; boot remains `dade7243-9103-4398-bb45-fa28fbc0be72`. All six user-file hashes match. Actual HEAD is `48771ac4318ada0bff6fef35157ba03b95d99d07`, master is `2b546e946ddb7fdb6c0092df9cc19f566e301aa2`; the production/test/CI/Project diff against master and staged diff are empty. Saved host remote-ref evidence matches these refs; no fresh network publication was performed by this reviewer.

Reviewed input identities:

- W evidence: `b5f041610df9b9c81f09ff3c11c80888b2827f6e5d86420c9aab96f8117ae6cc`.
- W author check result: `f0373eba35bf63dc67730e48128449f2c121219450e38d13ca3a877776c9e3a9`.
- Oracle report: `9b598ccf25fcf88f4f3c6843ec43b032952fd03e60d547830bde1600604375d3`.
- S5-X preparation plan: `16fe4568579f35207caadc497c9c619a330afff544bc2b0ac367932cb23342ef`.

## Numerical/control-flow assessment

The selected composition is meaningful beyond the existing final-refactor stop and other-event observer-failure coverage. It checks INITIAL delivery after work reconciliation and event recording, followed by failure to return. It does not require another successful cancellation/control run.

`src/simplex_start.jl:146` constructs the latched guard. The initial refactorization attempt is charged before assigning TRIAL (`:161`), which is initialized using the same problem and progress; recovery_active is set only after the constructor. The final selected `_crash_refactor!` (`:241`) calls `recompute!`. Its refactor_other event at `src/simplex.jl:434` occurs after incrementing local refactorizations, but before primal and dual reconstruction at `:465` and `:473`. Native refinement returns immediately without consulting the stop (`src/simplex_recovery.jl:484`), recovery is false, and verbose=false skips progress reporting. Thus setting done in this callback is not a stop-before-solves boundary. Conditional normal reconstruction completes before the final guard at `src/simplex_start.jl:242` observes true and latches stopped.

The fallback at `src/simplex_start.jl:84` applies scalar maxima to INITIAL, then delivers crash_fallback on INITIAL. `src/simplex_diagnostics.jl:87` records the event before invoking the observer. An original `SingularException(42)` thrown there becomes `DiagnosticObserverFailure` with the identical cause. The crash numerical predicate excludes that wrapper; the catch rethrows without a second fallback or return. Kernel timing is false, so the outer timed-crash finally does not add timed bookkeeping. This differs from injecting a throwing stop and does not establish guard.exception identity.

The work formula is correct for the selected successful-reconstruction prefix: max(entry_iterations, captured_trial_iterations) and max(entry_refactorizations+1, captured_trial_refactorizations). The +1 accounts for the pre-constructor charge. The selected refactor callback sees the incremented trial count; its finally preserves at least before+1 and does not add an extra count on normal completion. Missing/duplicate/wrong-state events or unexpected work must fail the future oracle, not trigger retuning. Two pivots and interval20 support distinguishing the intended final refactor from scheduled refactoring, while actual reachability/counts remain unqualified.

The fixture's exact constructor/default context is retained: Float64, PFI/native, legacy/native, dual, interval20, limits100000/Inf, fill_limit8, no recovery/refinement/phase_one/hypersparse/sparse-pricing, and kernel_timing=false. Policy, options, tolerances and precision are not tuned. Direct workspace setup does not execute the public presolve/scaling pipeline. Progress shares its original clock, offsets, diagnostics, policy and scaling.

## Ownership, computational work and memory

No unnecessary NEW production work, allocations or retained memory were found. There is no production change, no runtime implementation yet, and no plausible production hot-path cost delta needing a before/after benchmark. No timing, allocation-byte, native-memory or speedup claim is supported or made.

The 17 entry roles are consistent with the actual constructor (`src/simplex.jl:486`). The first eleven are INITIAL and its selected owned workspace/container roles; problem/progress/diagnostics/options/policy/scaling complete the schema. Adding TRIAL, FALLBACK, sentinel and caught gives **21 selected reference roles**, not 21 disjoint allocations. FALLBACK aliases INITIAL; policy/scaling/diagnostics are reachable through progress; immutable options identity is value identity. Fresh trial basis arrays, factor, scratch and selected numerical arrays are distinct, but references retain mutable/transitive backend graphs. The report correctly excludes deep scalar ownership, native-memory confinement, full-state rollback and observer neutrality.

The proposed cold observation costs are justified: **seven owned vector copies containing26 entries** (one length2 plus six length4 vectors), and seven corresponding endpoint equalities visiting at most26 element pairs. These compare selected basis/state/primal/price/cost/bound values without numerical solves or matrix/factor snapshots. Scalar captures have the stated sizes: three clock/offset plus two entry-work scalars; six probe scalars and two state references; two refactor-work scalars; seven fallback scalars and seven after-unwind scalars; sentinel/caught references and returned Boolean. Record containers, local aliases and eventual output/assertion storage are additional costs to inventory in the actual candidate. Slack-basis verification must also remain explicit in that future concrete inventory.

No proposed callback requires vector scans/copies, basis solves, refactors, certificates or a growing instrumentation ledger. Four selected event_count calls use scalar dictionary lookups; they avoid recent_events and its copied ring. Existing diagnostic event storage and numerical work remain additional. The retained TRIAL is captured before reconstruction completes; endpoint checks on retained objects do not observe intermediate values. Seven copied INITIAL vectors establish only selected unchanged endpoints.

Existing work is correctly kept separate: initial/private setup, factor factories, ordinary forward/transpose reconstruction, sparse candidate scans, FTRAN/BTRAN, updates and final refactorization scale with dimensions, nonzeros and update-chain/backend state. The fixed two-column case does not qualify other precisions, managers, dense cases or native/import costs. Native recovery=false suppresses the selected checkpoint branch without proving no other internal work. Numerical safeguards, tolerances and arithmetic precision are preserved.

S5-X properly allows only a separately saved UNEXECUTED candidate with exact construction inverse, actual field/copy/scan accounting and fresh offline review. It prohibits a launcher, actual-test edit, Julia or numerical admission and requires preservation/stopping on future failures. All broader gates, historical rejected evidence, CIoff/HHdisabled and Q/bootstrap/cache/init/native-retention/full-suite limitations remain open.
