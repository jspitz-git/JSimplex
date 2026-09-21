# Negate endpoints for negative unit dependency weights

Round 64 replaces exact rational multiplication by minus one with negation in
`_implied_interval`. Each finite, nonzero endpoint is converted once and then
either reused for a unit weight, negated for a negative unit weight, or multiplied
by another weight. Endpoint selection, lazy weight negation, zero-bound guards,
unboundedness, and interval accumulation retain their previous behavior.
Arithmetic does not mutate the model's bounds or the dependency proof.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 63 allocation rounds. All 34 measurements in each run
recorded zero compilation time. Values below are minimum allocated bytes per
call, not peak or retained memory. Timings overlapped validation; no runtime
speedup is claimed.

The probes contain 128 proportional rows and three free columns with zero
objective. The first row is `[1, 2, -1]`; subsequent rows are its multiple by
`s`. Bounds are the correspondingly scaled interval `[1, 6]`, except in the
zero-bound control where all endpoints are zero. Only the first row is retained.
The target uses `s = -1`; controls use `s = 1`, `s = -2`, and zero bounds with
`s = -1`.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Negative unit weight | 694,488 | 623,336 | 10.25% | 17,755 → 15,977 |
| Unit weight | 598,912 | 600,144 | — | 15,215 → 15,215 |
| Nonunit negative weight | 737,896 | 738,936 | — | 18,898 → 18,898 |
| Zero endpoints | 481,168 | 481,648 | — | 11,151 → 11,151 |

The target removes 1,778 allocations. All controls retain their counts; their
small byte increases reflect cross-process exact-arithmetic allocation variation.

| Model | Dependency pass before → after | Allocations before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 198,704 → 198,928 | 4,272 → 4,272 | 831,344 → 831,824 |
| adlittle | 720,472 → 721,432 | 16,762 → 16,762 | 3,625,672 → 3,626,600 |
| kb2 | 3,467,728 → 3,467,760 | 80,025 → 80,025 | 11,168,408 → 11,166,832 |
| sc50a | 1,330,952 → 1,332,616 | 31,066 → 31,066 | 3,063,488 → 3,063,904 |
| flugpl | 183,680 → 184,320 | 3,830 → 3,830 | 1,341,824 → 1,342,400 |

The standalone dependency passes retain identical allocation counts on these
fixtures. The full presolve pipeline encounters different rows and removes
14 allocations on afiro and 49 on kb2; the other three fixtures retain their
counts.

| Model | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 968,096 → 967,296 | 946,096 → 947,040 | 14 |
| adlittle | 4,416,904 → 4,415,800 | 4,692,904 → 4,692,408 | 0 |
| kb2 | 11,621,448 → 11,619,520 | 11,635,544 → 11,633,536 | 49 |
| sc50a | 3,410,096 → 3,409,168 | 3,363,024 → 3,362,192 | 0 |
| flugpl | 1,451,160 → 1,451,784 | 1,495,960 → 1,496,104 | 0 |

Full presolve removes the same number of allocations as each whole solve.
The fixture savings are small compared with byte variation: afiro's primal
solve and full presolve allocate slightly more bytes despite fewer allocations.
Unchanged paths without presolve vary from -528 to +208 bytes with identical
allocation counts. Counts provide the clearer evidence for small fixture
differences; no improvement is claimed where counts remain unchanged.

All ten model snapshots (five fixtures × dependency/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`dependent-negative-weights-allocations-before.toml`](dependent-negative-weights-allocations-before.toml)
and [`dependent-negative-weights-allocations-after.toml`](dependent-negative-weights-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=reduce_dependent_rows --output=dependent-negative-weights-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
for kind in (:negative, :unit, :nonunit, :zero)
    count = 128
    scale = kind == :unit ? 1.0 : kind == :nonunit ? -2.0 : -1.0
    multipliers = [1.0; fill(scale, count-1)]
    problem = LinearProblem(sparse(multipliers * [1.0 2.0 -1.0]), zeros(3);
        row_lower=kind == :zero ? zeros(count) : min.(multipliers, 6multipliers),
        row_upper=kind == :zero ? zeros(count) : max.(multipliers, 6multipliers),
        column_lower=fill(nothing, 3))
    println(measure_allocations(_ -> JSimplex.reduce_dependent_rows(problem); samples=3))
end
```

## Regression coverage

The target allocation guard failed against the original implementation:
17,800 allocations exceeded the 16,500 limit. The other 139 assertions,
including all three controls, passed. All 140 new assertions now pass as part
of 2,198 targeted dependency assertions. Allocation-count budgets avoid unstable
exact-arithmetic byte totals.

Tests cover Float32, Float64, BigFloat, and Rational{BigInt}, positive and
negative endpoints, multiple signed contributions, fractional and nonunit
weights, one-sided and zero intervals, ignored zero/current proof entries,
row removal, contradictions, postsolve, and preservation of inputs.

Independent review found no issues and separately passed all 140 new assertions.
Thirty-two saved-baseline scenarios passed 248 additional assertions, comparing
direct implied intervals and complete reductions, including eight contradictions.
The four numeric types include BigFloat endpoints stored at 53/128/256/384 bits
under 64-bit working precision. Input and combination preservation, full result
snapshots, and postsolve outputs matched the baseline.

The full mandatory suite passed all 21,971 assertions in 4m46.8s.
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
