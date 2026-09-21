# Normalize negative unit parallel bounds by exact negation

Round 68 adds a dedicated negative-unit-pivot path to `_normalized_interval`.
It converts the two bounds exactly, reverses their order, and negates finite
nonzero endpoints. Zero and unbounded endpoints are reused. Dispatch occurs
after the existing unit-pivot shortcut and before the other zero/nonzero paths.
Keeping the new calculation in its own helper preserves the existing local
conversion structure for other pivots. Interval comparisons, representative
selection, contradictions, and postsolve retain their previous behavior.
Stored BigFloat values are converted before negation; input bounds are not
mutated, including their precision and signed zeros.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 67 allocation rounds. All 35 measurements in each run
recorded zero compilation time. Values below are minimum allocated bytes per
call, not peak or retained memory. Timings overlapped validation; no runtime
speedup is claimed.

The probes contain 128 identical rows `[s, 2s, -s]`, three free columns, and a
zero objective. Bounds are the interval between `s` and `6s`, except in the
zero-endpoint target, which lies between zero and `6s`. Both targets have
`s = -1`; controls use `s = 1`, `s = 2`, and `s = -2`. Only the first row is
retained in every case.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Negative unit, nonzero endpoints | 496,864 | 416,848 | 16.10% | 14,907 → 12,859 |
| Negative unit, one zero endpoint | 449,504 | 397,536 | 11.56% | 13,499 → 12,091 |
| Unit pivot | 367,872 | 367,280 | — | 11,067 → 11,067 |
| Positive nonunit pivot | 571,600 | 570,640 | — | 16,699 → 16,699 |
| Negative nonunit pivot | 571,440 | 570,720 | — | 16,699 → 16,699 |

The targets remove 2,048 and 1,408 allocations. All three controls retain their
counts; their small byte differences reflect cross-process exact-arithmetic
allocation variation, so no improvement is claimed for them.

| Model | Parallel pass before → after | Allocations before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 8,064 → 8,064 | 125 → 125 | 827,104 → 825,152 |
| adlittle | 76,576 → 75,376 | 1,638 → 1,638 | 3,617,816 → 3,618,152 |
| kb2 | 182,432 → 182,320 | 4,690 → 4,690 | 11,152,176 → 11,150,576 |
| sc50a | 25,992 → 25,992 | 478 → 478 | 3,060,640 → 3,060,544 |
| flugpl | 5,808 → 5,808 | 89 → 89 | 1,338,976 → 1,338,112 |

| Model | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 963,136 → 962,288 | 942,448 → 941,024 | 0 |
| adlittle | 4,408,776 → 4,407,384 | 4,685,528 → 4,683,640 | 0 |
| kb2 | 11,603,984 → 11,603,040 | 11,618,512 → 11,617,072 | 0 |
| sc50a | 3,406,912 → 3,406,880 | 3,359,376 → 3,359,680 | 0 |
| flugpl | 1,448,536 → 1,448,632 | 1,492,936 → 1,492,856 | 0 |

All five fixtures retain identical allocation counts in the direct parallel
pass, full presolve, and whole solves. The measurements establish a benefit for
the targeted negative-unit cases, not for these fixtures. Unchanged paths without
presolve vary from -144 to +224 bytes with identical allocation counts. Lower
byte totals alone do not establish an improvement when counts remain unchanged.

All ten model snapshots (five fixtures × parallel/full presolve) matched exactly:
CSC arrays, objective and constant, sense, bounds, domains, names, and original
column count. All 20 whole-solve combinations remained `OPTIMAL`, with identical
status, objective, complete primal vector, and iteration count (`isequal`).

Machine-readable results:
[`parallel-negative-bounds-allocations-before.toml`](parallel-negative-bounds-allocations-before.toml)
and [`parallel-negative-bounds-allocations-after.toml`](parallel-negative-bounds-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=reduce_parallel_rows --output=parallel-negative-bounds-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
for kind in (:negative, :zero, :unit, :positive, :nonunit)
    count = 128
    pivot = kind == :unit ? 1.0 : kind == :positive ? 2.0 : kind == :nonunit ? -2.0 : -1.0
    endpoint = kind == :zero ? 0.0 : pivot
    problem = LinearProblem(sparse(repeat([pivot 2pivot -pivot], count, 1)), zeros(3);
        row_lower=fill(min(endpoint, 6pivot), count),
        row_upper=fill(max(endpoint, 6pivot), count), column_lower=fill(nothing, 3))
    println(measure_allocations(_ -> JSimplex.reduce_parallel_rows(problem); samples=3))
end
```

## Regression coverage

Both target allocation guards failed against the original implementation:
14,952 allocations exceeded the 14,000 limit, and 13,507 exceeded 13,000. The
other 92 assertions, including all three controls, passed. All 94 new assertions
now pass as part of 1,146 targeted parallel-row and presolve assertions.
Allocation-count budgets avoid unstable exact-arithmetic byte totals.

Tests cover Float32, Float64, BigFloat, and Rational{BigInt}, positive, negative,
mixed-sign, zero and signed-zero endpoints, one-sided and fully unbounded
intervals, representative replacement, contradictions, postsolve, and input
preservation. BigFloat endpoints stored at 192/256 bits retain their exact values
and precision under 64-bit working precision.

Independent review found no issues and separately passed all 94 new assertions.
Thirty-two saved-baseline scenarios passed 1,052 additional assertions across
the four numeric types. Direct interval comparisons include pivots one, minus
one, two, and minus two; full reductions cover representative selection,
contradictions, postsolve, signed-zero input preservation, and mixed stored
BigFloat precision under 64-bit working precision. Only the baseline interval
and reduction functions were renamed; unchanged helpers remained current.

The full mandatory suite passed all 22,459 assertions in 4m59.1s.
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
