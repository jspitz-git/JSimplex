# Task1 — owned phase state and maintained invariants

Task1 is runtime-qualified in its stated small component scope: **106/106 ordinary Test checks passed**, after a16-failure interface RED and a separately observed one-failure ownership regression. No full dual step, proposal execution, transactional pivot publication, recovery controller, public LP solve or performance measurement is implemented/claimed. Tasks2–6 remain open.

## Delivered

The distinct ExperimentalDualEngine module provides eligibility and a frozen/tightenable Float64 native-PFI/Devex policy; private phase workspace/progress/scaling/basis/factor owners; five physically retained stamped supports; inverse basis map and exact primal/dual violation sets; invalidation/generation handling; and capacity-reserved future proposal/undo storage. Numerical thresholds/tolerances and the shared clock are bound to the imported configuration. Working-model data is borrowed read-only under the no-concurrent-mutation contract, not proclaimed universally immutable.

Import constructs one new owned factor from the committed source basis, rather than sharing the old native factor. The additional setup factorization is included in workspace refactor count and EngineCounters. Per-variable writes retain untouched provenance and update membership without full vector scans; unknown writes require explicit invalidation/rebuild. The cold allocating oracle is excluded from ordinary mutation paths. Original-model optimality is not implied by empty working-state violation sets.

## Test evidence

| Ordinary Test group | Pass |
|---|---:|
| Eligibility and frozen policy |13/13|
| Private ownership and retained capacity |41/41|
| Invalid source state rejection |8/8|
| Maintained violation sets |31/31|
| Reusable sparse sets/stamped support |13/13|
| Total |106/106|

Tests cover source preservation including a deliberately dirtied source basic_mask; private numeric/bound/basis/Devex/factor/scratch/progress/scaling owners; unchanged clock/offsets/tolerances; unsupported precision/backend/callback/config rejection; preexisting nonadjacent dual violations outside future row support; free/fixed/boxed classification; invalid weights/nonfinite state; incremental mutations matched to a separately coded full scan; repeated support insert/remove/cancellation, smallest positive subnormal, signed zero and UInt32/UInt64 wrap without physical shrinking. One direct tiny FTRAN confirms imported factor usability. This does not qualify every basis chain or precision, factor-update failure, pivot commit or callback recovery behavior.

## Observed stages and preserved correction

- Original RED: exactly16missing-interface failures,0errors,exit1,5.233447s. Only the bootstrap E module existed; no candidate implementation was executed.
- Initial136-pin GREEN source admission was rejected before any GREEN launch. `basis_matrix(source)` called the existing validator, which writes source.scratch.basic_mask; the original snapshot did not contain that mask.
- Ownership RED: one dedicated ordinary failing assertion,0errors,exit1,9.308282s. It deliberately filled source.basic_mask with true before import, proving the actual owner mutation rather than relying on already-canonical scratch values.
- One correction: validate into the engine-owned inverse map and call the unchanged owned assembly helper directly. Reuse the inverse during initial membership. The full GREEN snapshot now includes and dirties the source mask; all original expectations remain.
- Corrected GREEN:106/106,exit0,12.328131s, exact174pins unchanged and completion marker present. Independent corrected source/admission review accepted SHA256`a66c91ae73c1a1d6b0dedbab677108a9ef5bc119c220e747138c18c074e92118` before launch. Full results reviewed separately after exit.

All times are inclusive guarded process observations, not speed measurements. Each process had its own bounded1800s maximum, no numerical retry of an accepted run. Original source/test/document versions, rejected review, all manifests and raw failures remain preserved. `ownership-before-map.json` resolves changed historical paths to exact before-fix bytes; earlier launch-time hashes are not retroactively claimed to bind changed current files. `green-final-pins.before-provenance.json` is an unexecuted preparation snapshot, not another numerical admission or attempt.

## Work, memory and limitations

OWNERSHIP.md enumerates setup assembly/factor/index builds, workspace/context copies, all reusable values/support/map/set/proposal/journal arrays and temporary overlap. Current support metadata payload is12(4m+N) bytes on64bit before headers; proposal+old numeric capacity is64N. These are field-capacity formulae, not allocations/native-retention measurements. Retained high-water capacities never shrink during support reuse. No factor or complete workspace is copied on per-variable writes.

The implementation does not add production execution work: the module is opt-in and no src/test/public/default dispatch is modified. Candidate phase setup is intentionally more expensive through independent factor construction and additional O(N+z) storage; a later whole-solve comparison must establish payoff. Passing component tests provides no speedup claim.

Independent source review found no hidden full-vector scan in ordinary variable classification and no unbounded growing trace or extra ordinary basis solve. It did identify **one redundant cold N-entry zeroing pass**: the imported inverse is allocated with zeros and then cleared by the nonmutating validator. This adds no allocation/retention or hot-path scan, remains transparently deferred, and should be considered when later setup cost is measured. No correctness finding remains unresolved.

Postcheck34/34 passed, independently matching all observed stage expectations, old source mappings and final174pins. Across26resource samples, all memory/swap guards held; sampled maximum child VmHWM675952KiB, VmPeak1629868KiB and swap0. These process observations include Julia loading/compilation and cannot be attributed to the tiny engine's native allocation traffic. Standalone terminal verification found all788 historical/new groups ANDsessions absent and noJulia, using boot/start_ticks/command identities. Master9940bdabe149e922afa60b5364227a7e7393bc75 remained unchanged. No environment installation, CI change, source/test production edit, master merge or push.

## Continuation

The next task is Task2 (solve outputs, pricing and complete residual checks), not an automatic production promotion. Current source/test/guard/raw/review artifacts are frozen; never rerun their scripts against a changed module. Preserve qualified Task1 bytes and bind any subsequent changed paths explicitly. The live plan ledger records the Task1-only scope, source ownership decision and deferred cold-work note.
