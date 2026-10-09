# Basis-manager kernel savings

This work follows the diagnostic measurements in
[`remaining-kernel-probes`](../remaining-kernel-probes/README.md), against master
`21a3fae8fe15107b6f09475d1acd03a9f986b9c8`. It changes only PFI eta traversal and
FT/SS/BG upper-factor solve loops. Pricing, candidate selection, tolerances,
refactorization policy, arithmetic precision and numerical safeguards are
unchanged. Experimental Direct-LU managers are outside this production change.

## Production changes

PFI checks the paired index/value axes once per eta using joint `eachindex`.
Only the sequential paired loads use `@inbounds`; the indirect access to the
solution/work vector remains bounds-checked. This avoids the unsafe assumption
that externally mutable eta payloads can never contain an invalid row. Input
and output dimensions, scratch-output alias rejection, the pivot access and
operation order are unchanged. Mismatched payload lengths now raise
`DimensionMismatch`, including an oversized values array. No per-nonzero
validation scan or persistent validation cache is introduced.

FT/SS/BG packed upper columns maintain unique logical row indices. Packing,
ordered insertion/replacement, row permutations, copying and resetting preserve
this invariant. If the last stored entry is the diagonal, the solve excludes
that entry once and traverses the remaining coefficients without a per-entry
diagonal test. The original loop remains the fallback when the diagonal is not
last. Stable physical IDs retain their existing logical arithmetic order.
This does not promise support for externally corrupted duplicate-diagonal
columns; they violate the existing packed-column invariant.

Both changes apply on every affected FTRAN/BTRAN. PFI adds O(update-chain length)
length checks and removes paired per-coefficient bounds checks. Upper kernels
add O(active columns) endpoint tests and remove O(stored upper coefficients)
diagonal comparisons on canonical columns. There are no new basis solves,
full-vector scans, coefficient copies/conversions, allocations or retained
buffers. Public dimensions and existing numerical acceptance tests remain.

For scale, the preceding unchanged-history census recorded 2,790,850 PFI eta
coefficients across 320 updates on runtime, and 105,956 on fast0507. The new
length compatibility check runs 320 times, not once per coefficient. This is
an overhead reduction; it does not reduce fill or the number of arithmetic
operations required by the existing representation.

## Measurement protocol

`pfi-production.jl` compares frozen original methods with the production methods
on the same PFI object and RHS. `upper-production.jl` installs a process-local
selector around the original and current upper-method bodies; both arms pay
the same selection overhead. Histories are built with the original upper path.
The diagnostic asserts unique sorted logical rows at each measured state.

Both probes use the saved `runtime-40000` and `fast0507-1000` histories, chain
lengths 0/80/320, actual next entering columns for FTRAN and unit rows for BTRAN,
and dense RHS controls. Eleven warmed alternating rounds use batches calibrated
to approximately 10 ms of baseline work. Each timed result must equal the
original bit-for-bit and report no compilation time. Two separate production
measurement processes are retained for each implementation. These native
Float64 measurements do not establish performance for Markowitz, other
precisions or other update histories.

`runtime.jl` performs full legacy dual runtime solves with native refactorization,
interval 320, steepest-edge pricing, partial pricing disabled, presolve/scaling
at their defaults, relaxed integrality and a one-million-iteration ceiling.
The solver time limit is infinite; the external safety watchdog is 1500 s.
Baseline mode restores only the six changed methods from the frozen source.
All other solver code, options and event observation are identical. A one-second
SIGUSR1 profile was additionally collected during the BG baseline; see the
timing caveat below. Event hashes
include every completed pivot/flip; state hashes include basis indices/states,
primal values, prices, costs and weights every 80 iterations and at completion.
Full pairs are correctness/trajectory checks, not repeated end-to-end timing
experiments. Compilation, GC, allocations and original primal certification
are recorded separately from those hashes.

All jobs run sequentially with one Julia/BLAS thread under the established
8 GiB virtual-memory limit, 6 GiB available-RAM floor and 1 GiB swap ceiling.
The guard terminates only its own process group. `run.py` pins sources, tests,
environment and inputs and verifies their digests at completion. Raw attempts
remain under `.superpowers/basis-kernel-savings`; local manifests/preferences
and binary histories are not committed. `precompile_workload=false` is retained.

## HH compact-index experiment

`hh-compact-probe.jl` creates process-local update records with Int32 row indices
and shared original coefficients. Both benchmark arms use the same solve body
specialized for their index representation, with unchanged dot/axpy order.
Construction is outside solve timing and is reported separately. This is an
experiment only: production HH and its recycling/sharing representation are
unchanged. A deployed design would need dimension/range checks, a wide-index
fallback, pool/copy/refactorization coverage and construction/update timing.
A second retained compact cache would add memory; it is not an acceptable
substitute for changing the owned representation.

## Kernel results

Candidate/original median time ranges across the two separate processes,
using the actual RHS at chain length 320 (lower is faster):

| Manager | Runtime FTRAN | Runtime BTRAN | fast0507 FTRAN | fast0507 BTRAN |
| --- | ---: | ---: | ---: | ---: |
| PFI | 0.949–0.954 | 0.982–0.993 | 0.884–0.901 | 0.978–0.987 |
| FT | 0.911–0.927 | 0.956–0.968 | 0.942–0.948 | 0.910–0.925 |
| SS | 0.901–0.904 | 0.970–1.024 | 0.940–0.944 | 0.923–0.946 |
| BG | 0.914–0.918 | 0.978–0.992 | 0.933–0.950 | 0.911–0.945 |

All 192 production measurement cells (24 PFI and 72 upper cells per process)
have exactly equal output vectors and zero measured steady-state solve bytes.
Each cell has 11 alternating warmed rounds. FTRAN savings are repeatable on
long chains. Runtime BTRAN changes are smaller and, for SS, mixed; they do not
support a uniform speedup claim. The CSV retains dense controls and all chain
lengths, including regressions.

Repeated chain-zero controls include fast0507 PFI dense BTRAN increases of
2.3%/2.7%, runtime FT dense BTRAN increases of 3.3%/3.7%, and runtime SS actual
BTRAN increases of 2.3%/3.8%. PFI performs no eta work at chain zero, so these
are useful controls for timing/code-generation effects. Upper selection wrappers
can affect generated code even though both arms pay the same dispatch overhead.
The unwrapped full solves below serve as correctness checks rather than a
second basis for statistical speed claims.

The HH prototype has 48 exact-output timing cells. Its original integer-averaged
allocation reports require the batch-overhead qualification below. At chain 320 its actual
runtime FTRAN ratio is 0.938–0.969 and BTRAN 0.962–0.971; fast0507 ratios are
0.936–0.971 and 0.985–0.988. Runtime update index payload decreases from
3,672,232 to 1,836,116 bytes; fast0507 from 756,592 to 378,296 bytes. These
are index bytes, not whole-factor or process-memory savings. Runtime conversion
takes 0.257–0.260 ms and allocates 1,905,696 bytes in the probe; fast0507 takes
0.059–0.065 ms and allocates 445,320 bytes. Both old and compact records coexist
during the comparison, with coefficient vectors shared. Fresh allocation/layout
also differs, so this does not isolate index width from every locality effect.
Production integration and broader precision/dimension testing remain future
work; no HH representation or pool change is included.

A follow-up asserts total batch bytes before any integer division. All 96
production PFI/upper cells pass with exactly zero total bytes in both arms.
The HH version of that assertion intentionally remains recorded as a failed
diagnostic: after completing 12 runtime cells it exposed a hidden nonzero
allocation in fast0507. `total-batch.jl` then measured all 24 HH cases with
11 rounds: fast0507 chains 0/80 allocate exactly 16 bytes per batch in both arms;
all other cells allocate zero. This is fixed batch overhead, not 16 bytes per
solve. It coincides with larger calibrated counts and is consistent with
argument boxing at heterogeneous-arm dispatch, although no allocation stack
was captured to identify the boxed object.

`hh-isolated-allocations.jl` places `@timed` inside a specialized measurement
function, after arm dispatch. All 24 cases then pass the assertion of exactly
zero total timed bytes in both arms over 11 rounds. No solve implementation is
changed. This isolates allocation-free solve batches from outer harness cost;
it does not retroactively make the original truncated-byte reports exact.
The partial failed report and both follow-ups are preserved. These follow-ups
are allocation diagnostics and are not substituted for the repeated timing
samples in the table.

## Verification and results

Completed regression groups:

- **4,910** normally compiled checks: PFI/upper order and safety tests, existing
  factorization tests, PFI history ownership/reuse, triangular transpose,
  hypersparse update and LU allocation checks.
- **15,689** broader semantic checks with `--compile=min`: primal/dual methods,
  phase transitions, native recovery, postsolve, precision and existing solver
  regressions. Allocation-sensitive checks are separate and normally compiled.
- **100 unique external solves**, five models × five managers × two algorithms ×
  native/Markowitz (305 assertions). Every solve is OPTIMAL, matches its reference
  objective and passes original-model primal feasibility.

New scalar references exercise Float16/Float32/Float64/BigFloat and both rational
precisions; PFI covers both backends, shared copies/refactorization, input/output
aliases, invalid dimensions/indirect indices, cancellation and signed zeros.
Upper tests cover ordinary/stable rows, rotated physical IDs, selected/empty
column sets and the non-last-diagonal fallback. They check exact equality of
ordered arithmetic rather than only an approximate residual.

The initial red attempt also had a test-fixture error (`copy(f)` instead of
`copy_basis_factorization(f)`); it is preserved, not counted as verification.
After fixing the fixture, the second red attempt had 552 passes and the 12
expected mismatch-exception failures before the PFI change. The corrected
production code passed those checks. Upper scalar-reference tests passed before
and after the optimization: preserving their result is the intended behavior.
No numerical solver failure or resource termination is inferred from these
intentional red checks and the fixture error.

The complete project suite was not rerun. Missing reports are never counted as
successful runs. Both full runtime pairs described below completed successfully.

### Full runtime correctness checks

The completed PFI pair reached OPTIMAL with 52,343 iterations and 176
refactorizations in both modes. Objective, every recorded event count, pivot/flip
hash and sampled-state hash match exactly; original primal feasibility passes.
The baseline/current solve times are 251.289/246.937 s, with 0.0613/0.0614 s
compilation and 2.277/2.408 s GC. Cumulative allocation is
9,199,118,664/9,199,112,728 bytes; counts are 82,774,441/82,774,444. Peak process
RSS is 2.394/2.379 GiB. This single pair does not establish an end-to-end speedup;
the tiny cold allocation-count difference does not establish hot-loop overhead.

The original-method BG baseline recorded one failed certification, and a
diagnostic profile observed execution inside the original-LP retry. It ultimately
reached OPTIMAL with 128,742 iterations and 462 refactorizations, passing original
primal feasibility. One SIGUSR1 profiling intervention occurred during this run;
its elapsed time, GC and allocation totals are diagnostic telemetry and are
excluded from performance comparisons. The precise retry trigger was not
captured by the quiet logger.

The optimized BG run also reached OPTIMAL with original primal feasibility.
Both runs have exactly matching objective, event counts, pivot/flip hashes and
sampled-state hashes, including the failed-certification/recovery trajectory.
The optimized solve took 1,387.023 s with 0.0661 s compilation and 54.167 s GC;
its cumulative allocation was 59,074,397,536 bytes in 471,964,210 allocations.
For context only, the profiled baseline recorded 1,394.693 s, 0.0684 s
compilation, 50.975 s GC and 59,074,441,792 bytes in the same allocation count.
These timings do not establish a solver speedup. This change preserves the
existing recovery behavior; it does not repair or explain that certificate
rejection. Both runs stayed below the external watchdog and returned exit code
zero with unchanged pinned sources.



## Evidence audit and independent review

`reproduce/audit.py` verifies the expected Cartesian grids, uniqueness, round
counts, exact output flags, recomputed median ratios, input hashes and reference
objectives, completed process exits and test summaries. It exports compact
reports, all measured timing cells and source/input provenance under `results/`.
The audit covers 22 successful jobs, 240 repeated timing cells, 100 external
solutions, two full runtime pairs, 96 production total-zero-batch cells and
24 isolated HH allocation cells. Two intentional red attempts (including the
first fixture error) and the incomplete HH allocation assertion are retained
separately; none is counted as a passed job.

Independent review found no production correctness blocker and no unnecessary
increase in computational work, allocation or retained memory. Supporting
evidence includes the unique-row invariant audit, six-precision ordered scalar
references, retained indirect PFI bounds checks, the 96 exact total-zero-batch
checks, normally compiled allocation regressions and matching full-solve
trajectories. Review also required the reporting qualifications for short-chain
regressions, measurement dispatch, HH index-only memory savings and the BG
profile intervention. This is a native-Float64 kernel improvement with broader
semantic checks, not a claim of universal speedup across all managers,
precisions, refactorization backends or problems.

After fast-forward integration at `d7aa374`, the 4,910 normally compiled checks
were rerun against `/home/jspitz/JSimplex.jl` and passed, with unchanged pinned
sources and process exit zero. See `results/master-compiled.log` and the
matching process/source-hash record. The subsequent evidence-only commit does
not change production sources or tests.
