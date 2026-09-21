# Allocation audit: product-form basis updates

This fourth round targets the PFI basis updates used during simplex iterations.
The preceding presolve, MPS, and MOI changes remain in both measurements; baseline
`src/factorization.jl` is unchanged from `4fb2026`. Measurements use Julia 1.13.0
on aarch64-linux-gnu with one Julia thread and native basis refactorization.
Each whole-solve entry is the minimum of three warmed calls, with no compilation
observed in any measured call. These are cumulative Julia heap allocations,
not peak memory.

## Findings and changes

The `adlittle` dual solve profile without presolve identified growing eta index
and coefficient vectors as a substantial source of iteration allocations.
For a tableau column already using the factorization's scalar type, the update
now counts nonzero entries and reserves capacity in both vectors before packing.
Capacity follows the nonzero count, so sparse columns do not reserve dense
storage. The additional counting pass trades another scan for fewer growth
allocations; it does not change the arithmetic or update representation.

Inputs with a different element type retain the original single conversion pass.
This matters for BigFloat and Rational{BigInt}: converting values merely to count
nonzeros would introduce substantial allocations. Zeros are still tested after
conversion during packing, including values that underflow to zero.

Each update still owns its vectors. Copying a factorization, adding updates, and
refactorizing preserve the existing ownership behavior. Pivot checks, arithmetic
order, zero tolerance, and the other basis-update methods are unchanged.

## Results

One Float64 update on a fresh 512-row factorization, with factor construction
outside measurement:

| Column | Before (B) | After (B) | Before allocations | After allocations |
|---|---:|---:|---:|---:|
| Dense, 512 nonzeros | 17,344 | 8,496 | 19 | 9 |
| Sparse, 3 nonzeros | 352 | 352 | 7 | 7 |

The dense update allocates **51.0% fewer bytes**. A separate repeated-update
probe, retaining the update-list capacity, also covered 8,192-row dense/sparse
columns and Float32, BigFloat, Rational{BigInt}, and mixed scalar types. Sparse
storage remained small; the mixed-type path retained its original allocation
count. Timings were collected while other validation ran, so no runtime-speedup
claim is made.

Whole solves without presolve:

| Model | Dual before (B) | Dual after (B) | Fewer bytes | Primal before (B) | Primal after (B) | Fewer bytes |
|---|---:|---:|---:|---:|---:|---:|
| afiro | 110,976 | 106,080 | 4.4% | 147,152 | 144,800 | 1.6% |
| adlittle | 606,656 | 539,184 | 11.1% | 794,432 | 727,632 | 8.4% |
| kb2 | 1,070,240 | 1,033,712 | 3.4% | 353,208 | 306,104 | 13.3% |
| sc50a | 370,560 | 350,960 | 5.3% | 301,160 | 264,728 | 12.1% |
| flugpl | 51,600 | 50,032 | 3.0% | 112,896 | 110,240 | 2.4% |

With presolve enabled, measured totals range from 1.63% fewer bytes (`adlittle`
dual) to 0.09% more bytes (`flugpl` dual). These smaller changes do not establish
a universal whole-pipeline allocation reduction. Allocation counts decreased in
all 20 solve configurations.

All 20 combinations (five models, primal/dual, presolve on/off) remained `OPTIMAL`.
The status, objective, complete primal vector, and iteration count matched
serialized pre-change snapshots exactly using `isequal`.

Machine-readable results are in
[`pfi-allocations-before.toml`](pfi-allocations-before.toml),
[`pfi-allocations-after.toml`](pfi-allocations-after.toml), and
[`pfi-update-shapes.toml`](pfi-update-shapes.toml). Shape-probe values are totals
over the recorded number of repetitions; unlike the fresh-factor measurements,
they reuse the update-list capacity.

## Reproduction

The existing audit measures whole solves with both algorithms and presolve
settings. This command also profiles allocation sites in the dual solve without
presolve:

```sh
julia --startup-file=no --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=solve_dual_no_presolve --output=pfi-audit.toml
```

To isolate a single update, run the following in Julia with `--project=dev` from
the repository root:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex

dimension = 512
column = ones(dimension)
setup = () -> JSimplex.PFIFactorization(
    JSimplex.SparseArrays.spdiagm(0 => ones(dimension)))
measure_allocations(factor -> JSimplex.replace_column!(factor, column, 256);
                    setup, samples=3)

fill!(column, 0.0)
column[[1, 256, 512]] .= 1.0
measure_allocations(factor -> JSimplex.replace_column!(factor, column, 256);
                    setup, samples=3)
```

The reported runs used `--compiled-modules=existing` to support the read-only
package cache. Use identical runtime and input files for comparisons.

## Regression coverage

The dense-update budget failed on the original code at 17,248 bytes versus a
10,000-byte limit. The companion sparse budget rejects reserving dimension-sized
storage for a three-entry update. Another allocation regression test rejects
double conversion of a Float64 column into Rational{BigInt}; it was observed
failing before the mixed-type correction.

Semantic tests cover independent coefficient storage, copied factorizations
after subsequent updates/refactorization, Float32/Float64/BigFloat/exact rational
solves, and mixed-type underflow. Independent review verified matching packed
indices and coefficients in eight typed/mixed, sparse/dense cases and confirmed
that the mixed-type allocation regression was resolved.

The GLPK comparison suite passed all six numerical fixtures: `adlittle`,
`flugpl`, `kb2`, `markshare_4_0`, `sc50a`, and `stein9inf`.
The final mandatory suite passed **14,233/14,233** tests, including the new
21 allocation and ownership checks. The two previously documented JET
development-suite failures remain outside this round's scope; the full optional
development suite was not rerun.
