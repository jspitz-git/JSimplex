# S4-L: HH symbolic reuse cost and memory measurement contract

SOURCE/EVIDENCE ONLY. No Julia, numerical component, factor, workspace or public
solver calls. Production, tests and CI remain identical to master 0eb75c3;
conditional symbolic reuse remains diagnostic only. This report specifies a future
measurement, not a measured improvement or production acceptance.

## Evidence and provenance

Read-only reuse: S4-B's `S4-COMPONENTS.md` and component driver; S4-C's
`S4-TRIPLETS.md` and paired triplet driver; S4-D's scalar component report/driver.
Their recorded runs are evidence of the stated protocols, not new executions here.
B's separate backend/extraction/whole timings cannot be added into a lifecycle
estimate. C's mostly-zero256 side median 1.0258 is not a speedup. D's preserved
Serialization/hash failure is not repaired by its later canonical probe. None of
these scripts or measurements was rerun.

Installed sources: `src/huangfu_hall_factorization.jl`, `src/factorization.jl`,
Julia 1.13.0 SparseArrays `solvers/umfpack.jl`, generated `wrappers.jl`,
`base/abstractarray.jl` and `sparsematrix.jl`. The source inventory pins them and
all repository src/test files, the six user files and the known native libraries.
These are L read-time hashes, not numerical launch pins or exhaustive loader proof.

No UMFPACK header was found in the searched Julia include, artifact and system
include trees. The preserved versioned upstream
[SuiteSparse v7.10.1 header](https://raw.githubusercontent.com/DrTimothyAldenDavis/SuiteSparse/v7.10.1/UMFPACK/Include/umfpack.h)
documents UMFPACK 6.3.5, matching the installed generated version constants and
library filename. It is **not an installed header or proof of binary build inputs**.
The original header and URL/hash provenance are in results/S4-L. Initial split-header
URLs were unavailable; no numeric action depended on those attempts.

## Work at the proposed boundary

Only whole `refactorize!(::HuangfuHall, B)` is timed. Both sides still copy incoming
CSC values/indices into native-owned storage, compute numeric LU, extract and
validate factors/scaling, materialize HH-owned base arrays, publish and retire old
HH state. No update history is populated in this cost probe; update-chain scaling
is not measured. G's old nonempty history boundary is reused, not repeated.

The candidate adds one `_same_umfpack_pattern` check per refactor: dimensions and
lengths, then n+1 column pointers and nnz row indices for these matching patterns.
It does not scan coefficients, add a basis solve, or cache mutable pattern results.
Source calls convert twice versus once on the reference route. For the frozen
`SparseMatrixCSC{Float64,Int64}` input on this 64-bit host, AbstractArray's
`convert(::Type{T}, a::T)=a` returns the input itself. Those conversions do not copy
CSC arrays; this does not make the pattern scan free. Calling the CSC constructor
instead is a different operation which may copy. Other types/conversions are excluded.

Reference rebuilds symbolic and numeric state. Candidate retains the initial
symbolic state when its actual guard succeeds and still rebuilds numeric state.
Symbolic construction receives values; different numeric trajectories remain
possible even with equal index arrays. Identical input, default control, q=nothing,
IRSTEP=0 and successful residual checks do not establish value-independent quality.
All extraction orientation checks remain enabled: up to one native validation
solve per successful extraction, a SOURCE-DERIVED bound rather than an observed
count. No extra component replay will be used to attribute whole-window savings.

## What memory measurements mean

| Observable | Unit / lifetime | Valid interpretation and limitation |
| --- | --- | --- |
| `@timed.bytes`, `Base.gc_alloc_count(stats.gcstats)` | Julia-accounted bytes / allocation events in window | Traffic, not retained heap; native malloc traffic is not fully covered |
| `@timed.time`, `gctime`, compile/recompile time | seconds in window | Include GC actually incurred; never subtract GC or compilation to manufacture speedup |
| `Base.summarysize` of four current HH roots | bytes in traversed Julia object graph | Deduplicated across roots; excludes pointed-to native allocations, allocator capacity and unrelated process roots |
| UMFPACK `SIZE_OF_UNIT` | bytes per native Unit | Multiply size fields by this captured value, not a hardcoded machine word |
| `SYMBOLIC_SIZE` / `SYMBOLIC_PEAK_MEMORY` | Units; final object / symbolic phase peak | Reported native algorithm sizes, not a live-process allocation ledger |
| `NUMERIC_SIZE_ESTIMATE` / `PEAK_MEMORY_ESTIMATE` | Units; symbolic estimates | Not guaranteed upper bounds; candidate symbolic-origin fields retain initial-analysis provenance |
| `NUMERIC_SIZE` / `PEAK_MEMORY` | Units; final numeric object / native algorithm peak | Do not include all simultaneously alive retired wrappers or total process memory |
| `VARIABLE_PEAK` | Units used inside numeric variable block | Not allocated block size; never equate with malloc bytes |
| `/proc/self/status` VmRSS, VmHWM, VmSize, VmPeak | Linux kB (=1024 bytes) | Whole process, allocator/JIT/Julia/native mixed; high water cannot fall and RSS alone cannot prove release or a leak |

Generated constants are C zero-based indices; Julia indexes `info[index+1]`.
Pin the mapping SIZE_OF_UNIT=3, SYMBOLIC_PEAK_MEMORY=13, SYMBOLIC_SIZE=14,
NUMERIC_SIZE_ESTIMATE=20, PEAK_MEMORY_ESTIMATE=21, NUMERIC_SIZE=40,
PEAK_MEMORY=41, VARIABLE_PEAK=46. Copy scalar values from the mutable info buffer
outside windows before any later native activity and label their origin. Do not
interpret cached symbolic timing fields as work executed in the latest call.
Do not call show_umf_info: it temporarily mutates control.

Native Numeric and Symbolic wrappers have finalizers that call their respective
native free routines. Reference `lu!` replaces the symbolic wrapper; numeric LU
creates a new object before replacing the old numeric wrapper. Old and new storage
can overlap, and unreachable objects can await GC/finalizers. HH state publication
similarly replaces extracted arrays. A shallow UmfpackLU copy shares native owners
and cannot be used as a private memory control. No retired owner, shallow factor
copy, old-base identity snapshot or closure over such state may survive a sample.
Explicit `GC.gc(true)` outside windows encourages collection but is not proof that
all native frees ran or that allocator pages returned to the OS. Do not manually
free/finalize live native wrappers.

**Native retention remains OPEN.** Available source/info/RSS/summarysize evidence
cannot certify a globally bounded native allocation balance. The next probe bounds
its own roots and observes process trends; it cannot close the production native
retention gate. A future true allocation/free ledger or equivalent supported native
accounting would need its own justified plan. Do not infer it from flat RSS.

## Future experiment and acceptance scope

The separate S4-M plan freezes two NEW 96x96 finite dyadic fixtures, exact value
schedule and RHS, four factors, 128 warmup and 512 measured refactors, and 88 direct
HH solves. Whole-window repeated pairs, compile-zero measurements and exact offline
residuals separate correctness from speed observations. No old tiny lifecycle,
corpus, medium or full-suite rerun is needed. No constructor or solve is hidden by
disabled counters. Input preparation, diagnostics, endpoint solves, serialization,
explicit GC and graph inspection are outside timing and separately counted.

There is no new production computational work or memory cost in L. The proposed
candidate scan costs O(n+nnz) at refactor frequency, versus avoided symbolic work
whose amount depends on sparsity and native ordering. Extraction/numeric work may
also change; differing factor/output fingerprints prohibit a kernel-only attribution.
The bounded plan is needed because source inspection and earlier tiny identity
checks cannot establish representative lifecycle benefit. No benchmark is run for
this documentation change. Broader consumers, controls, precisions, platforms,
fullsuite and all historical rejection decisions stay open/unchanged.

## Offline verification

`source_contract.py` completed 36/36 source/exact-input checks with 527 read-time
hashes. A separate author `independent_check.py` rehashed all 527 and passed all
15 checks, including all eight RHS bit/rational pairs, six user hashes, actual
local/remote refs and full previous process groups. These are offline checks, not
new numerical runtime assertions. Both scripts use exclusive output and must not
be rerun. HEAD 457d4c0/master 0eb75c3 matched remotes; groups12358/12360 and Julia
were absent, boot dade7243-9103-4398-bb45-fa28fbc0be72.
