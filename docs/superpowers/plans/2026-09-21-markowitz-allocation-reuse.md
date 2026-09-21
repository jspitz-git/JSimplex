# Markowitz allocation reuse implementation plan

> Execution: implement inline with `superpowers:executing-plans`, following the
> user's approved sequence. Preserve unrelated workspace changes; no commits or
> branch operations are requested for this shared dirty checkout.

**Goal:** Reduce recurring Markowitz allocation traffic in the five audited areas.
**Architecture:** Borrow input CSC storage, retain private construction scratch,
then recycle protected output and dense-core candidates. Compare ordered and
unordered dictionaries before choosing the construction representation.
**Tech stack:** Julia 1.13, SparseArrays, LinearAlgebra; OrderedCollections 2.0.1
is available in the development environment for the comparison.
**Spec:** `diagnostics/markowitz_allocation_report.md` and the user's approval of
points 1–5, with OrderedDict comparison added to point 2.

## Global constraints and review focus

- Preserve input ownership, saved copies and the active basis on failed resets.
- Keep arithmetic concrete for every supported floating/rational type.
- Retain capacity where reusable; do not mutate shared scalar objects.
- Check empty and changing basis/core dimensions, singular/nonfinite failures,
  stored BigFloat precision and copy-of-copy isolation.
- Compare pivot paths, fill, residuals, whole-solve status, allocations and time.
  Recycled Dict capacity may affect iteration order and pivot ties.

## Steps and verification

- [x] 1. CSC borrowing. Add `test/markowitz_csc_reuse_allocation_tests.jl`: compare
  dense-CSC and dense-matrix allocation budgets; verify unchanged input, mutation
  after construction, saved copies and failure recovery across scalar types.
  Watch the budgets fail, replace the copying CSC constructor with `convert`,
  and run the focused Markowitz suite and the production suite.
- [x] 2. Construction workspace and dictionary comparison. Add private scratch
  containing row/column dictionaries, active bits, singleton queues, doubletons,
  affected rows and inverse permutations. Refill after `empty!` with retained
  capacity. Compare Dict and OrderedDict using the same allocation and numeric
  cases, mixed reset histories and complete solves. Record the selected approach
  and any pivot-path changes. No saved factor may share mutable scratch.
- [x] 3. Output reuse. Recycle unshared L/U index/value vectors, diagonal and
  permutations through an inactive candidate. Test repeated nonempty histories,
  branching saved copies, changed dimensions, failed candidates and recovery.
- [x] 4. Core reuse. Reuse private same-size Float32/Float64 dense-core LUs and
  solve work arrays. Retain failure isolation and handle independently changing
  core dimensions. Verify zero warmed container allocations where applicable.
- [x] 5. Generic arithmetic. Remove measured avoidable zero/constant creation and
  repeated threshold work without changing rounding or mutating stored BigFloat/
  BigInt values. Add precision, extreme-exponent and rational regression cases.
- [x] Run independent review, final complete suite and matched allocation probes;
  document actual gains and remaining scalar/rehash allocations.

Commands use `julia --startup-file=no --compiled-modules=existing --project=dev`.
Complete suite: `-e 'push!(LOAD_PATH, pwd()); include("test/runtests.jl")'`.
Record per-step evidence below as work completes; do not infer completion from
an allocation-only probe.

## Execution record

The production source before this sequence is saved as
`/tmp/jsimplex-before-markowitz-sequence.jl` for scoped comparisons.

Step 1: two allocation budgets RED, 379 focused checks GREEN; complete suite
219,198/219,198 (8m15.2s). CSC borrowing probe agrees with the audited savings.

Step 2 decision: choose OrderedCollections.OrderedDict 2.x after the comparison.
Both recycled containers have identical warm allocation totals on standard cases;
OrderedDict avoids history-dependent pivot changes (0/40 versus 40/40 for Dict)
and large-table traversal regressions. This changes tie order relative to the
old implementation; whole-solve comparison must include numerical equivalence,
not require identical iteration histories. Add OrderedCollections as a direct
dependency, already present in the development environment at 2.0.1.

Memory-budget adjustment: retained workspace intentionally raises backend memory.
Keep the old 250 kB sparse-output guard on a saved factor (which excludes mutable
construction scratch), and separately require total storage below one dense
512-square Float64 matrix. This protects the original sparse-storage purpose
without forbidding the newly approved capacity retention.

Step 2 verification: 292 workspace checks (including 56 tie-history/ownership
checks); forcing Dict in the tie regression failed 16 order assertions. Complete
production suite 219,491/219,491 (7m47.3s). A standalone neighboring numeric-type
run omitted `typed_bounded_problem` from solver_tests.jl, producing four setup
errors; the complete suite includes that helper and passes.

Step 3: all four allocation budgets failed at 508 allocations before reuse;
1,196 output tests passed after implementation. Active/inactive backend slots
alternate only after successful construction. Copied output is marked shared
and never recycled. Retired L/U vectors remain in private pools across changes
in sparse pivot count; workspaces remain private to a refactorization branch.

Step 4: 64 zero-byte/count checks failed before core reuse. The first replacement
left one 96-byte workspace-wrapper box on sparse paths. Allocation profiling
identified the optional immutable workspace assignment; making its wrapper
mutable removed that allocation. Same-size private LU factor/pivot arrays and
solve buffers are reused for all supported types; generic scalar arithmetic
still allocates. Repeated empty resets preserve a nonempty spare.

Step 5: add Markowitz-local stored-precision BigFloat magnitude, one read-only
elimination zero, and once-per-column exact Rational{BigInt} thresholds using
integer ten. Preserve the original multiply/subtract grouping and exact BigFloat
threshold predicate. New helper tests failed before implementation and pass
afterward. Generic-focused suite 1,345/1,345, including existing Markowitz cases.

Combined focused suite: 3,129/3,129 (1m13.5s), including all new allocation budgets,
precision/rounding/ownership checks and existing solver integration tests.
Independent review found no introduced correctness bugs and passed 480 randomized
mixed-history resets across all four update modes. Added its suggested dense NaN
failure/recovery regression (56 checks), included in the final complete run.
Pre-existing sparse singleton NaN/Inf acceptance remains outside this allocation
change; only failures actually raised by factorization promise rollback.

Capacity regression: after warming both slots at 64 rows, shrink both to three
rows and return each to 64. Float32 and Float64 allocate zero bytes on the return
and solve correctly (8/8 checks). This specifically verifies retained dictionary,
permutation, sparse-vector-pool and work-vector capacity, independently of the
basis-update wrappers' separate resize behavior.

Matched production audit: 84 matrix cases and 16 complete LP solves per revision,
904 assertions total. All 80 Float32/Float64 repeated-refactorization cases have
zero bytes and objects in every sample. Generic byte reductions are 36–75%.
All complete solves are OPTIMAL, maximum objective difference 8.73e-10; allocated
bytes decrease in every complete solve. Afiro's object counts increase during
fresh setup, and two adlittle dual trajectories change with OrderedDict tie order.
Details, source fingerprints and reproduction are in
`diagnostics/markowitz_reuse_report.md` and matching TOML files.

Final verification: complete production suite **222,012/222,012** (8m03.9s),
including all new tests and reviewer-requested regressions. Separate updated
workspace/core suite **580/580**. `git diff --check` passes. Production source
SHA-256 hashes match the measured after revision. No commits or branch changes.
