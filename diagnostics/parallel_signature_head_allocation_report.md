# Construct the leading normalized coefficient directly

Round 48 constructs an exact one for the first coefficient of a nonunit-pivot
parallel-row signature. The pivot comes from a nonzero row entry, so its ratio
to itself is exactly one. This avoids reconverting that stored coefficient and
dividing it by the pivot. Remaining coefficients retain their original exact
conversion and division, and the existing unit-pivot path is unchanged.

The shortcut uses iteration position, independent of the stored column index.
Signature contents, support grouping, interval normalization, representative
selection, contradictions, and postsolve behavior are unchanged.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 47 allocation rounds. All 33 measurements in each run
recorded zero compilation time. Values below are minimum allocated bytes per
call, not peak or retained memory. Timings overlapped validation; no runtime
speedup is claimed.

Each probe has 128 identical rows proportional to `0 ≤ x + 2y - z ≤ 6`, free
columns, and a zero objective. Positive and negative nonunit probes use pivots
2 and -2, with corresponding scaled bounds. The control uses pivot 1. Parallel
reduction retains the first row in all cases.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Pivot 2 | 595,152 | 519,936 | 12.64% | 17,467 → 15,291 |
| Pivot -2 | 596,512 | 521,664 | 12.55% | 17,467 → 15,291 |
| Pivot 1 | 403,136 | 403,952 | — | 12,219 → 12,219 |

Each nonunit probe removes 2,176 allocations. The unit-pivot control retains
identical allocation counts; its 816-byte difference is allocator variation.

| Model | Parallel pass before → after | Allocations before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 8,064 → 8,064 | 125 → 125 | 986,032 → 984,784 |
| adlittle | 80,720 → 78,808 | 1,749 → 1,698 | 3,818,328 → 3,811,400 |
| kb2 | 202,448 → 190,344 | 5,299 → 4,942 | 12,452,264 → 12,423,480 |
| sc50a | 28,104 → 26,352 | 541 → 490 | 3,934,448 → 3,926,768 |
| flugpl | 5,808 → 5,808 | 89 → 89 | 1,376,880 → 1,373,728 |

Three direct fixture passes allocate 2.37–6.23% fewer bytes. Afiro and flugpl
retain identical direct-pass measurements. Earlier presolve passes expose
nonunit parallel rows on those models, so complete presolve benefits on all five.

| Model | Dual solve before → after | Primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 1,120,832 → 1,120,496 | 1,100,672 → 1,099,072 | 34 |
| adlittle | 4,607,704 → 4,601,496 | 4,884,264 → 4,877,800 | 136 |
| kb2 | 12,904,104 → 12,878,536 | 12,917,816 → 12,893,064 | 714 |
| sc50a | 4,280,112 → 4,272,416 | 4,232,736 → 4,224,992 | 204 |
| flugpl | 1,487,592 → 1,484,520 | 1,531,416 → 1,529,224 | 68 |

Whole solves with presolve record approximately 0.03–0.21% fewer bytes.
Full presolve removes the same number of allocations as each whole solve.
These byte changes are small relative to cross-process exact-arithmetic
variation, so allocation counts provide the clearer evidence. Unchanged paths
without presolve vary from -272 to +48 bytes with identical allocation counts.

All ten model snapshots (five fixtures × parallel/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`parallel-signature-head-allocations-before.toml`](parallel-signature-head-allocations-before.toml)
and [`parallel-signature-head-allocations-after.toml`](parallel-signature-head-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=reduce_parallel_rows --output=parallel-signature-head-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
for pivot in (2.0, -2.0, 1.0)
    count = 128
    A = sparse(repeat(reshape([pivot, 2pivot, -pivot], 1, 3), count, 1))
    problem = LinearProblem(A, zeros(3); row_lower=fill(min(0.0, 6pivot), count),
        row_upper=fill(max(0.0, 6pivot), count), column_lower=fill(nothing, 3))
    println(measure_allocations(_ -> JSimplex.reduce_parallel_rows(problem); samples=3))
end
```

## Regression coverage

The allocation guard failed against the original implementation: 17,512
allocations exceeded the 16,000 limit, while the other 101 assertions passed.
All 102 new assertions now pass, as do all 476 targeted parallel-row assertions
together. Direct instrumentation includes 45 allocations beyond the warmed
benchmark. Allocation-count budgets avoid unstable exact-arithmetic byte totals.

The new tests cover signed and fractional pivots, noncontiguous column indices,
one-term signatures, vector and tuple inputs, proportional versus distinct rows,
contradictions, postsolve values, and original input preservation across Float32,
Float64, BigFloat, and Rational{BigInt}. Stored 256-bit BigFloat coefficients
retain their exact normalized ratios under 64-bit working precision. Existing
targeted tests cover unit pivots, zero and unbounded row endpoints, overlapping
intervals, representative replacement, and restored bases.

Independent review found no issues and separately passed all 102 new assertions.
Thirty-two comparisons with the original implementation passed 476 assertions
across all four numeric types, including single-term and noncontiguous supports,
tuple and restartable generator inputs, grouping, overlap, contradictions,
postsolve, and input preservation. Six additional assertions checked stored
BigFloat precision. Its separate warmed probe also removed 2,176 allocations.
Invalid zero pivots and stateful iterators are outside the production caller's
nonzero row-entry vector contract.

The full mandatory suite passed all 19,945 assertions in 4m46.8s.
`git diff --check` passed. The two previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
