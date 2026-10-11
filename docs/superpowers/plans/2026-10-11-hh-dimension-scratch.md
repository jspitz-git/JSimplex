# HH dimension-change scratch ownership plan

> **For agentic workers:** Use `superpowers:executing-plans` sequentially.

**Status:** Complete locally: production8701a58 -> master4143dad, pushed.
Focused4366 and integrated344 assertions pass; broader S4 remains pending.

**Goal:** Release obsolete HH solve-scratch capacity after a successful dimension
change and retain the extraction buffers already allocated for the new shape.

**Architecture:** Keep the existing factorization transaction and immutable
base/update ownership. Prepare all dimension-dependent vectors before publication;
reuse same-length vectors, publish newly sized private vectors only on success.
No public API, numerical policy, tolerance, symbolic-reuse or coefficient changes.

**Spec:** [Core architecture design](../specs/2026-10-11-simplex-core-architecture-design.md), S4.
**Tech stack:** Julia1.13, HH native/Markowitz, Test, existing guarded runner.

## Global constraints and order

One guarded numerical Julia process, one Julia/BLAS thread, heap hint2G,8GiB VM,
6GiB RAM floor,1GiB swap maximum. Preserve all old worktrees/environments and
attempts. No excluded model or alias. Repository content English. At plan creation, the
S0 isolated calibration had priority; its process absence was confirmed before
S4 RED. Always inspect actual pin manifests and the host before edits/launches.

Ruling: the roadmap permits S4 independently after an earlier rejected experiment.
This small memory-lifecycle task follows the static inventory while S0's timing
calibration is unresolved. It cannot accept S0, S2 or a whole-medium improvement.

## Concrete finding and design

`refactorize!(f::HuangfuHallFactorization,B)` creates fresh `work`/`auxiliary` when
n changes, uses them for extraction, then discards them and resizes the four old
solve/preparation vectors. Julia1.13 `resize!` shrinking changes length and clears
removed references; it retains the backing Memory allocation. A large factor
shrunk to a small/empty one can therefore keep obsolete private vector capacity.

Modify only `src/huangfu_hall_factorization.jl` for production. Preserve the
signature and these decisions:

- Keep existing work/auxiliary when their lengths equal n. Otherwise retain the
  newly allocated extraction vectors and publish them after successful extraction.
- For prepared_partial/prepared_direction, keep same-length storage. Otherwise
  allocate `Vector{T}(undef,n)` before publication. Contents need not survive a
  successful refactorization because prepared_valid becomes false; valid prepared
  storage must survive a failed factorization. No arithmetic uses new undefined
  elements before its normal initialization path.
- Prepare vector references inside the existing try before publishing base or
  retiring updates. On candidate-construction/extraction or vector-preparation failure preserve
  live base/history and prepared identity/data; discard the backend construction workspace as already required.
- Replace the final resize loop with assignment of the four prepared references.
  Leave pools, unit workspace, extraction cap and all numerical extraction unchanged.
- Preserve the old dimension decision until pool retirement/clearing finishes;
  assigning new work earlier must not make a changed dimension appear unchanged.
- No capacity scan, global cache or new per-iteration field. Same-size refactors
  must preserve vector identity and introduce no vector allocations. Shrinking
  adds at most two small prepared-vector allocations while dropping old capacity;
  changed-size work/auxiliary allocations already exist and must no longer be wasted.

## Review focus

1. Same-size failure can mutate disposable work/auxiliary, but never valid
   prepared data or a shared saved factor.
2. Dimension growth/shrink/empty transitions must initialize scratch before use
   for all supported scalar types and both backends.
3. Checkpoints own private scratch and shared immutable coefficients/history;
   avoid counting legitimately retained saved-factor storage as a leak.
4. Memory assertions must inspect backing capacity, not just vector length or RSS.
5. A scratch-only result must not claim a bound on the entire factor/backend,
   arbitrary-precision payload or process allocator/JIT memory.

### S4-A1: Reproduce retention before the production edit

Files: create `test/hh_dimension_scratch_tests.jl`; later register in
`test/runtests.jl`. Tests inspect Julia1.13 Memory backing, consistent with the
repository's existing packed-upper retention implementation.

- [x] Write a65536-row Float64/native diagonal fixture, refactor to4 and then0.
  Require the total backing elements of work/auxiliary/prepared_partial/
  prepared_direction to equal4n after each successful dimension change. Preserve
  a saved factor separately and verify its solves, excluding it from the scratch
  payload metric. Confirm same-size identity before shrinking.
- [x] Cover small dimension transitions for Float16/32/64, BigFloat,
  Rational{Int}, Rational{BigInt}, native/Markowitz. Verify forward and transpose
  equations, same-size identity, invalid prepared state after success and saved
  factor independence. A singular changed-size candidate must preserve vector
  references, prepared data, active base and update history.
- [x] After S0's driver stops, verify host process absence and snapshot active
  src/test/env plus exact test/launcher. Run only the new regression under the
  guard; expected failure is retained scratch capacity after shrink/empty.
  Do not attribute a compilation timeout to the tested behavior.

### S4-A2: Minimal publication change and focused verification

- [x] Implement the vector-ownership change only after the observed RED.
- [x] Run the same guarded regression GREEN and register it in runtests.
- [x] Run existing HH factorization, precision, Markowitz and integration tests.
  Use normal compilation for cost claims; if a bounded compiler stall recurs,
  record it separately from semantic coverage and diagnose before expanding work.
- [x] Compare baseline/candidate retained scratch capacity on the same large-small-
  empty history. Measure warm allocation bytes/events and elapsed on representative
  sparse/dense Float64 HH refactors, native/Markowitz, including unchanged sizes.
  Three interleaved pairs, separate compilation, identical basis matrices and
  forward/transpose results. Report ordinary same-size costs separately from
  changed-dimension reclamation; no whole-solver speedup inference.
- [x] Independently review numerical ownership and AGENTS.md work/memory costs.
  Explicitly account for new small allocations on shrink, removed discarded
  extraction vectors and unchanged-size work. Resolve blocking findings.

### S4-A3: Integrate only verified production files

- [x] Record result modes, pins, failures and measurement limitations in
  diagnostics/simplex-core-architecture/S4-SCRATCH.md and STATUS.md.
- [x] Commit the production/test change separately from diagnostics. Preserve
  user dirt and environments; integrate only reviewed passing code to current
  master, validate the integrated focused regression and push under the standing
  authorization. Record actual commit/push IDs.
- [x] Leave S4 broad/backend attribution and S0 long reference pending; resume
  the already planned S0 next gate without repeating accepted calibration.

## Completed execution record

Static and final code review accepted this scope. Pool retirement uses the old
dimension before publication; failure promises cover candidate construction/
extraction/vector preparation rather than arbitrary later allocation failures.
No new per-iteration scans, solves or copies were introduced.

red-1 exit1/pins unchanged:6 passes/2 intended capacity failures. green-1
exit0/pins unchanged:344 passes. focused-1 normal compilation exit0/pins unchanged:
4366 passes, including the344 regression assertions. cost-1 exit0/pins unchanged:
60 matched records, unchanged same-size allocations and released changed-shape
scratch capacity. Exact costs/limits are in S4-SCRATCH.md.

Architecture production8701a58 cherry-picked to master4143dad. integration-1
passed344 assertions directly from master, exit0/pins unchanged. Host process
absence and unchanged main user-file hashes were verified. Master4143dad pushed
and remote identity confirmed. Subsequent S0 smoke passed and its long reference
is active; consult STATUS.md for current process identity. No S4 process remains.
