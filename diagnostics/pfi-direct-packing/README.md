# Direct packing of PFI eta updates

## Scope and hypothesis

Baseline: `43bb7a0` (`Avoid dense unit-RHS gathers in triangular BTRAN`).
This continues the basis-update/storage performance investigation across managers.
FT/SS/BG already pack their shared upper columns into exact-size arrays; HH also
counts and directly fills its packed updates. PFI counted same-type nonzeros and
allocated/resized to the final capacity, but then shrank both vectors to one entry
and appended every remaining coefficient using `push!`.

For a native `Vector{Float32}` or `Vector{Float64}` matching the factor type, keep
that exact length and write directly into the prepared slots. The prior count and
validated nonzero pivot establish the bounds of the fill loop. All other inputs
retain the original path, including views, mixed scalar types, BigFloat, and exact
arithmetic. This is storage packing only, not an eta sparsification scheme.

## Numerical and work contract

The pivot stays first, followed by nonzero entries in the original index order.
The same `inv(pivot)` and `-(value / pivot)` operations execute, without replacing
division by multiplication. Zero tests, pivot tolerances, validation, conversion
rules, solve arithmetic, refactorization and buffer-retirement policy do not change.

The affected frequency is one accepted PFI column replacement. There are still
exactly two input scans for same-type arrays (count and fill), no extra solves,
conversions, copies, or metadata. Storage stays O(nnz(direction)), with identical
capacity and lifetime. The optimization removes two length reductions and two
append operations per nonpivot stored coefficient. It does not alter the number
or density of eta entries or the cost of applying a long update chain.

Native vectors have stable length and primitive scalar reads during packing;
there are no user-defined indexing/conversion callbacks in the bounds-free loop.
General AbstractVector inputs and other precisions keep checked original behavior.
The existing ownership policy prevents recycling active or shared update buffers.

## Measurement protocol

`reproduce/reference.jl` freezes the baseline packing function. `bench.jl` compares
it with a diagnostic prototype or production in one warmed process, with 11
interleaved sample pairs per case. Compilation and fixture creation precede timing.
The 24 cases cover Float32/Float64, dimensions 4,132 / 20,000 / 360,982, sparse
(approximately 1% support) and dense (approximately 94% support) inputs, and both
fresh allocation and recycled buffers. Every case checks packed coefficients and
indices exactly before measuring. Each batch immediately returns updates to a private pool in recycled cases or
discards them in fresh cases, to bound memory.
It does not empty the vectors as real refactorization retirement does. This
identical bookkeeping is included in both timings; real retirement and capacity
reuse are exercised separately by the regression tests.

The fixture has a dimension-only backend: **no LU or solve is performed**. These
are packing-kernel measurements, not evidence for whole-solver speedups. Small
amortized timing-harness allocations can appear in short batches; dedicated
allocation tests check actual warmed replacement calls separately.

The first checked direct-fill prototype slowed sparse inputs by about 20–31%
while helping dense inputs. It was rejected. Restricting the bounds-free loop to
ordinary Float32/Float64 vectors removed that regression in the measured cases.
Production keeps all other original paths. Raw attempts, including the rejected
prototype, remain in `.superpowers/pfi-direct-packing/`.

`reproduce/validate.py` runs tests and paired solves sequentially under `run.py`:
one Julia/BLAS thread, 8 GiB VM, 6 GiB available-RAM floor, 1 GiB swap ceiling.
Sources, inputs and environments are hashed before/after each job. Paired solves
compare PFI on baseline and candidate for fast0507 (both algorithms), medium
(primal 2,000 / dual 4,000 iteration prefixes), and a full runtime dual solve.
They retain steepest edge, legacy, native refactorization, presolve/scaling defaults,
partial pricing off and integrality relaxation. Intervals: fast0507 80, others 320.
Solver time limit is infinite; the external validation guard is 1,800 seconds.
Event hashes include chosen pivots and steps; state hashes sample basis, variable
states, primal values, reduced costs, costs and pricing weights every 80 iterations
and at termination. Full solutions also check original feasibility/objective.

## Independent code review

The `pfi_packing_review` review found no blocking correctness issue and no
unnecessary added work, allocation or retained memory. It checked the bounds
argument, the private recycled-buffer lifetime, scalar-operation identity, and
unchanged fallback paths. It independently read the 24-case production kernel
report. It explicitly cautioned that the synthetic pack-only timings exclude
refactorization and cannot establish a whole-solver speedup. Final trajectory
and validation results are reported separately below.

## Initial production kernel results (`-O1`)

Across all 24 cases, median new/old elapsed ratios were 0.920–0.948 for sparse
support and 0.397–0.523 for dense support. Median allocated bytes matched in every
case. Representative recycled Float64 cases (microseconds per pack):

| Dimension | Support | Baseline | Candidate |
| ---: | :--- | ---: | ---: |
| 4,132 | Sparse | 3.082 | 2.894 |
| 4,132 | Dense | 7.176 | 3.231 |
| 20,000 | Sparse | 13.938 | 12.972 |
| 20,000 | Dense | 33.999 | 15.363 |
| 360,982 | Sparse | 278.900 | 264.380 |
| 360,982 | Dense | 629.860 | 305.400 |

The absolute savings are small relative to full simplex work. These measurements
do not address the large runtime gap against other solvers. In the paired
fast0507 and medium prefix solves, overall timings did not establish a speedup:
they are single, instrumented executions including cold solver compilation.
Their role is numerical trajectory validation, not throughput measurement.

## Final validation

- 4,176 targeted assertions passed, including 724 new packing/order and solve
  checks across five scalar types, native/Markowitz backends, vectors/views,
  dense/sparse histories, pivot positions and buffer reuse. Existing mixed-type
  conversion, BigFloat precision, copy isolation, rejected-update and allocation
  tests passed. The new semantic cases also passed on the unchanged baseline;
  this optimization is intended to change cost, not behavior.
- 15,689 broader semantic assertions passed with `--compile=min`. Allocation and
  kernel checks ran with normal compilation. This is not a fresh pass of the
  entire project suite; no such claim is made.
- Five paired cases matched exactly in all recorded fields except elapsed time:
  event hashes (pivots/steps), sampled and final state hashes, diagnostic counts,
  iterations/refactorizations, terminal status, and, for optimal runs, objective,
  final primal hash and original feasibility.

| Case | Algorithm | Status | Iterations | Refactorizations |
| :--- | :--- | :--- | ---: | ---: |
| fast0507 | Primal | OPTIMAL | 4,923 | 63 |
| fast0507 | Dual | OPTIMAL | 7,346 | 92 |
| medium prefix | Primal | ITERATION_LIMIT (planned) | 2,000 | 7 |
| medium prefix | Dual | ITERATION_LIMIT (planned) | 4,000 | 12 |
| runtime full | Dual | OPTIMAL | 52,343 | 176 |

Both full runtime solves returned `51425691.76210445` with original feasibility.
Instrumented solver times were 315.28 s (baseline) and 317.31 s (candidate),
which do not establish a whole-solver speedup. Medium prefixes do not establish
convergence of medium. Runtime primal was not run.

The additional 24-case warmed `-O2` comparison confirmed the kernel savings:
new/old medians were 0.866–0.916 for sparse support and 0.336–0.453 for dense
support, again with identical median allocated bytes. No new buffer is retained.
Together with the `-O1` comparison, this supports the local optimization, not a
change in simplex trajectories or a claim about total solver speed.

`reproduce/audit.py` checks all nine sequential validation jobs and the additional
`-O2` job exited successfully with unchanged pinned inputs. It verifies all
reported source hashes against baseline `43bb7a0` or the candidate tree, checks
input hashes, compares the paired numerical results and archives compact reports
in `results/`. Original logs, preflights, and rejected prototype attempts remain
under `.superpowers/pfi-direct-packing/`. The rejected prototype source is also
archived with a hash matching its original preflight.

The final independent review also verified the ten process records, 70 source
hashes, frozen baseline function, assertion counts, all five numerical pairs,
both production kernel reports and the rejected prototype provenance. It found
no blocker for integration.
