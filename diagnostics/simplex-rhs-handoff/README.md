# Unit right-hand-side handoff

Baseline: `15573547d12c16838abd1c7b93870ee478f6ff5c`.
This is the second bounded change in the shared simplex work investigation.
Production kernel, targeted/semantic and paired solve checks are complete.
The complete project-suite attempt timed out; no full-suite pass or whole-solver
speedup is claimed.

## Scope and numerical contract

A selected tableau row uses a unit right-hand side for BTRAN. The simplex
pipeline materializes this vector for residual checks, then each triangular
manager gathers the same vector through its column permutation. The candidate
passes call-local unit metadata to dense BTRAN for Float32 and Float64. FT, SS,
BG and HH initialize their existing work vector with zeros and set its one live
entry using the inverse permutation they already maintain. BG also maps that
position through its upper-factor row order.

All arithmetic after this initialization, update ordering, prepared-spike
invalidation, residual checks, tolerances, and precision remain unchanged. The
dense RHS is still materialized and passed unchanged to refinement. Generic
RHS inputs, PFI, other precisions, and indexed/hypersparse execution retain the
original path. There is no new public option or adaptive decision.

The metadata is valid only immediately after unit materialization. It is not a
cross-solve cache. Five existing primal/dual callsites provide the known row;
the default pipeline path does not infer unit structure by scanning a vector.

## Work and memory

Frequency: each selected dual row and the corresponding primal row validation
or unshared pricing-weight row. Initialization replaces approximately `m` RHS
reads and `m` column-permutation reads (plus `m` row-order reads for BG) with a
fill of the existing work vector and one indexed store. It retains O(m) writes.
Neither matrix-nonzero traversal nor update-chain arithmetic changes. It adds
no solves, precision conversions, caches, or retained arrays.

The prototype found no benefit for PFI, whose original contiguous copy is
already inexpensive; that manager is deliberately unchanged. Dense-factor
BTRAN is dominated by factor traversal and showed negligible benefit. Do not
interpret the large sparse synthetic cases as a general solver-speed guarantee.

## Reproduction

`reproduce/run.py` runs one Julia process with source/input digests and the
existing 8 GiB VM, 6 GiB free-RAM, and 1 GiB swap guard. `reproduce/probe.jl`
compares full BTRAN including unchanged dense RHS materialization on dense
256-dimensional and sparse 20,000/360,982-dimensional factors, with 0/80/320
updates. Eleven interleaved warmed batches are measured per case. Initialization
and compilation are outside the reported kernel timings. Pass `production` as
the second Julia script argument to measure the installed candidate instead of
the exploratory prototype. Raw attempts remain under
`.superpowers/simplex-rhs-handoff`.

## Completed focused measurements

The installed implementation passed 12,154 targeted checks and 15,689 broader
semantic checks. Twenty warmed tests measure the complete checked pipeline,
including metadata construction, across Float32/Float64, both refactorization
backends, and all five managers: zero allocated bytes. The initial integration
exposed a 32-byte boxing allocation; returning directly from the tagged branch
removed it. The failing attempt is retained alongside its passing regression.

Kernel baseline means the ordinary dense-RHS path in the **same candidate
binary**, not a separately run old checkout. The prototype and installed
candidate were measured separately. Production kernel results below use
Float64/native, Julia 1.13.0 aarch64, one Julia/BLAS thread, and `-O1`.
They include the unchanged dense RHS materialization. All 45 cases were bitwise
equal and allocated zero bytes.

Median unit-handoff time / ordinary BTRAN time, synthetic sparse dimension
360,982 (smaller is better):

| Manager | 0 updates | 80 updates | 320 updates |
| --- | ---: | ---: | ---: |
| PFI | 1.009 | 1.030 | 1.001 |
| FT | 0.902 | 0.944 | 0.928 |
| SS | 0.897 | 0.916 | 0.925 |
| BG | 0.893 | 0.890 | 0.899 |
| HH | 0.912 | 0.922 | 0.932 |

The four optimized managers have 5.57–11.03% lower median times in these wide
sparse kernel cases. Dense dimension-256 cases are essentially unchanged; unchanged PFI
shows timing noise of roughly 3%. Smaller sparse cases and raw batch samples
are retained in the results. No Float32 or Markowitz timing benefit is claimed.
The timings exclude compilation, factor initialization, and update construction;
there is no claim of an equivalent whole-solver speedup or a recovery speedup.

Independent read-only review found no correctness blocker and no unnecessary
scans, solves, copies, conversions, or retained memory. It checked manager
permutations, aliasing, invalidation, precision fallback, pipeline integration,
raw kernel evidence and source manifests. Paired trajectory validation passed; the complete project-suite attempt is
classified separately below.

## Paired trajectory checks

Reused archived candidate reports from `diagnostics/simplex-shared-work/results`
as the baseline after verifying **every recorded source hash** against commit
`1557354`. The reproduction script is unchanged. Comparisons exclude only the
elapsed-time field; all other case fields, including event/state/primal hashes,
objectives, original feasibility, iteration/refactorization counts and numerical
recovery counters are required to match exactly.

- `fast0507.mps`: all five managers, primal and dual, native refactorization,
  interval 80. All ten full solves reached OPTIMAL with original feasibility.
- `medium.mps`: HH/native320, 2,000 primal and 4,000 dual iterations. Both
  reached their planned iteration limits with identical recorded trajectories.
  These are prefixes, not complete medium solves.
- `runtime.mps`: complete HH/native320 dual solve, OPTIMAL, 54,591 iterations,
  194 refactorizations, objective `51425691.76210138`, original feasibility
  verified. All recorded numerical fields match the baseline exactly.

These are correctness/trajectory checks. Their single instrumented elapsed
measurements are not treated as solver-speed estimates. Other managers' full
runtime solves and full medium solves were not repeated for this change.

The independent paired-result audit also checked all 70 baseline source hashes
against `1557354`, candidate source hashes and all 491 candidate preflight pins
against the current files, successful/unchanged-source process records, matching
project/manifest/preferences/reproduction-script hashes, and input hashes.
It found no blocker in the completed evidence. All 64 numerical counters match
in the medium and runtime comparisons.

Timing uncertainty: individual wide-sparse batches include reversals and large
outliers (maximum paired candidate/baseline ratio 1.705 in SS/80). FT/80 was
faster in 7 of 11 interleaved pairs; the other optimized wide-sparse cases were
faster in 10 or 11 pairs. Thus the table reports medians, not a uniform speedup
on every invocation. No causal explanation for the timing outliers is asserted.

## Whole-project attempt and final audit

The normal-compilation command `julia -O1 test/runtests.jl` did not complete.
The existing 600-second wall-time guard terminated only its own process group
(exit 75, elapsed 610.38 s including termination, peak RSS 2,206,520 KiB).
The termination report names `legacy_primal_working_row_scope_tests.jl:25`.
No failed assertion or test error was reported before termination. That file
passed in the 15,689-check semantic run with `--compile=min`. The termination
stack only reports libc frames: this attempt does **not** independently prove
that LLVM compilation caused the delay. It is not counted as a full-suite pass.

`reproduce/audit.py` verifies completed job exits and source pins, every baseline
source hash, the unchanged project environment, all case fields except elapsed
time, and all 45 allocation/equality records before collecting compact reports.
All seven validation processes retained unchanged pinned sources. Six completed
successfully; the whole-project attempt is explicitly recorded as incomplete.
Raw red/green, ambiguity-fix and 32-byte-allocation attempts remain preserved.
No solver tolerance, numerical recovery policy, precision or public configuration
was changed. Full-source independent review and independent paired-data review
found no blocker in the completed evidence; neither claims full-suite coverage.
