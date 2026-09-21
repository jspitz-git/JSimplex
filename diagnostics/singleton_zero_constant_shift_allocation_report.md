# Zero-RHS objective constant updates in singleton aggregation

Round 144 changes only the objective constant update in
`aggregate_singleton_equalities` in `src/presolve_aggregation.jl`. When the
equality RHS is zero, the exact constant is reused instead of multiplying the
objective ratio by zero and adding the result. The earlier zero-ratio shortcut
is preserved; a nonzero RHS and nonzero ratio retain general rational arithmetic.

The unchanged constant still passes through `_represent_exact`: a BigFloat
constant stored at higher precision can be unrepresentable at the current
precision even when the mathematical update is zero. Projection, candidate
ordering, exact-versus-rounded objective selection, staged updates, rollback,
and primal/basis restoration remain unchanged. No operands are mutated.

As with the existing zero-ratio path, reusing a Rational{BigInt} constant can
share its numerator and denominator with the input model. Ordinary rational
arithmetic is nonmutating, and replacing output array elements preserves the
source. Deep ownership against mutation through internal GMP APIs is not a
model contract.

## Method and results

The baseline includes the preceding 143 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 56 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each probe contains 128 singleton columns and one shared retained column, with
equalities `2*x_i+y=rhs`, bounds `[1,3]` on every x_i, and free y. The objective
prices are `2*ratio` on each x_i and two on y, with initial constant seven.
The four targets use RHS zero (negative zero for negative ratios) and objective
ratios 3, -3, 1, and -1. All 128 eliminations succeed. The projected rows retain
coefficient one and bounds `[-6,-2]`, the retained cost becomes `2-128*ratio`,
and the constant remains seven. Measurement includes projection, staging,
objective updates and reconstruction, not just the skipped arithmetic.

The nonzero-RHS control uses RHS four and ratio three, giving projected bounds
`[-2,2]` and constant `7+128*12`. The zero-ratio control exercises the previous
shortcut with RHS zero. Both controls accept all pivots.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Ratio 3 | 969,112 | 886,408 | 8.53% | 25,216 → 23,168 |
| Ratio -3 | 970,712 | 888,184 | 8.50% | 25,216 → 23,168 |
| Ratio 1 | 970,720 | 888,304 | 8.49% | 25,213 → 23,165 |
| Ratio -1 | 970,712 | 888,408 | 8.48% | 25,216 → 23,168 |
| Nonzero-RHS control | 1,029,896 | 1,030,296 | — | 27,136 → 27,136 |
| Zero-ratio control | 722,568 | 722,872 | — | 18,304 → 18,304 |

All four targets save **2,048 allocations per call**, or **16 per eliminated column**.
Allocated bytes decrease by **8.48–8.53%** in the four targets.
Both controls retain their allocation counts. Cross-process byte differences
on unchanged paths alone establish no benefit.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 843 → 843 | 44,688 → 45,024 |
| afiro | sparse | 4,891 → 4,891 | 214,816 → 214,448 |
| afiro | propagation | 2,437 → 2,437 | 92,648 → 93,208 |
| afiro | presolve | 16,217 → 16,217 | 728,424 → 728,632 |
| afiro | dual | 17,032 → 17,032 | 864,328 → 864,088 |
| afiro | primal | 16,938 → 16,938 | 842,728 → 842,536 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,744 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,747 → 2,747 | 174,088 → 174,264 |
| adlittle | propagation | 18,182 → 18,182 | 641,912 → 641,800 |
| adlittle | presolve | 82,433 → 82,433 | 3,328,136 → 3,326,504 |
| adlittle | dual | 84,448 → 84,448 | 4,115,928 → 4,115,912 |
| adlittle | primal | 85,246 → 85,246 | 4,392,856 → 4,392,792 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,672 → 461,464 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,424 → 607,536 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 2,060 → 2,015 | 111,296 → 109,584 |
| kb2 | sparse | 2,836 → 2,836 | 162,160 → 161,984 |
| kb2 | propagation | 12,948 → 12,948 | 455,200 → 454,656 |
| kb2 | presolve | 229,194 → 229,149 | 10,641,920 → 10,639,040 |
| kb2 | dual | 230,396 → 230,351 | 11,095,088 → 11,092,336 |
| kb2 | primal | 230,563 → 230,518 | 11,108,960 → 11,106,384 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,032 → 877,984 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,896 → 260,960 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,618 → 6,618 | 300,560 → 299,920 |
| sc50a | propagation | 6,020 → 6,020 | 223,632 → 223,008 |
| sc50a | presolve | 67,457 → 67,457 | 2,845,944 → 2,846,504 |
| sc50a | dual | 68,529 → 68,529 | 3,191,560 → 3,191,352 |
| sc50a | primal | 68,474 → 68,474 | 3,144,248 → 3,144,120 |
| sc50a | dual_no_presolve | 961 → 961 | 306,256 → 306,128 |
| sc50a | primal_no_presolve | 964 → 964 | 232,200 → 232,232 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 5,598 → 5,598 | 210,824 → 209,992 |
| flugpl | propagation | 3,253 → 3,253 | 123,296 → 123,088 |
| flugpl | presolve | 30,791 → 30,791 | 1,170,416 → 1,170,528 |
| flugpl | dual | 31,462 → 31,462 | 1,280,328 → 1,279,992 |
| flugpl | primal | 31,811 → 31,811 | 1,324,696 → 1,324,920 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

The standalone singleton pass, full presolve, and both solves with presolve
each save **45 allocations on kb2**. The remaining 46 reference measurements
retain their allocation counts, including both solves without presolve.

All 30 model snapshots (five fixtures × basic/doubleton/singleton/sparse/
propagation/full presolve) matched exactly: CSC arrays, objective and constant,
sense, bounds, domains, names, and original column count. All 20 whole-solve
combinations remained `OPTIMAL`, with identical status, objective, full primal
vector, and iteration count (`isequal`).

Machine-readable results:
[`singleton-zero-constant-shift-allocations-before.toml`](singleton-zero-constant-shift-allocations-before.toml)
and [`singleton-zero-constant-shift-allocations-after.toml`](singleton-zero-constant-shift-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_singleton_equalities --output=singleton-zero-constant-shift-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function singleton_zero_constant_shift_probe(kind; count=128, T=Float64)
    ratio=kind==:zero_ratio ? 0 : kind==:unit_positive ? 1 : kind==:unit_negative ? -1 : kind==:negative ? -3 : 3
    rhs=kind==:nonzero_rhs ? T(4) : kind in (:negative,:unit_negative) ? -zero(T) : zero(T)
    A=hcat(sparse(1:count,1:count,fill(T(2),count),count,count),sparse(ones(T,count,1)))
    problem=LinearProblem(A,[fill(T(2ratio),count);T(2)];objective_constant=T(7),
        row_lower=fill(rhs,count),row_upper=fill(rhs,count),
        column_lower=[ones(T,count);nothing],column_upper=[fill(T(3),count);nothing])
    return problem,JSimplex.aggregate_singleton_equalities
end

for kind in (:positive,:negative,:unit_positive,:unit_negative,:nonzero_rhs,:zero_ratio)
    problem, pass = singleton_zero_constant_shift_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **1,722 assertions** and failed only
the four target allocation guards: 25,261, 25,224, 25,221, and 25,224 allocations
against a 24,500 limit. Both control budgets passed. There are **1,726 new
assertions**; existing allocation budgets were not relaxed.

Coverage includes Float32, Float64, BigFloat, and Rational{BigInt}; signed zero
RHS and constants; signed unit, nonunit, fractional, and zero objective ratios;
finite and free pivot bounds; sequential nonzero/zero constant shifts;
projected matrix/bounds/objective; restored primal and basis; objective
equivalence; and source preservation under ordinary output mutation.

BigFloat tests use stored 256-bit constants at ambient precision 32/64/256.
An unchanged constant `7+2^-200` rejects at the lower precisions while exactly
representable seven succeeds. A retained column of degree two prevents an
unrelated alternate singleton candidate. Accepted output constants use ambient
precision, and the source retains its stored 256-bit value.

The targeted presolve/allocation suite passed **81,392 / 81,392 assertions**
in 1m59.0s, including every new allocation guard.

Independent read-only review found no issues. An AST-renamed copy of the saved
baseline passed **1,931 assertions across 144 differential models**, plus two
rational alias probes. Coverage included all four numeric types, BigFloat
stored at 256 bits with ambient precision 32/64/256, exact-versus-rounded
candidate preference, late rejection and rollback, sequential constant shifts,
projected/free/fixed bounds, primal and basis restoration, and source preservation.
The rational alias probes confirmed the documented component sharing and
nonmutating ordinary arithmetic.

The full test suite passed **100,889 / 100,889 assertions** in **6m02.7s**.

Full-suite command:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
