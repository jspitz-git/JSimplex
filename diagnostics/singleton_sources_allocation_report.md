# Lazy source maps for singleton-row reduction

Round 33 delays construction of the two bound-source arrays in
`reduce_singleton_rows` until the first removable singleton row. Both candidate
bounds must pass the existing exact-representability checks before allocation.
The arrays remain separate, initialized with `nothing`, and are reused for all
later rows in the pass.

Passes with no singleton rows or only rejected singleton candidates avoid both
arrays. Successful row removal still creates both arrays even when no column
bound tightens, because the postsolve step requires them. Bound arithmetic,
source-row selection, contradictions, result construction, and basis restoration
are unchanged.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times with setup
outside measurement and garbage collection before each sample. Tables report
minimum allocated bytes. All 32 measurements per run recorded zero compilation
time. The baseline includes the preceding 32 allocation rounds.

Runs used `--startup-file=no --compiled-modules=existing --project=dev`. Timings
overlapped validation; no runtime-speedup claim is made. Values are allocated
bytes per call, not peak or retained memory.

The wide-row probe has a 128 × 128 all-ones sparse matrix. The rejection probe
has 128 columns and one row, `3x₁ = 1`; the exact bound `1/3` is not representable
in Float64. All columns are free. Both passes return the original problem.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| No singleton rows | 7,992 | 3,496 | 56.26% | 15 → 9 |
| Rejected singleton | 8,376 | 3,880 | 53.68% | 114 → 108 |

| Model | Singleton pass before → after | Full presolve before → after | Full presolve allocations before → after |
| --- | ---: | ---: | ---: |
| afiro | 16,224 → 16,224 | 1,132,200 → 1,130,360 | 26,665 → 26,657 |
| adlittle | 41,528 → 41,528 | 4,736,184 → 4,733,416 | 117,591 → 117,587 |
| kb2 | 2,944 → 1,408 | 13,130,864 → 13,126,032 | 291,603 → 291,595 |
| sc50a | 3,504 → 1,648 | 4,123,792 → 4,120,272 | 101,704 → 101,692 |
| flugpl | 11,864 → 11,864 | 1,493,928 → 1,492,888 | 38,983 → 38,975 |

The standalone `kb2` and `sc50a` passes save 52.17% and 52.97%, respectively,
and drop from 12 to 8 allocations. Successful standalone passes on the other
three fixtures retain identical bytes and allocation counts. Later passes
within full presolve can avoid source maps on all five models.

| Model | Dual solve before → after | Primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 1,268,216 → 1,266,360 | 1,246,104 → 1,245,288 | 8 |
| adlittle | 5,525,416 → 5,523,352 | 5,801,944 → 5,800,136 | 4 |
| kb2 | 13,584,000 → 13,580,112 | 13,597,920 → 13,593,072 | 8 |
| sc50a | 4,470,272 → 4,467,040 | 4,423,264 → 4,419,552 | 12 |
| flugpl | 1,603,392 → 1,602,976 | 1,648,192 → 1,647,504 | 8 |

Whole solves with presolve show approximately 0.03–0.15% fewer allocated bytes.
These small differences include cross-process variability: unchanged solves
without presolve vary from -400 to +128 bytes with identical allocation counts.
The standalone identity-pass measurements give the clearest evidence.

All ten model snapshots (five fixtures × singleton/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`singleton-sources-allocations-before.toml`](singleton-sources-allocations-before.toml)
and [`singleton-sources-allocations-after.toml`](singleton-sources-allocations-after.toml).

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=reduce_singleton_rows --output=singleton-sources-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
for kind in (:wide, :rejected)
    count = 128
    A = kind == :wide ? sparse(ones(count, count)) :
        sparse([1], [1], [3.0], 1, count)
    problem = LinearProblem(A, ones(count); row_lower=ones(size(A, 1)),
        row_upper=ones(size(A, 1)), column_lower=fill(nothing, count))
    println(measure_allocations(_ -> JSimplex.reduce_singleton_rows(problem); samples=3))
end
```

## Regression coverage

The wide-row budget failed against the original body at 7,992 bytes against a
4,000-byte limit. The rejected-candidate budget failed at 159 allocations
against a 155-allocation limit in the direct test context (the warmed benchmark
records 114 before and 108 after). The 93 new assertions also cover repeated
tightening by negative coefficients, bound-source selection, primal and basis
restoration at both bounds, input preservation, row removal without tightening,
distinct source arrays, and a rejected candidate preceding an accepted one.
Successful cases cover Float32, Float64, BigFloat, and Rational{BigInt}; inexact
rejections use the three floating-point types.

An initial 4,000-byte guard for the rejected candidate passed in isolation but
failed at 4,616 bytes in the full suite. Repeating the preceding 3,025 tests and
then measuring both versions reproduced 4,472–4,616 bytes for the new code,
with a stable 108 allocations; the baseline retained 8,376 bytes and 114
allocations. This exact-arithmetic path therefore uses an allocation-count
guard to check the removed source maps without depending on byte variability.
The initial full run passed the other 17,774 assertions.

Together with the existing singleton-bound and singleton-scan tests, all 264
targeted assertions pass. Independent review found no issue and passed all 93
new assertions. Its 176 baseline differential checks covered zero dimensions,
absent and rejected singletons, unchanged bounds, negative coefficients,
repeated tightening, and contradictions across Float32, Float64, BigFloat, and
rational types. Results, primal restoration, unchanged inputs, and distinct
source maps matched the baseline. Review also independently reran the final
allocation guards: all 93 assertions passed on the new code, while both guards
failed against the renamed baseline at 7,992 bytes and 159 allocations.

The complete mandatory suite passed **17,775/17,775** tests, including the 93
new assertions. `git diff --check` passed. The two previously documented JET
development-suite failures remain outside this round's scope; the full optional
development suite was not rerun.
