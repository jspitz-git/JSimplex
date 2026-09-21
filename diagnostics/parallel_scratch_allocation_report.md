# Lazy interval and representative storage for parallel rows

Round 34 delays two allocations in `reduce_parallel_rows`. The interval cache
is created only when two rows share a normalized signature and require interval
comparison. Distinct supports, different signatures on the same support, and
empty rows need no cache. Once created, the cache retains the existing undefined
entry checks and is reused for all later groups.

The representative-list dictionary now uses a lazy `get!` default. A missing
signature receives its own empty vector; a hit reuses the existing vector
without constructing a discarded default. Signature arithmetic, row ordering,
interval comparisons, failure metadata, and postsolve maps are unchanged.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times with setup
outside measurement and garbage collection before each sample. Tables report
minimum allocated bytes. All 32 measurements per run recorded zero compilation
time. The baseline includes the preceding 33 allocation rounds.

Runs used `--startup-file=no --compiled-modules=existing --project=dev`. Timings
overlapped validation; no runtime-speedup claim is made. Values are allocated
bytes per call, not peak or retained memory.

The unique-support probe uses a 128 × 128 identity matrix. The repeated-signature
probe has 128 identical rows with coefficients `[1, 2, -1]`. Both have a zero
objective and free row and column bounds. The unique-support pass returns the
original problem; the repeated-signature pass retains its first row.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Unique supports | 32,240 | 31,120 | 3.47% | 534 → 532 |
| Repeated signature | 309,360 | 304,192 | 1.67% | 9,274 → 9,147 |

The first probe avoids the interval array and its backing storage. The second
still needs that cache, but avoids 127 discarded representative vectors.

| Model | Parallel pass before → after | Allocations before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 8,336 → 8,064 | 127 → 125 | 1,133,128 → 1,130,168 |
| adlittle | 80,960 → 80,592 | 1,751 → 1,749 | 4,738,024 → 4,733,256 |
| kb2 | 204,560 → 203,120 | 5,301 → 5,299 | 13,128,912 → 13,128,128 |
| sc50a | 28,584 → 28,104 | 543 → 541 | 4,123,568 → 4,121,280 |
| flugpl | 6,016 → 5,808 | 91 → 89 | 1,495,272 → 1,492,952 |

Every standalone reference pass removes two allocations. The byte reductions
range from 0.45% to 3.46%, including variation in exact-arithmetic allocation
sizes. Full presolve and both whole-solve algorithms remove 6 allocations for
afiro, 4 for adlittle, 4 for kb2, 6 for sc50a, and 6 for flugpl.

| Model | Dual solve before → after | Primal solve before → after |
| --- | ---: | ---: |
| afiro | 1,269,208 → 1,266,408 | 1,247,256 → 1,245,576 |
| adlittle | 5,527,368 → 5,523,656 | 5,803,448 → 5,799,672 |
| kb2 | 13,582,848 → 13,580,432 | 13,597,392 → 13,592,400 |
| sc50a | 4,470,096 → 4,465,184 | 4,422,464 → 4,418,208 |
| flugpl | 1,604,896 → 1,602,880 | 1,649,760 → 1,647,296 |

The entire byte difference is not attributed to this change. Unchanged paths
without presolve vary from -128 to +400 bytes with identical allocation counts;
exact arithmetic in presolve introduces further byte variation. The synthetic
probes and consistently reduced allocation counts give the clearest evidence.

All ten model snapshots (five fixtures × parallel/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`parallel-scratch-allocations-before.toml`](parallel-scratch-allocations-before.toml)
and [`parallel-scratch-allocations-after.toml`](parallel-scratch-allocations-after.toml).

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=reduce_parallel_rows --output=parallel-scratch-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
for kind in (:unique, :repeated)
    count = 128
    A = kind == :unique ? sparse(1:count, 1:count, ones(count), count, count) :
        sparse(repeat([1.0 2.0 -1.0], count, 1))
    problem = LinearProblem(A, zeros(size(A, 2)); column_lower=fill(nothing, size(A, 2)))
    println(measure_allocations(_ -> JSimplex.reduce_parallel_rows(problem); samples=3))
end
```

## Regression coverage

Both new budgets failed against the original body: 32,240 bytes against a
31,500-byte unique-support limit, and 9,319 allocations against a 9,250
repeated-signature limit. Both now pass. Direct test instrumentation records 45
more allocations than the warmed benchmark for the second probe; its guard
uses allocation count to avoid exact-arithmetic byte variability.

The 64 new assertions cover both budgets, identity returns, multiple signatures
sharing one support, comparisons after earlier representatives are removed,
tightened bounds, retained row order and names, primal and basis restoration,
input preservation, late contradictions with the original error message,
distinct signatures without interval comparisons, and empty matrix dimensions.
Numeric coverage includes Float32, Float64, BigFloat, and Rational{BigInt}.
Together with existing parallel unit-pivot tests, all 223 targeted assertions
pass.

Independent review found no change-specific issue. It passed all 64 new
assertions and 774 differential assertions across 270 cases and six numeric
types, including Float16 and Rational{Int}. Comparisons covered complete
results, failure metadata, input preservation, postsolve values, and restored
bases. Duplicate-index/explicit-zero CSC inputs reaching a disjoint-bound
failure also matched the baseline.

Review excluded a noncanonical raw CSC case with duplicate row indices that
crashes during retained-row slicing; the same crash was reproduced on the
saved baseline. This existing slicing behavior is outside the storage change.

The complete mandatory suite passed **17,839/17,839** tests, including the 64
new assertions. `git diff --check` passed. The two previously documented JET
development-suite failures remain outside this round's scope; the full optional
development suite was not rerun.
