# Equal denominators in doubleton substitution ratios

Round 174 changes only the nonunit-pivot ratio calculations in
`substitute_free_doubleton`, in `src/presolve_substitution.jl`. If the exact RHS
and pivot have the same denominator, alpha is constructed from their numerators.
If the retained coefficient and pivot have the same denominator, beta is
constructed from the negated retained numerator and pivot numerator. Both use
the canonical `Rational{BigInt}` constructor, which still normalizes signs and
reduces the fraction, avoiding general rational division's denominator work.

Signed-unit pivots retain their existing paths, and zero RHS still reuses its
exact zero. Unequal denominators retain the original division expressions.
Both `_represent_exact` checks remain: even an exact rational ratio must be
representable in the stored numeric type before substitution can proceed.
Objective and matrix updates, bound shifts, candidate rejection, row/column
removal and postsolve are unchanged. Input exact values are not mutated.

## Method and results

The baseline includes the preceding 173 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 56 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each probe contains 128 independent two-variable equalities
`pivot*x+retained*y=rhs`. Every `x` is free, every `y` has bounds `[-10,10]`,
the eliminated costs are three, and the retained costs are the smallest positive
Float64 subnormal. The objective constant is seven. All candidate ratios are
representable, but the subsequent exact retained-cost update is not. All 128
candidates must be rejected and the original model returned. Construction is
outside measurement; the call runs the complete free-doubleton substitution pass.

- `positive` and `negative`: pivot ±2, RHS four and retained coefficient three;
  all input denominators are one.
- `fraction_positive` and `fraction_negative`: pivot ±0.5, RHS 1.5 and retained
  coefficient 2.5; all input denominators are two.
- `unequal`: pivot 0.5, RHS four and retained coefficient three; both divisions
  retain the general path because their input denominators differ.
- `unit`: pivot one, RHS four and retained coefficient three; the existing
  unit-pivot path bypasses both new branches.

Each target calculates 256 matching-denominator ratios. Both controls preserve
allocation counts.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| positive | 947,672 | 905,896 | 4.41% | 23,940 → 22,916 |
| negative | 948,584 | 908,296 | 4.25% | 23,940 → 22,916 |
| fraction_positive | 951,544 | 911,160 | 4.24% | 23,940 → 22,916 |
| fraction_negative | 951,496 | 911,016 | 4.25% | 23,940 → 22,916 |
| unequal | 951,672 | 952,248 | — | 23,940 → 23,940 |
| unit | 818,120 | 818,504 | — | 20,100 → 20,100 |

Target allocated bytes decrease by **4.24–4.41%**.
Cross-process byte differences on unchanged paths alone establish no benefit.

- `positive` saves **1,024 allocations per call**, or 8 per candidate (4 per ratio).
- `negative` saves **1,024 allocations per call**, or 8 per candidate (4 per ratio).
- `fraction_positive` saves **1,024 allocations per call**, or 8 per candidate (4 per ratio).
- `fraction_negative` saves **1,024 allocations per call**, or 8 per candidate (4 per ratio).

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 747 → 747 | 41,184 → 41,264 |
| afiro | sparse | 3,736 → 3,736 | 173,408 → 173,744 |
| afiro | propagation | 2,437 → 2,437 | 92,056 → 92,520 |
| afiro | presolve | 15,410 → 15,410 | 698,536 → 698,904 |
| afiro | dual | 16,225 → 16,225 | 833,704 → 833,976 |
| afiro | primal | 16,131 → 16,131 | 811,704 → 812,040 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,936 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,776 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 1,572 → 1,572 | 127,240 → 127,976 |
| adlittle | propagation | 18,182 → 18,182 | 639,656 → 640,616 |
| adlittle | presolve | 80,377 → 80,377 | 3,259,352 → 3,257,752 |
| adlittle | dual | 82,392 → 82,392 | 4,050,056 → 4,046,872 |
| adlittle | primal | 83,190 → 83,190 | 4,327,192 → 4,323,816 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,096 → 461,720 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,408 → 607,744 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 1,915 → 1,915 | 105,016 → 105,352 |
| kb2 | sparse | 1,999 → 1,999 | 127,464 → 127,816 |
| kb2 | propagation | 12,948 → 12,948 | 453,056 → 453,232 |
| kb2 | presolve | 227,017 → 227,017 | 10,560,808 → 10,561,272 |
| kb2 | dual | 228,219 → 228,219 | 11,014,712 → 11,014,248 |
| kb2 | primal | 228,386 → 228,386 | 11,027,800 → 11,028,200 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,064 → 878,224 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,848 → 260,816 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 5,489 → 5,489 | 262,064 → 262,464 |
| sc50a | propagation | 6,020 → 6,020 | 220,848 → 220,992 |
| sc50a | presolve | 64,941 → 64,941 | 2,761,536 → 2,761,808 |
| sc50a | dual | 66,013 → 66,013 | 3,107,920 → 3,108,000 |
| sc50a | primal | 65,958 → 65,958 | 3,060,800 → 3,060,672 |
| sc50a | dual_no_presolve | 961 → 961 | 306,128 → 306,224 |
| sc50a | primal_no_presolve | 964 → 964 | 232,200 → 232,200 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 3,956 → 3,956 | 149,208 → 150,408 |
| flugpl | propagation | 3,253 → 3,253 | 122,320 → 122,736 |
| flugpl | presolve | 25,726 → 25,726 | 988,584 → 988,648 |
| flugpl | dual | 26,397 → 26,397 | 1,098,864 → 1,098,800 |
| flugpl | primal | 26,746 → 26,746 | 1,143,040 → 1,143,456 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,728 |

All 50 reference model/stage allocation counts are unchanged. The measured
benefit is confined to the targeted matching-denominator ratio probes.

All 30 model snapshots (five fixtures × basic/doubleton/singleton/sparse/
propagation/full presolve) matched exactly: CSC arrays, objective and constant,
sense, bounds, domains, names, and original column count. All 20 whole-solve
combinations remained `OPTIMAL`, with identical status, objective, full primal
vector, and iteration count (`isequal`).

Machine-readable results:
[`doubleton-equal-ratio-denominator-allocations-before.toml`](doubleton-equal-ratio-denominator-allocations-before.toml)
and [`doubleton-equal-ratio-denominator-allocations-after.toml`](doubleton-equal-ratio-denominator-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=substitute_free_doubleton --output=doubleton-equal-ratio-denominator-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function doubleton_equal_ratio_denominator_probe(kind; count=128, T=Float64)
    fractional=kind in (:fraction_positive,:fraction_negative,:unequal)
    pivot=kind==:unit ? one(T) : fractional ? T(1)/2 : T(2)
    kind in (:negative,:fraction_negative) && (pivot=-pivot)
    rhs=kind in (:fraction_positive,:fraction_negative) ? T(3)/2 : T(4)
    retained=kind in (:fraction_positive,:fraction_negative) ? T(5)/2 : T(3)
    tiny=T in (Float32,Float64) ? nextfloat(zero(T)) : T(BigInt(1)//(BigInt(1)<<512))
    rows=collect(1:count)
    A=sparse(vcat(rows,rows),vcat(rows,rows.+count),vcat(fill(pivot,count),fill(retained,count)),count,2count)
    problem=LinearProblem(A,vcat(fill(T(3),count),fill(tiny,count));objective_constant=T(7),
        row_lower=fill(rhs,count),row_upper=fill(rhs,count),
        column_lower=vcat(fill(nothing,count),fill(T(-10),count)),
        column_upper=vcat(fill(nothing,count),fill(T(10),count)))
    return problem,JSimplex.substitute_free_doubleton
end

for kind in (:positive,:negative,:fraction_positive,:fraction_negative,:unequal,:unit)
    problem, pass = doubleton_equal_ratio_denominator_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **3,056 assertions** and failed only
the four target allocation guards; both controls passed. The file contains
**3,060 new assertions**, all passing after the change. Existing allocation
budgets were not relaxed.

Independent exact substitution covers 320 full-pass models across Float32,
Float64, BigFloat and Rational{BigInt}, signed integer/fractional pivots and
retained coefficients, zero/signed RHS, and matching/mixed input denominators.
Tests compare alpha/beta, matrix, row bounds, objective, primal/basis restoration
and source preservation. Sixteen additional large-rational models use 300-bit
numerators and denominators 5, 7, 15 and 21, checking general and cancelled
ratios, canonical signs/reduction and reconstruction.

Twenty-four BigFloat models store integer inputs near 2^200 at 256 bits and
run under ambient precision 32/64/256. They separately exercise exact ratios,
inexact alpha, inexact beta and zero RHS with inexact beta. Both target gates
must reject low-precision conversions while preserving the stored inputs.
Twelve Float32/Float64/BigFloat models separately reject nondyadic alpha or beta
from division by signed three, despite matching denominators.

Eighteen block-probe models confirm rejection for Float32/Float64/BigFloat.
Twenty-four accepted variants across all four numeric types use representable
cost updates, checking matrix/bounds/objective, substitution selection,
primal/basis restoration, objective equivalence and preservation of the source
after ordinary output mutation. Unequal-denominator and unit-pivot controls
guard unchanged allocation paths.

The targeted suite passed **170,439/170,439 assertions** in 2m58.7s.

Independent differential review passed **3,325/3,325 assertions** across 132
models: 88 accepted substitutions and 44 unchanged cases. Coverage includes
396 primal restorations, 528 basis restorations and eight late rejection/fallback
cases. Exact model, substitution step, metadata, source preservation and stored
BigFloat precision matched the AST-loaded saved baseline. Additional edge cases
include zero/tiny pivots, overflow/underflow and canonical large ratios. No findings.

The full project suite passed **189,936/189,936 assertions** in 7m15.1s.

Full-suite command:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
