# Skip exact conversion of stored zero doubleton coefficients

Round 175 changes only the affected-row coefficient guard in
`substitute_free_doubleton`, in `src/presolve_substitution.jl`. It reads the
stored coefficient, tests `iszero`, and skips the row before converting to
`Rational{BigInt}`. Previously it performed the conversion first, then detected
that the exact coefficient was zero and skipped the same row.

Explicit positive and negative zeros in CSC storage therefore avoid unnecessary
exact conversion. Absent entries never enter this loop. Every nonzero coefficient,
including subnormal or high-precision values, still follows the original exact
conversion and matrix/bound update paths. No tolerance or rounding is introduced.

The equality row is still excluded first. Row scanning, pivot selection, exact
representation gates, private working copies, candidate rejection, row/column
removal and postsolve are unchanged. Skipped rows preserve their original matrix
entries and bound representations even under lower ambient BigFloat precision.

## Method and results

The baseline includes the preceding 174 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 56 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each probe contains the equality `2*x+y=4` and 128 other rows
`coefficient*x+2*y`. Variable `x` is free, `y` has bounds `[-10,10]`, costs are
`[2,3]`, and the objective constant is seven. Substitution removes `x` and the
first equality. The output has cost two and objective constant eleven.
Construction is outside measurement; the call runs the complete free-doubleton
substitution pass.

- `positive`: explicitly stored +0.0 coefficients, row bounds `[-100,100]`.
- `negative`: explicitly stored -0.0 coefficients, row bounds `[-100,100]`.
- `equal_bounds`: explicitly stored zero coefficients, both bounds 20.
- `unbounded`: explicitly stored zero coefficients, both bounds free.
- `nonzero`: stored coefficients three, row bounds `[-100,100]`; exact updates
  must still run and produce coefficient 0.5 and shifted bounds `[-106,94]`.
- `absent`: no stored entries for `x` outside the first equality; the loop has
  no zero entries to skip.

Each target skips 128 exact conversions. The four target outputs retain the
original coefficient two and row bounds. Both controls preserve allocation counts.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| positive | 78,992 | 36,496 | 53.80% | 1,406 → 254 |
| negative | 78,864 | 36,496 | 53.72% | 1,406 → 254 |
| equal_bounds | 78,864 | 36,496 | 53.72% | 1,406 → 254 |
| unbounded | 78,704 | 36,496 | 53.63% | 1,406 → 254 |
| nonzero | 674,080 | 674,096 | — | 17,406 → 17,406 |
| absent | 34,368 | 34,368 | — | 252 → 252 |

Target allocated bytes decrease by **53.63–53.80%**.
Cross-process byte differences on unchanged paths alone establish no benefit.

- `positive` saves **1,152 allocations per call**, or 9 per skipped conversion.
- `negative` saves **1,152 allocations per call**, or 9 per skipped conversion.
- `equal_bounds` saves **1,152 allocations per call**, or 9 per skipped conversion.
- `unbounded` saves **1,152 allocations per call**, or 9 per skipped conversion.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 747 → 747 | 41,008 → 41,424 |
| afiro | sparse | 3,736 → 3,736 | 173,808 → 173,696 |
| afiro | propagation | 2,437 → 2,437 | 93,096 → 93,336 |
| afiro | presolve | 15,410 → 15,410 | 699,992 → 698,936 |
| afiro | dual | 16,225 → 16,225 | 835,512 → 834,616 |
| afiro | primal | 16,131 → 16,131 | 812,984 → 812,840 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 1,572 → 1,572 | 127,848 → 127,512 |
| adlittle | propagation | 18,182 → 18,182 | 641,224 → 641,208 |
| adlittle | presolve | 80,377 → 80,377 | 3,258,536 → 3,257,608 |
| adlittle | dual | 82,392 → 82,392 | 4,047,208 → 4,046,216 |
| adlittle | primal | 83,190 → 83,190 | 4,323,944 → 4,323,000 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,336 → 461,464 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,232 → 607,632 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 1,915 → 1,915 | 105,384 → 105,096 |
| kb2 | sparse | 1,999 → 1,999 | 127,848 → 127,608 |
| kb2 | propagation | 12,948 → 12,948 | 454,976 → 454,032 |
| kb2 | presolve | 227,017 → 227,017 | 10,562,936 → 10,561,608 |
| kb2 | dual | 228,219 → 228,219 | 11,014,152 → 11,013,960 |
| kb2 | primal | 228,386 → 228,386 | 11,029,176 → 11,027,640 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,000 → 877,616 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,832 → 260,880 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 5,489 → 5,489 | 262,784 → 262,992 |
| sc50a | propagation | 6,020 → 6,020 | 221,680 → 222,032 |
| sc50a | presolve | 64,941 → 64,941 | 2,761,408 → 2,762,304 |
| sc50a | dual | 66,013 → 66,013 | 3,108,432 → 3,107,392 |
| sc50a | primal | 65,958 → 65,958 | 3,061,024 → 3,060,096 |
| sc50a | dual_no_presolve | 961 → 961 | 306,176 → 306,496 |
| sc50a | primal_no_presolve | 964 → 964 | 232,184 → 232,280 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 3,956 → 3,956 | 149,848 → 150,712 |
| flugpl | propagation | 3,253 → 3,253 | 123,280 → 123,120 |
| flugpl | presolve | 25,726 → 25,726 | 988,968 → 988,344 |
| flugpl | dual | 26,397 → 26,397 | 1,098,592 → 1,098,304 |
| flugpl | primal | 26,746 → 26,746 | 1,142,880 → 1,142,288 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

All 50 reference model/stage allocation counts are unchanged. The measured
benefit is confined to the targeted explicit-zero coefficient probes.

All 30 model snapshots (five fixtures × basic/doubleton/singleton/sparse/
propagation/full presolve) matched exactly: CSC arrays, objective and constant,
sense, bounds, domains, names, and original column count. All 20 whole-solve
combinations remained `OPTIMAL`, with identical status, objective, full primal
vector, and iteration count (`isequal`).

Machine-readable results:
[`doubleton-stored-zero-coefficient-allocations-before.toml`](doubleton-stored-zero-coefficient-allocations-before.toml)
and [`doubleton-stored-zero-coefficient-allocations-after.toml`](doubleton-stored-zero-coefficient-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=substitute_free_doubleton --output=doubleton-stored-zero-coefficient-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function doubleton_stored_zero_coefficient_probe(kind; count=128, T=Float64)
    coefficient=kind==:negative ? -zero(T) : kind==:nonzero ? T(3) : zero(T)
    first_rows=kind==:absent ? [1] : collect(1:count+1)
    rows=vcat(first_rows,collect(1:count+1))
    columns=vcat(fill(1,length(first_rows)),fill(2,count+1))
    values=vcat(kind==:absent ? T[2] : T[2;fill(coefficient,count)],T[1;fill(T(2),count)])
    A=sparse(rows,columns,values,count+1,2)
    lower=kind==:unbounded ? nothing : kind==:equal_bounds ? T(20) : T(-100)
    upper=kind==:unbounded ? nothing : kind==:equal_bounds ? T(20) : T(100)
    problem=LinearProblem(A,T[2,3];objective_constant=T(7),
        row_lower=[T(4);fill(lower,count)],row_upper=[T(4);fill(upper,count)],
        column_lower=[nothing,T(-10)],column_upper=[nothing,T(10)])
    return problem,JSimplex.substitute_free_doubleton
end

for kind in (:positive,:negative,:equal_bounds,:unbounded,:nonzero,:absent)
    problem, pass = doubleton_stored_zero_coefficient_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **2,396 assertions** and failed only
the four target allocation guards; both controls passed. The file contains
**2,400 new assertions**, all passing after the change. Existing allocation
budgets were not relaxed.

Two hundred forty full-pass models cover Float32, Float64, BigFloat and
Rational{BigInt}, signed pivots, zero/signed RHS, explicitly stored ±0.0 and
finite/equal/one-sided/free row bounds. Tests assert the explicit CSC entries
remain in the source and verify matrix, bounds, objective, primal/basis restoration
and source preservation.

Six BigFloat models store nonzero old matrix entries and bounds at 256 bits,
with tails of 2^-200, and run under ambient precision 32/64/256. A stored zero
coefficient must leave these values unchanged without requiring them to fit
the ambient precision. Additional Float32/Float64 cases preserve distinct
negative-zero lower bounds and positive-zero upper bounds.

Twenty-four tiny-nonzero models use minimum Float32/Float64 subnormals or signed
2^-200 BigFloat/rational values. They must update the matrix to the exact nonzero
result, never take the zero shortcut. Four underflow models reject inexact
nonzero products and preserve the original source.

Twenty-four block-probe models cover all four numeric types and six probes,
checking stored-entry counts, matrix/bounds/objective, substitution selection,
primal/basis restoration, objective equivalence and source preservation after
ordinary output mutation. Nonzero and absent-entry controls guard unchanged
allocation paths.

The targeted suite passed **172,839/172,839 assertions** in 3m01.3s.

Independent differential review passed **3,853/3,853 assertions** across 130
models: 112 substitutions and 18 unchanged results. Coverage includes 390 primal
restorations, 520 basis restorations and six late rejection/fallback cases. Exact
model, substitution step, metadata, source preservation and ordinary output
mutation matched the AST-loaded saved baseline. Fixtures also cover signed and
absent zeros, mixed row scans, zero pivots, tiny nonzeros and preservation of
stored BigFloat precision. No findings.

The full project suite passed **192,336/192,336 assertions** in 7m20.0s.

Full-suite command:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
