# Equal denominators in implied-bound activity sums

Round 160 changes only the two activity-sum updates in
`_equality_implies_column_bounds` in `src/presolve_aggregation.jl`. When a nonzero
partial sum and the next exact product share a denominator, their numerators
are added directly. `Rational{BigInt}` reduces the result, including exact
cancellation to canonical zero. Different denominators retain general addition.

The zero-partial-sum shortcut still runs first. Unbounded activity and endpoint
guards, zero endpoints and signed-unit products retain their order. Minimum
and maximum activities use their own partial sum independently, including after
cancellation or when only one extreme becomes unbounded. Stored values retain
full precision, including BigFloat values stored above ambient precision.
Final bound comparisons, projection, row-removal decisions, representation
gates, staged updates, rollback and postsolve are unchanged. Inputs are not mutated.

## Method and results

The baseline includes the preceding 159 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 56 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each probe contains 128 independent two-row, three-column blocks:
`2*x+a*y+b*z=4` and `6*x+5*y+7*z<=100`. The cost of x is zero, the costs of y/z
are two/three, and the objective constant is seven. Both retained variables
are fixed to one. All 128 pivots are accepted and all equality rows are removed.
The second row's retained coefficients become `5-3*a` and `7-3*b`, and its upper
bound becomes 88. Measurement includes the full sparse aggregation pass, with
input construction outside measurement.

Integer targets use a/b equal to 3/5 or -3/-5; fraction targets use 1/2 and 3/2,
or their negatives. The eliminated x has bounds `[-8,8]`. The first contribution
uses the existing zero-sum shortcut, while the second uses the new branch on
both activity extremes. Thus each target has 256 shared-denominator additions.
Fraction targets reduce the sum ±4/2 to ±2.

The unequal-denominator control uses a=1/2 and b=1/4, retaining general addition.
The free-pivot control uses a=3 and b=5 with free x; the helper returns early.
Both controls accept every pivot and remove the equality rows.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| integer_positive | 2,544,816 | 2,516,976 | 1.09% | 66,643 → 66,131 |
| integer_negative | 2,546,848 | 2,518,720 | 1.10% | 66,643 → 66,131 |
| fraction_positive | 2,569,856 | 2,545,696 | 0.94% | 66,899 → 66,643 |
| fraction_negative | 2,569,488 | 2,545,632 | 0.93% | 66,899 → 66,643 |
| unequal | 2,675,520 | 2,673,872 | — | 69,971 → 69,971 |
| free_pivot | 1,846,752 | 1,845,376 | — | 44,115 → 44,115 |

Target allocated bytes decrease by **0.93–1.10%**.
Both controls retain allocation counts. Cross-process byte differences on
unchanged paths alone establish no benefit.

- `integer_positive` saves **512 allocations per call**, or 2 per shared-denominator addition.
- `integer_negative` saves **512 allocations per call**, or 2 per shared-denominator addition.
- `fraction_positive` saves **256 allocations per call**, or 1 per shared-denominator addition.
- `fraction_negative` saves **256 allocations per call**, or 1 per shared-denominator addition.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 747 → 747 | 40,976 → 40,880 |
| afiro | sparse | 4,167 → 4,167 | 186,920 → 185,384 |
| afiro | propagation | 2,437 → 2,437 | 92,600 → 92,312 |
| afiro | presolve | 15,653 → 15,653 | 706,376 → 706,296 |
| afiro | dual | 16,468 → 16,468 | 841,880 → 840,888 |
| afiro | primal | 16,374 → 16,374 | 820,344 → 819,256 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,339 → 2,339 | 156,904 → 156,744 |
| adlittle | propagation | 18,182 → 18,182 | 641,704 → 640,856 |
| adlittle | presolve | 81,429 → 81,426 | 3,290,520 → 3,288,432 |
| adlittle | dual | 83,444 → 83,441 | 4,080,952 → 4,078,848 |
| adlittle | primal | 84,242 → 84,239 | 4,357,208 → 4,355,120 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,352 → 461,176 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,200 → 607,536 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 1,915 → 1,915 | 105,384 → 105,352 |
| kb2 | sparse | 2,259 → 2,259 | 137,336 → 137,240 |
| kb2 | propagation | 12,948 → 12,948 | 454,672 → 453,792 |
| kb2 | presolve | 227,909 → 227,907 | 10,590,928 → 10,591,456 |
| kb2 | dual | 229,111 → 229,109 | 11,045,104 → 11,043,264 |
| kb2 | primal | 229,278 → 229,276 | 11,057,808 → 11,056,416 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,080 → 878,080 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,832 → 260,912 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,174 → 6,174 | 282,496 → 281,808 |
| sc50a | propagation | 6,020 → 6,020 | 222,352 → 221,504 |
| sc50a | presolve | 66,302 → 66,302 | 2,803,304 → 2,801,176 |
| sc50a | dual | 67,374 → 67,374 | 3,148,616 → 3,146,488 |
| sc50a | primal | 67,319 → 67,319 | 3,101,416 → 3,099,304 |
| sc50a | dual_no_presolve | 961 → 961 | 306,144 → 306,176 |
| sc50a | primal_no_presolve | 964 → 964 | 232,200 → 232,200 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 4,677 → 4,667 | 174,096 → 172,344 |
| flugpl | propagation | 3,253 → 3,253 | 122,672 → 122,336 |
| flugpl | presolve | 28,078 → 28,046 | 1,064,352 → 1,061,528 |
| flugpl | dual | 28,749 → 28,717 | 1,173,832 → 1,170,736 |
| flugpl | primal | 29,098 → 29,066 | 1,218,056 → 1,215,040 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,728 |

Full presolve and each solve with presolve save three allocations on adlittle,
two on kb2 and 32 on flugpl. Standalone sparse aggregation saves ten on flugpl.
The remaining 40 reference measurements retain their allocation counts.

All 30 model snapshots (five fixtures × basic/doubleton/singleton/sparse/
propagation/full presolve) matched exactly: CSC arrays, objective and constant,
sense, bounds, domains, names, and original column count. All 20 whole-solve
combinations remained `OPTIMAL`, with identical status, objective, full primal
vector, and iteration count (`isequal`).

Machine-readable results:
[`aggregation-implied-equal-sum-denominator-allocations-before.toml`](aggregation-implied-equal-sum-denominator-allocations-before.toml)
and [`aggregation-implied-equal-sum-denominator-allocations-after.toml`](aggregation-implied-equal-sum-denominator-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-implied-equal-sum-denominator-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_implied_equal_sum_denominator_probe(kind; count=128, T=Float64)
    fractional=kind in (:fraction_positive,:fraction_negative,:unequal)
    direction=kind in (:integer_negative,:fraction_negative) ? -one(T) : one(T)
    a=direction*(fractional ? T(1)/2 : T(3))
    b=kind==:unequal ? T(1)/4 : direction*(fractional ? T(3)/2 : T(5))
    xlo=kind==:free_pivot ? nothing : T(-8)
    xhi=kind==:free_pivot ? nothing : T(8)
    rows=collect(1:2:2count);other=rows.+1;cols=collect(1:3:3count)
    A=sparse(vcat(rows,rows,rows,other,other,other),vcat(cols,cols.+1,cols.+2,cols,cols.+1,cols.+2),
        vcat(fill(T(2),count),fill(a,count),fill(b,count),fill(T(6),count),fill(T(5),count),fill(T(7),count)),2count,3count)
    problem=LinearProblem(A,repeat(T[0,2,3],count);objective_constant=T(7),
        row_lower=[isodd(i) ? T(4) : nothing for i in 1:2count],
        row_upper=[isodd(i) ? T(4) : T(100) for i in 1:2count],
        column_lower=[i%3==1 ? xlo : one(T) for i in 1:3count],
        column_upper=[i%3==1 ? xhi : one(T) for i in 1:3count])
    return problem,JSimplex.aggregate_sparse_equalities
end

for kind in (:integer_positive,:integer_negative,:fraction_positive,:fraction_negative,:unequal,:free_pivot)
    problem, pass = aggregation_implied_equal_sum_denominator_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **2,910 assertions** and failed only
the four target allocation guards. Both controls passed. There are **2,914 new
assertions**; existing allocation budgets were not relaxed.

An independent endpoint oracle covers 1,200 helper models across Float32,
Float64, BigFloat and Rational{BigInt}, signed pivots and RHS, integer/fraction
sums, shared/different denominators, cancellation and finite/free/one-sided
bounds. The ±1000 witnesses suffice for these small bounded-size fixtures.
BigFloat cases store terms ±(3+2^-200) and ±(5-2^-200) at 256 bits and run at
ambient 32/64/256. The low bits cancel exactly, while a further ±2^-200 residual
changes the bound decision. Large rational sums use 300-bit numerators and odd
denominators 5, 7, 15 and 21; addition reduces the denominator to one.

Full aggregation checks cover matrix/bounds/objective, projected/removed rows,
primal/basis restoration, objective equivalence and source preservation after
ordinary output mutation.

The targeted presolve/allocation suite passed **129,848 / 129,848 assertions**
in **2m23.2s**, including every new allocation guard.

Independent read-only review found no issues. AST-renamed baseline helper and
sparse aggregation functions passed **5,248 assertions across 140 differential
models**, including 568 helper comparisons against baseline and an independent
exact interval oracle, 420 primal and 560 basis restoration comparisons. There
were 112 accepted and 28 rejected models, with 76 removed and 36 projected rows.
Coverage included eight late rejection/rollback cases, all four numeric types,
MIN/MAX senses, signed/fractional sums, unequal denominators, cancellation and
reentry, normalization, divergent extrema, zero endpoints, early/late unbounded
terms, stored-256 BigFloat at ambient 32/64/256, non-dyadic 300-bit rationals and
source preservation.

The full test suite passed **149,345 / 149,345 assertions** in **6m48.3s**.

Full-suite command:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
