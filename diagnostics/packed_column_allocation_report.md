# Allocation audit: packed upper columns

This tenth round targets the upper-column storage shared by Forrest–Tomlin,
Bartels–Golub, and Suhl–Suhl basis updates. All preceding allocation changes
remain in both measurements. Measurements use Julia 1.13.0 on aarch64-linux-gnu,
one Julia thread, and native refactorization. Each entry is the minimum of three
warmed calls; no compilation was observed in measured calls. These are
cumulative Julia heap allocations, not peak memory.

## Findings and changes

`_packed_column` previously grew its index and value vectors repeatedly with
`push!`. It now counts the nonzero entries, allocates the two output arrays,
and fills them in their original order. The output still owns its arrays and
retains stored values without arithmetic or conversion.

Nonempty columns retain one spare slot beyond their logical length. This matters
because subsequent row rotation can remove an early entry and append it at the
end. Julia may advance a vector's start during deletion; an exactly full backing
array then requires growth for the append. An isolated 128-entry rotation
allocated 8,528 bytes with exact capacity and zero bytes with the spare slot.
Empty columns retain zero capacity. No factorization arithmetic is changed.

## Results

Packing 1,024-element Float64 vectors:

| Stored entries | Before (B) | After (B) | Change |
|---|---:|---:|---:|
| 1,024 | 33,920 | 16,656 | 50.9% fewer |
| 3 | 160 | 192 | 32 B more |
| 0 | 64 | 64 | unchanged |

A complete first-column update of a 128-dimensional identity basis with a dense
unit-valued tableau column, with factorization setup outside measurement:

| Method | Before (B) | After (B) | Fewer bytes |
|---|---:|---:|---:|
| Forrest–Tomlin | 3,456 | 2,400 | 30.6% |
| Bartels–Golub | 9,696 | 8,640 | 10.9% |
| Suhl–Suhl | 3,488 | 2,432 | 30.3% |

Whole dual solves without presolve:

| Model | FT before (B) | FT after (B) | Fewer bytes | BG before (B) | BG after (B) | Fewer bytes | SS before (B) | SS after (B) | Fewer bytes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| afiro | 110,912 | 108,144 | 2.50% | 117,552 | 114,256 | 2.80% | 110,224 | 107,920 | 2.09% |
| adlittle | 577,944 | 563,400 | 2.52% | 719,200 | 691,104 | 3.91% | 600,968 | 572,248 | 4.78% |
| kb2 | 1,014,912 | 978,256 | 3.61% | 1,034,432 | 983,168 | 4.96% | 1,014,880 | 982,144 | 3.23% |
| sc50a | 380,992 | 378,432 | 0.67% | 395,792 | 377,632 | 4.59% | 372,912 | 368,496 | 1.18% |
| flugpl | 49,968 | 49,744 | 0.45% | 53,440 | 52,480 | 1.80% | 52,128 | 50,560 | 3.01% |

Across both primal and dual solves, without presolve, allocation reductions
ranged from **−0.92% to 13.57%**. With presolve, the range was **−0.21% to
0.93%**. Negative reductions indicate increases. Of the 60 measured
configurations, 41 allocated less and 19 allocated slightly more. The spare
capacity has a cost for small sparse columns, so this is a tradeoff rather than
a universal whole-solve improvement. The default PFI update method does not use
this helper and is unaffected by this round.

All 60 combinations (five models, three update methods, primal/dual, presolve
on/off) remained `OPTIMAL`. Status, objective, complete primal vector, and
iteration count matched serialized pre-change snapshots exactly with `isequal`.

Machine-readable measurements are in
[`packed-column-allocations-before.toml`](packed-column-allocations-before.toml)
and [`packed-column-allocations-after.toml`](packed-column-allocations-after.toml).
Timings overlapped other validation, so no runtime-speedup claim is made.

## Reproduction

The existing audit supports all three update methods. For example:

```sh
julia --startup-file=no --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --basis-update=forrest_tomlin --profile=solve_dual_no_presolve --output=packed-column-audit.toml
```

Repeat with `--basis-update=bartels_golub` and `--basis-update=suhl_suhl`.
To reproduce isolated packing and complete-update probes, run from the repository
root with `--project=dev`:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex

values = ones(1024)
measure_allocations(_ -> JSimplex._packed_column(values); samples=3)

B = JSimplex.SparseArrays.spdiagm(0 => ones(128))
tableau = ones(128)
for F in (JSimplex.ForrestTomlinFactorization,
          JSimplex.BartelsGolubFactorization, JSimplex.SuhlSuhlFactorization)
    measure_allocations(f -> JSimplex.replace_column!(f, tableau, 1);
                        setup=() -> F(B), samples=3)
end
```

The reported runs used `--compiled-modules=existing` to support the read-only
package cache. Use identical runtime and inputs for comparisons.

## Regression coverage

The dense packing budget failed on the original implementation: 33,920 bytes
against a 20,000-byte limit. Whole-update budgets caught the exact-capacity
candidate's rotation regression: 10,928/10,960 bytes for FT/SS against 4,000-byte
limits. All three budgets pass with the spare slot.

The 102 new checks cover empty, zero, sparse, and dense inputs, independent
arrays, retained values and index order, signed zeros, nonfinite entries,
subnormal values, and complete forward/transpose solves after the measured
updates. Numeric coverage includes Float32, Float64, BigFloat, and
Rational{BigInt}; stored 512-bit BigFloat values remain intact at ambient
precision 64 bits.

Independent review found no issue. Differential checks across six numeric types
matched packing and 2,520 subsequent insertions, changes, and removals. Follow-up
checks of the spare-slot version covered empty/singleton/128-entry columns,
allocation-free first rotation, repeated rotations, and BigFloat precision.

The complete mandatory suite passed **14,802/14,802** tests, including the 102
new checks. `git diff --check` passed. The two previously documented JET
development-suite failures remain outside this round's scope; the full optional
development suite was not rerun.
