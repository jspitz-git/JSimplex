# Offline shared zero-counter candidate

Prepared only, not Julia-parsed, loaded, compiled or executed. The user accepted the prior bounded proposal and explicitly requested a separate candidate and structural tests without Julia. This scope supersedes runtime TDD/full-suite skill defaults: the saved four missing-source checks and eight passing source checks are Python text checks, not a Julia RED/GREEN run or allocation proof. Frozen old evidence, candidate sources, master, actual src/test/environment/CI remain unchanged.

## Exact candidate

`panel.jl` is a separate whole-file copy of the original `diagnostics/direct-bg-blocked-update/reproduce/panel.jl`. It adds exactly one module-private binding:

```julia
const _BGB_ZERO_COUNTS = ntuple(_ -> 0, Val(20))
```

Only the zero-tuple expressions at `BGPanelCounts()`, `counts(::BGNoCounts)` and `_bgb_dimensions` now reference this binding. The expected type is `NTuple{20,Int}`, with all20 entries zero. No new public export, helper method, mutable singleton, numerical branch or instrumentation was added. The original module name is retained; a future isolated harness must load exactly one panel implementation into a fresh parent, never overwrite the frozen module's methods in an existing session. Its parent must already bind the admitted JSimplex stage.

The exact inverse removes the single declaration and reverses the three replacements, recovering every original byte. Original `bump!`, `peak!`, checked addition, dimension/density/finite gates, pivot policy, coefficient arithmetic, workspace layout and other methods are unchanged. `BGPanelCounts()` still constructs a new mutable owner for each call. Immutable zero tuples can safely be shared: updates replace the owner's `values` field, not tuple elements. Existing diagnostic counts and all20 statistics remain intact.

Candidate SHA256: `19dccf0d5259d730b19333b2b1c685a50ee76f93d2cc3b242cb54a762cae9295`.

## Prepared tests

`zero-counts-tests.jl` defines `BGZeroCountsTests.run_zero_counts_tests()` without invoking it. Its future parent must contain the candidate `BGBlockedPanel` and frozen `BGBlockedPanelTests` fixture definitions. No driver or launcher is created here. The original tests including the exact P011 zero-allocation assertion remain byte-identical; this new file supplements them and does not replace their integration coverage.

Five testsets contain41 literal test expressions and350 prospective assertions on their intended execution path:

| Group | Expected assertions | Defect caught |
|---|---:|---|
| Immutable zero statistics |7|Wrong constant type/width/value or uncounted behavior|
| Twenty independent counter/overflow cases |300|Shared mutable owner, wrong slot, missing update, unchecked overflow or altered state after overflow|
| Peak ownership and monotonicity |10|Peak overwrites unrelated slot, decreases maximum or changes another owner/saved tuple|
| Thirteen literal dimension cases |26|Changed boundary/gate, incomplete or incorrect decision fields|
| n32 concrete eligibility |7|Charged counters leak into rejection, counter mutation, changed selected input values/owners|

Every mutable-slot case constructs separate a/b, checks both zero, bumps only a by1 and2, checks b and saved zero values, then forces typemax(Int)+1 and requires OverflowError with a/b/constant preserved. The peak case preserves slot1 and previously returned values while updating only slot14. Expected zeros are a literal20-entry tuple in the tests; expected one-slot updates use Base.setindex rather than the candidate's helpers. Dimension expectations are hand-derived literals, including width64/63,4/3-step rejection and invalid dimensions. The n32 test uses the original real Carrier fixture, two eligibility calls (ordinary and with a previously charged counter), saved packed values/row memberships and selected owner identities. This last small check is not the full diagnostic ownership proof or a complete graph snapshot.

These are proposed runtime checks only. No Julia parser, macro expansion, import, compile, test, IR query or numerical call has run. The old P011 remains failed and the six N026 checks remain unreached. Zero allocations and the explanation of residual400bytes/3events are not yet qualified.

## Work and memory budget

Candidate change: one fixed tuple initialization at module setup; thereafter three direct immutable-value uses replace repeated integer-length tuple factories. The constant's20 Int entries have160 scalar payload bytes on the pinned64-bit target; total module/object/header retention and cold initialization allocations are unmeasured. No new mutable scratch, capacity reserve, invalidation, full-vector/matrix scan, basis solve, update-chain traversal, precision conversion or growing cache is introduced. Cost is independent of n, nnz(U) and chain length. Each mutable counter still has its own object; bump/peak tuple replacement remains unchanged. The source is an isolated Float64 panel candidate; no runtime claim for other precisions follows.

Prepared test cost is cold only:44 mutable counter objects across the fixed cases,20 expected overflow exceptions,13 dimension calls, one n32 zero-matrix Carrier setup and two eligibility calls, before/after structural snapshots and ordinary Test storage. Counter tuple expectations and saved tuples add fixed-width values. Fixture construction and snapshot scans/copies are outside any future measured eligibility window; no factorization, basis solve, BG update or extra solver iteration is introduced. Julia compiler behavior and allocations are unmeasured, so these are source counts, not a native-memory or elapsed-time budget. The350 assertions are not historical execution evidence.

## Next boundary

After independent offline acceptance, prepare a separate concrete driver and admission for the unchanged structural suite plus bounded old/static tuple, dimension and eligibility comparisons. Preserve full decisions, counter independence and all cost/preparation records; keep the original-shaped wrapper as a separate control. Never infer elimination of400bytes from this source edit alone. Any Julia launch requires the existing fresh host/source/runtime identity checks and exact independent admission. No old driver/checker is rerun automatically, and no production integration is authorized by this offline candidate preparation.
