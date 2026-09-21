# Basic presolve matrix allocation audit

Round 17 removes the intermediate sparse matrix from `_presolve_basic`. The
previous implementation selected retained columns into `A[:, columns]` before
checking for empty rows, even when it ultimately returned the original problem.
When a reduction was needed, it then selected rows into another matrix.

The pass now scans active CSC entries of retained columns directly and constructs
`A[rows, columns]` only after confirming a reduction. The model constructor still
owns its independent copy. Elimination arithmetic, bound shifts, postsolve maps,
and the identity return are unchanged. The scan counts actual nonzero values for
infeasibility diagnostics; stored zero entries remain in retained rows/columns.

## Method

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and the native
basis factorization with PFI updates. Each case was warmed twice, followed by
three samples with setup outside the measured call and garbage collection before
each sample. Tables report minimum allocated bytes. All measurements recorded
zero compilation time. Runs used `--startup-file=no --compiled-modules=existing
--project=dev`; timing overlapped verification, so no runtime-speedup claim is made.

The before state includes the preceding 16 allocation rounds. These are bytes
allocated per call, rather than peak or retained memory.

## Isolated measurements

| Synthetic input | Before | After | Reduction |
| --- | ---: | ---: | ---: |
| Dense 128 × 128, unchanged by the pass | 271,728 | 8,320 | 96.94% |
| Dense 127 × 127 block plus one empty row and column | 808,472 | 549,032 | 32.09% |

Both inputs are stored as CSC matrices with unit objective coefficients. The
unchanged case now needs no matrix copy. The reduced case retains the final
matrix allocation and the copy owned by the resulting model.

| Model | Basic pass before | Basic pass after | Reduction | Full presolve before | Full presolve after | Reduction |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| afiro | 4,304 | 2,448 | 43.12% | 1,212,024 | 1,206,056 | 0.49% |
| adlittle | 12,144 | 5,008 | 58.76% | 5,066,520 | 5,037,752 | 0.57% |
| kb2 | 8,368 | 3,216 | 61.57% | 13,352,096 | 13,335,712 | 0.12% |
| sc50a | 22,336 | 19,616 | 12.18% | 4,355,296 | 4,347,792 | 0.17% |
| flugpl | 2,864 | 1,792 | 37.43% | 1,516,368 | 1,511,968 | 0.29% |

Whole solves with presolve enabled allocated 0.10–0.49% fewer bytes. The unchanged
paths with presolve disabled varied by -176 to +288 bytes, with identical
allocation counts. These small fluctuations are not attributed to this change;
the isolated basic-pass measurements provide the clearest evidence.

For each fixture, both the basic-pass and full-presolve results matched the
before snapshots exactly: CSC arrays, objective and constant, row and column
bounds, domains, names, and original column count. All 20 whole-solve combinations
(five fixtures, primal/dual, presolve on/off) remained `OPTIMAL`; status, objective,
complete primal vector, and iteration count matched with `isequal`.

Machine-readable measurements:
[`basic-presolve-allocations-before.toml`](basic-presolve-allocations-before.toml)
and [`basic-presolve-allocations-after.toml`](basic-presolve-allocations-after.toml).

## Reproduction

The existing audit supports both affected stages and whole solves:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=_presolve_basic --output=basic-presolve-audit.toml
```

To reproduce the synthetic probes, run from the repository root with the same
Julia flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays

for matrix in (ones(128, 128), [ones(127, 127) zeros(127); zeros(1, 128)])
    problem = LinearProblem(sparse(matrix), ones(128))
    println(measure_allocations(_ -> JSimplex._presolve_basic(problem); samples=3))
end
```

## Regression coverage

Both allocation budgets failed before the change: 271,728 bytes against a
60,000-byte limit for the unchanged case, and 808,472 bytes against a 650,000-byte
limit for reduction. Both now pass.

The 118 new checks cover simultaneous and separate row/column removal, retained
explicit zeros, zeros in removed rows, fixed-column bound shifts, infeasibility
diagnostics, independent result matrices, postsolve mapping, named rows/columns,
the identity return, spare CSC storage, and empty dimensions. Numeric coverage
includes Float32, Float64, BigFloat, and Rational{BigInt}.

Independent review found no issue. Its 300 differential cases across six numeric
types matched the original implementation exactly, including 156 infeasible
cases. Those comparisons also covered explicit selections, postsolve maps, all
model fields, failure diagnostics, and padded CSC storage.

The complete mandatory suite passed **15,722/15,722** tests, including the 118
new checks. `git diff --check` passed. The two previously documented JET
development-suite failures remain outside this round's scope; the full optional
development suite was not rerun.
