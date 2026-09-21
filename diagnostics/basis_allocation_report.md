# Allocation audit: basis matrix assembly

This fifth round targets basis assembly during refactorization. The preceding
presolve, MPS, MOI, and PFI changes remain in both measurements; baseline
`src/simplex.jl` is unchanged from `4fb2026`. Measurements use Julia 1.13.0 on
aarch64-linux-gnu with one Julia thread, PFI updates, and native refactorization.
Each entry is the minimum of three warmed calls, with no compilation observed
in any measured call. These are cumulative Julia heap allocations, not peak
memory.

## Findings and changes

The post-PFI `adlittle` profile still attributed substantial allocations to
`basis_matrix`: it assembled row/column/value triplets and passed them to
`sparse`, even though the source matrix already stores ordered CSC columns.

The function now counts the stored entries, allocates the three result arrays,
and copies structural columns directly. Each selected slack column contributes
its single negative unit entry. Column pointers follow the selected basis order.
This removes the triplet-to-CSC conversion and its temporary arrays.

Three obsolete triplet scratch vectors were also removed from `SimplexScratch`,
reducing workspace initialization and retained workspace storage. Basis
validation still runs before assembly. Result arrays remain independent of the
model and of later calls; explicit zeros and stored scalar values are preserved.
The direct copy relies on the standard CSC invariant of sorted, unique row
indices within each column. It does not normalize malformed matrices created
through low-level CSC construction.

## Results

Assembly on each fixture's initial slack basis:

| Model | Before (B) | After (B) | Fewer bytes |
|---|---:|---:|---:|
| afiro | 1,936 | 832 | 57.0% |
| adlittle | 3,696 | 1,584 | 57.1% |
| kb2 | 2,864 | 1,232 | 57.0% |
| sc50a | 3,360 | 1,440 | 57.1% |
| flugpl | 1,456 | 624 | 57.1% |

Complete native refactorization on these initial bases allocated 5.1–5.5% fewer
bytes. Workspace initialization allocated 2.3–2.5% fewer bytes. The larger LU
backend allocations are outside this change.

Whole solves without presolve:

| Model | Dual before (B) | Dual after (B) | Fewer bytes | Primal before (B) | Primal after (B) | Fewer bytes |
|---|---:|---:|---:|---:|---:|---:|
| afiro | 106,048 | 100,992 | 4.8% | 144,752 | 142,160 | 1.8% |
| adlittle | 539,664 | 498,088 | 7.7% | 726,720 | 668,064 | 8.1% |
| kb2 | 1,033,296 | 935,840 | 9.4% | 306,088 | 280,016 | 8.5% |
| sc50a | 350,688 | 328,640 | 6.3% | 265,032 | 251,192 | 5.2% |
| flugpl | 50,032 | 49,392 | 1.3% | 110,256 | 108,160 | 1.9% |

With presolve enabled, whole-solve savings were 0.2–1.3%. All 20 combinations
(five models, primal/dual, presolve on/off) remained `OPTIMAL`. Status, objective,
complete primal vector, and iteration count matched serialized pre-change
snapshots exactly using `isequal`.

A separate assembly probe covers larger bases and a mixture of structural and
slack columns. Mixed selections alternate slack columns with structural columns
selected in descending index order; these are assembly probes, not claims of
nonsingularity or successful solves.

| Source / selection | Rows | Stored entries | Before (B) | After (B) |
|---|---:|---:|---:|---:|
| Tridiagonal / slack | 512 | 512 | 29,304 | 12,568 |
| Tridiagonal / mixed | 512 | 1,023 | 45,688 | 20,760 |
| greenbea / slack | 2,392 | 2,392 | 134,584 | 57,688 |
| greenbea / mixed | 2,392 | 7,574 | 300,472 | 140,632 |

All three CSC arrays matched the original assembler exactly in all four cases.
The comparison invokes the original function with its triplet scratch supplied
separately, because those scratch fields no longer exist in the current workspace.
Both sides include basis validation; scratch and workspace preparation are
outside measurement. `greenbea` is not solved by this probe.

Machine-readable measurements are in
[`basis-allocations-before.toml`](basis-allocations-before.toml),
[`basis-allocations-after.toml`](basis-allocations-after.toml), and
[`basis-assembly-shapes.toml`](basis-assembly-shapes.toml). Whole-solve files also
include full-sampling allocation profiles for `adlittle` dual without presolve.
Timings overlapped other validation, so no runtime-speedup claim is made.

## Reproduction

The existing audit covers workspace initialization, refactorization, and whole
solves with both algorithms and presolve settings:

```sh
julia --startup-file=no --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=refactorize --output=basis-audit.toml
```

To isolate basis assembly in Julia with `--project=dev` from the repository root:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex

problem = read_mps("test/fixtures/solver/netlib/adlittle.mps")
options = SolverOptions(verbose=false)
setup = () -> JSimplex.initialize_workspace(problem, options)
measure_allocations(JSimplex.basis_matrix; setup, samples=3)
measure_allocations(w -> JSimplex.recompute!(w; refactorize=true); setup, samples=3)
```

The reported runs used `--compiled-modules=existing` to support the read-only
package cache. Use identical runtime and inputs for comparisons.

## Regression coverage

The warmed assembly budget failed on the original code at 29,304 bytes versus
a 15,000-byte limit for a 512-row slack basis. Semantic tests cover reordered
structural/slack columns, explicit zeros, empty columns and bases, independent
result arrays, and refactorized forward/transpose solves in Float32, Float64,
BigFloat, and Rational{BigInt}.

Independent review found no defect for valid CSC inputs. All 120 randomized
comparisons matched the original CSC arrays; a separate precision check retained
stored 512-bit BigFloat values with ambient precision reduced to 64 bits.

The GLPK comparison suite passed all six numerical fixtures: `adlittle`,
`flugpl`, `kb2`, `markshare_4_0`, `sc50a`, and `stein9inf`.
The complete mandatory suite passed **14,280/14,280** tests, including the new
47 allocation, matrix storage, and solve checks. The two previously documented
JET development-suite failures remain outside this round's scope; the full
optional development suite was not rerun.
