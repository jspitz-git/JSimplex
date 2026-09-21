# Presolve row-entry allocation audit

Round 18 reduces repeated growth of the vectors built by `_row_entries`, which
is used by seven presolve passes. The helper still returns independent mutable
vectors of `(column, value)` tuples, ordered by column and excluding zero values.

For matrices with more stored entries than rows, the helper now counts nonzeros
per row and allocates each result vector at its final length. It reuses the
counting array as write positions. For matrices with at most one stored entry per
row on average, it retains the previous single-pass `push!` implementation to
avoid allocating a row-count array. Both paths traverse only active CSC storage.

This is an allocation tradeoff rather than a universal improvement. Short rows
can fit within the first growth allocation of the old implementation, and a large
number of explicit zeros can make the stored-entry heuristic overestimate the
benefit. No coefficient arithmetic or conversion was added.

## Method

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native
basis factorization with PFI updates. Each case was warmed twice and sampled
three times, with input setup outside measurement and garbage collection before
each sample. Tables show minimum allocated bytes. All 35 measurements in each
run recorded zero compilation time. The baseline includes the preceding 17
allocation rounds.

Runs used `--startup-file=no --compiled-modules=existing --project=dev`. Timings
overlapped validation, so no runtime-speedup claim is made. Allocation totals are
per call, not peak or retained memory.

## Results

| Synthetic CSC input | Before | After | Reduction |
| --- | ---: | ---: | ---: |
| Dense 128 × 128 | 395,360 | 273,600 | 30.80% |
| 128 singleton rows | 15,456 | 15,456 | unchanged |
| Empty 128 × 128 | 5,216 | 5,216 | unchanged |
| 1,000 rows with only two entries | 40,232 | 40,232 | unchanged |
| 128 stored zeros in one column | 5,216 | 5,216 | unchanged |

The dense probe reduced allocation count from 770 to 388. The four sparse probes
retain the original path, including its allocation counts.

| Model | Row entries before | Row entries after | Reduction | Full presolve before | Full presolve after | Reduction |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| afiro | 4,704 | 3,600 | 23.47% | 1,204,952 | 1,187,016 | 1.49% |
| adlittle | 20,320 | 10,864 | 46.54% | 5,036,824 | 4,906,184 | 2.59% |
| kb2 | 18,112 | 8,128 | 55.12% | 13,335,344 | 13,200,704 | 1.01% |
| sc50a | 7,408 | 6,208 | 16.20% | 4,345,712 | 4,327,040 | 0.43% |
| flugpl | 2,224 | 2,304 | **-3.60%** | 1,510,784 | 1,513,536 | **-0.18%** |

Negative reductions indicate increased allocations. In flugpl, every row has
one to three nonzeros: the extra counting array outweighs savings from exact
vector sizes by 80 bytes per direct helper call. Repeated calls make full
presolve allocate 2,752 additional bytes. The heuristic is deliberately simple;
it does not attempt to predict Julia's vector growth for each row distribution.

Whole solves with presolve enabled allocated 0.39–2.25% fewer bytes on the four
improving models. Flugpl whole solves allocated 0.21–0.22% more. With presolve
disabled, byte totals varied by -80 to +272 bytes with unchanged allocation
counts; this variation is not attributed to the change.

All five row-entry outputs matched their serialized baseline exactly. All 20
whole-solve combinations (five models, primal/dual, presolve on/off) remained
`OPTIMAL`; status, objective, complete primal vector, and iteration count matched
baseline snapshots exactly with `isequal`.

Machine-readable results are in
[`row-entries-allocations-before.toml`](row-entries-allocations-before.toml) and
[`row-entries-allocations-after.toml`](row-entries-allocations-after.toml).

## Reproduction

For full presolve and whole solves:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=presolve --output=row-entries-audit.toml
```

For the helper, run from the repository root with the same Julia flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays

problem = read_mps("test/fixtures/solver/netlib/adlittle.mps")
println(measure_allocations(_ -> JSimplex._row_entries(problem.A); samples=3))
matrix = sparse(ones(128, 128))
println(measure_allocations(_ -> JSimplex._row_entries(matrix); samples=3))
```

## Regression coverage

The dense allocation budget failed before the change at 395,360 bytes against a
300,000-byte limit and now passes at 273,600 bytes. Three additional budgets
protect the empty, mostly empty, and single-column stored-zero inputs.

The 61 new checks cover both paths, column ordering, explicit and signed zeros,
spare CSC backing storage, independent row buffers and calls, unchanged inputs,
empty dimensions, numeric types, and preservation of stored BigFloat precision
when called under a lower ambient precision. Numeric coverage includes Float32,
Float64, BigFloat, and Rational{BigInt}.

Independent review found no correctness issue. Its 180 differential cases across
six numeric types matched the original implementation, including padded storage
and independent row buffers. Consumers do not depend on spare vector capacity.
Review also measured the heuristic's explicit-zero limitation: a 128 × 128 matrix
with all 16,384 entries stored as zeros increased from 5,216 to 6,336 bytes.

The complete mandatory suite passed **15,783/15,783** tests, including the 61 new
checks. `git diff --check` passed. The two previously documented JET
development-suite failures remain outside this round's scope; the full optional
development suite was not rerun.
