# Skip bound proofs for free aggregation pivots

Round 29 adds an early return to `_equality_implies_column_bounds` when both
bounds of the pivot column are unbounded. There are no column bounds to prove in
this case. The helper previously converted the other coefficients and computed
exact minimum/maximum activities before returning the same answer.

One-sided and finite pivot bounds retain the original proof. Aggregation still
checks objective, matrix, and shifted-row-bound representability before committing
an elimination. Pivot selection, postsolve records, and basis restoration are
unchanged.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times with setup
outside measurement and garbage collection before each sample. Tables report
minimum allocated bytes. All 37 measurements per main run recorded zero
compilation time. The baseline includes the preceding 28 rounds.

Runs used `--startup-file=no --compiled-modules=existing --project=dev`. Timings
overlapped validation; no runtime-speedup claim is made. Values are allocated
bytes per call, not peak or retained memory.

The repeated-update probe from the
[aggregation-default report](aggregation_defaults_allocation_report.md) has 64
equalities `xᵢ + y = 1`, free variables, objective `sum(xᵢ) + 2y`, and one additional
row `sum(xᵢ) + 2y ≤ 100`. Sparse aggregation fell from **670,416 to 598,448 bytes
(10.73%)**, and from 17,918 to 15,486 allocations. The unchanged singleton probe
retained 8,950 allocations; its bytes varied from 356,168 to 353,416.

A separate same-process comparison used the saved baseline helper body alongside
the current helper. Its eight-term row has a free pivot and seven peer variables,
either free or bounded to `[0,1]`. All four measurements used the same warmup and
sampling policy and recorded zero compilation time.

| Helper case | Before | After | Allocations before → after |
| --- | ---: | ---: | ---: |
| Free peers | 4,792 | 0 | 158 → 0 |
| Bounded peers | 20,720 | 0 | 550 → 0 |

All five reference fixtures retained identical allocation counts in singleton
aggregation, sparse aggregation, full presolve, and whole solves. These fixtures
do not demonstrate an allocation-count benefit from the shortcut. Small byte
differences are not attributed to the change: for example, kb2 full presolve
increased by 576 bytes, while unchanged whole-solve paths without presolve varied
from -224 to +496 bytes. The measured benefit is specific to the free-pivot cases
above.

All 15 model snapshots (five fixtures × singleton/sparse/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`aggregation-free-bounds-allocations-before.toml`](aggregation-free-bounds-allocations-before.toml),
[`aggregation-free-bounds-allocations-after.toml`](aggregation-free-bounds-allocations-after.toml),
and [`aggregation-free-bounds-helper.toml`](aggregation-free-bounds-helper.toml).

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-free-bounds-audit.toml
```

For the full-pass probe, use the `aggregation_probe` example in the
[aggregation-default report](aggregation_defaults_allocation_report.md#reproduction)
with `sparse_pass = true`. For the helper, run from the repository root with the
same Julia flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
for bounded_peers in (false, true)
    problem = LinearProblem(sparse(ones(1, 8)), zeros(8);
        row_lower=[6.0], row_upper=[6.0],
        column_lower=[nothing; fill(bounded_peers ? 0.0 : nothing, 7)],
        column_upper=[nothing; fill(bounded_peers ? 1.0 : nothing, 7)])
    terms = [(column, 1.0) for column in 1:8]
    pivot, rhs = big(1)//1, big(6)//1
    println(measure_allocations(_ -> JSimplex._equality_implies_column_bounds(
        problem, terms, 1, pivot, rhs); samples=3))
end
```

## Regression coverage

Both direct-call allocation tests failed before the change at 4,600 and 22,240
bytes against a 64-byte budget, and now pass. Their call context differs from
the warmed helper measurements above.

The 226 new checks cover both budgets, free/one-sided/finite pivot bounds,
bounded and unbounded peer variables, positive and negative unit/nonunit pivots,
reduced models, primal and basis restoration, and deep-copied input preservation.
Numeric coverage includes Float32, Float64, BigFloat, and Rational{BigInt}. All
513 targeted assertions pass when combined with the preceding aggregation
default and scratch-buffer tests.

Independent review found no issue. Its 720 differential cases across six numeric
types matched the baseline and preserved inputs, including free, one-sided, and
bounded variables with positive and negative pivots. It independently passed all
226 new assertions.

The complete mandatory suite passed **17,337/17,337** tests, including the 226 new
checks. `git diff --check` passed. The two previously documented JET
development-suite failures remain outside this round's scope; the full optional
development suite was not rerun.
