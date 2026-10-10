# Simplex core architecture: design and evidence boundaries

## Objective

Reduce repeated computational work and memory traffic in primal and dual
simplex while retaining the numerical protections established by earlier fixes.
Investigate architectural changes in five independently reviewable stages;
there is no promised speedup or commitment to merge an unsuccessful prototype.

This design records the proposal preceding the user's request for a durable
plan. Planning does not start production implementation or numerical jobs.

## Evidence

The baseline is production commit
`fe839aa72171d7496c9c931d9393278448c7317e`; diagnostic commit `6ded1fc`
contains [the measured time budget](../../../diagnostics/simplex-time-budget/README.md)
and [results](../../../diagnostics/simplex-time-budget/RESULTS.md).

The medium prefixes cover 4,000 dual and 2,000 primal steps. Two historical
handoffs each cover 256 actual primal cleanup steps, despite different origin
algorithms. Fresh prefixes use HH/native320; cleanup uses HH/native160.
Primal phase I includes artificial columns and is not the dual working matrix.

Measured targets include 2,003 primal reconstructions in 2,000 steps and 16,004
finite-workspace checks in 4,000 dual steps. These counts establish repeated
work, not that every check is redundant. Basis solves, full-vector operations,
lazy cleanup weight construction and refactorization-associated GC also matter.
The long reduced-model phase II of the seven-hour solve has not been profiled.
No whole-run or cross-solver speed ratio follows from these slices.

## Architectural directions

1. Track mutation and validation dependencies explicitly. Reuse a check only
   for unchanged inputs, with conservative invalidation on uncertain ownership.
   Establish a complete mutation inventory before choosing the tracking API.
2. Build on existing incremental primal updates. Avoid routine reconstruction
   only when native-precision error control and independent reconstruction can
   preserve correctness. Keep recovery, phase-boundary and final certification.
   Merely enabling existing policy flags is not an implementation of this design.
3. Preserve exact sparsity support through solves, pricing and updates. Reuse
   existing indexed-vector/hypersparse facilities. Never prune small entries;
   support invalidation and dense fallback must be explicit.
4. Separate reusable factorization scratch, retained factors and temporary data.
   Respect each backend's capabilities, pattern changes, ownership and memory
   limits. Do not infer reusable symbolic structure from equal dimensions.
5. Make phase and postsolve/cleanup handoffs explicit. Transfer only state whose
   matrix, ordering, bounds, costs and basis dependencies remain valid. Preserve
   original-model certification and safe fallback when reuse cannot be proved.

## Constraints

- Native problem precision is the normal computation mode; wider precision is
  an exceptional recovery/reference path, not a performance shortcut.
- Do not weaken tolerances, residual checks or certificate acceptance.
- Keep simplex candidate selection unchanged in arithmetic-preserving changes.
  Incremental arithmetic may change trajectories and requires separate evidence.
- Keep performance-adaptive functions disabled in controlled comparisons;
  numerical protections remain active. New adaptive selection rules are separate.
- Cover both simplex algorithms and PFI, HH, FT, SS and BG, with native and
  Markowitz refactorization where supported. Direct experimental managers stay
  separate; this project does not silently promote them.
- Use one numerical Julia process, one Julia thread and one BLAS thread,
  8 GiB virtual-memory limit, 6 GiB available-RAM floor and 1 GiB maximum swap.
  The guard may stop only its own process group. Preserve failed attempts.
- Do not solve or factor big.mps, largo.mps, AnyMod.mps or their aliases.
- Preserve old worktrees, snapshots and local environments; never commit
  Manifest.toml or LocalPreferences.toml. Preserve disabled precompile workload.
- Repository prose, code comments and commits are English; user communication
  is Czech. Follow AGENTS.md performance and numerical review requirements.

## Acceptance and separation of claims

An optimization must reduce a measured source of work or cost without an
unexplained numerical regression. Report compilation, setup, ordinary iterations,
recovery, handoff and certification separately. Repeated uninstrumented timings
are authoritative for elapsed time; counters explain work, not automatic speedup.
The earlier sampling overhead was material and cleanup sampling stalled; do not
repeat that failed method without diagnosing it first.

An identical-arithmetic change must preserve event/state fingerprints on paired
inputs. A changed-arithmetic prototype must preserve valid outcomes, original
feasibility, reference objectives and supported precision semantics; iteration
and recovery changes must be reported, not hidden behind a faster total.
A final status without its required certificate is not a successful solution.
