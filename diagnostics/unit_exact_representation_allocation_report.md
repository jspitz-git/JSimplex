# Avoid rational roundtrips for converted signed units

Round 177 changes only `_represent_exact` in `src/presolve.jl`. After the existing
conversion, finite-value and zero checks, converted +1 is accepted only if the
exact input is one; converted -1 is accepted only if the exact input is -1.
This avoids converting either stored unit back to `Rational{BigInt}` for comparison.

The exact-input checks remain essential: a nearby nonunit rational may round to
±1, and the new branches must still reject it. Original conversion determines
the returned numeric type and BigFloat precision. Exception handling, nonfinite
rejection, zero handling and every nonunit roundtrip remain unchanged. No input
values are mutated. Direct warmed checks confirmed that comparison with -1
allocates nothing for Float32, Float64, BigFloat and Rational{BigInt}.

## Method and results

The baseline includes the preceding 176 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 56 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each probe maps `_represent_exact(Float64, value)` over 128 preconstructed exact
rationals. Measurement includes the result vector and complete helper calls;
input construction is outside measurement. These are focused helper benchmarks,
not whole-program memory reductions.

- `positive_unit` and `negative_unit`: exact +1 and -1, accepted unchanged.
- `rounded_positive` and `rounded_negative`: ±(1+2^-55), which convert to ±1
  but must be rejected because the exact input is not a unit.
- `zero`: exact zero, retaining the existing zero shortcut.
- `nonunit`: exact 3/2, retaining the general rational roundtrip.

Each target skips 128 exact roundtrip conversions. Both controls preserve
allocation counts.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| positive_unit | 90,976 | 37,984 | 58.25% | 1,922 → 386 |
| negative_unit | 90,832 | 37,984 | 58.18% | 1,922 → 386 |
| rounded_positive | 89,760 | 36,928 | 58.86% | 1,922 → 386 |
| rounded_negative | 89,760 | 36,928 | 58.86% | 1,922 → 386 |
| zero | 37,984 | 37,984 | — | 386 → 386 |
| nonunit | 90,848 | 90,976 | — | 1,922 → 1,922 |

Target allocated bytes decrease by **58.18–58.86%**.
Cross-process byte differences on unchanged paths alone establish no benefit.

- `positive_unit` saves **1,536 allocations per call**, or 12 per skipped roundtrip.
- `negative_unit` saves **1,536 allocations per call**, or 12 per skipped roundtrip.
- `rounded_positive` saves **1,536 allocations per call**, or 12 per skipped roundtrip.
- `rounded_negative` saves **1,536 allocations per call**, or 12 per skipped roundtrip.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 747 → 747 | 40,720 → 41,024 |
| afiro | sparse | 3,502 → 3,238 | 166,560 → 157,904 |
| afiro | propagation | 2,437 → 2,437 | 93,224 → 92,840 |
| afiro | presolve | 15,257 → 15,257 | 694,936 → 694,136 |
| afiro | dual | 16,072 → 16,072 | 830,872 → 828,952 |
| afiro | primal | 15,978 → 15,978 | 808,104 → 807,336 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 554 → 554 | 59,088 → 59,088 |
| adlittle | sparse | 1,518 → 1,518 | 125,640 → 125,768 |
| adlittle | propagation | 18,173 → 18,173 | 641,416 → 640,552 |
| adlittle | presolve | 80,215 → 80,215 | 3,254,904 → 3,252,824 |
| adlittle | dual | 82,230 → 82,230 | 4,041,864 → 4,041,720 |
| adlittle | primal | 83,028 → 83,028 | 4,318,696 → 4,319,064 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,176 → 461,480 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 606,880 → 607,104 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 1,492 → 1,492 | 88,744 → 88,904 |
| kb2 | sparse | 1,765 → 1,765 | 118,664 → 118,840 |
| kb2 | propagation | 12,948 → 12,948 | 454,800 → 454,032 |
| kb2 | presolve | 226,297 → 226,297 | 10,539,096 → 10,539,192 |
| kb2 | dual | 227,499 → 227,499 | 10,992,744 → 10,992,424 |
| kb2 | primal | 227,666 → 227,666 | 11,005,896 → 11,005,560 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 877,648 → 878,176 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,912 → 260,832 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 4,859 → 4,415 | 241,680 → 227,800 |
| sc50a | propagation | 6,020 → 6,020 | 221,872 → 221,312 |
| sc50a | presolve | 63,825 → 63,297 | 2,726,912 → 2,710,240 |
| sc50a | dual | 64,897 → 64,369 | 3,072,656 → 3,056,608 |
| sc50a | primal | 64,842 → 64,314 | 3,025,488 → 3,008,784 |
| sc50a | dual_no_presolve | 961 → 961 | 306,480 → 306,496 |
| sc50a | primal_no_presolve | 964 → 964 | 232,216 → 232,216 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 3,812 → 3,812 | 145,672 → 145,256 |
| flugpl | propagation | 3,253 → 3,253 | 123,952 → 123,760 |
| flugpl | presolve | 25,339 → 25,339 | 976,392 → 976,760 |
| flugpl | dual | 26,010 → 26,010 | 1,085,936 → 1,086,528 |
| flugpl | primal | 26,359 → 26,359 | 1,130,224 → 1,130,624 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

Full presolve and each solve with presolve save 528 allocations on sc50a.
Standalone sparse aggregation saves 264 on afiro and 444 on sc50a. In total,
five reference model/stage counts decrease; the remaining 45 are unchanged.
None increase.

All 30 model snapshots (five fixtures × basic/doubleton/singleton/sparse/
propagation/full presolve) matched exactly: CSC arrays, objective and constant,
sense, bounds, domains, names, and original column count. All 20 whole-solve
combinations remained `OPTIMAL`, with identical status, objective, full primal
vector, and iteration count (`isequal`).

Machine-readable results:
[`unit-exact-representation-allocations-before.toml`](unit-exact-representation-allocations-before.toml)
and [`unit-exact-representation-allocations-after.toml`](unit-exact-representation-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=unit-exact-representation-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
function unit_exact_representation_probe(kind; count=128)
    value=kind==:zero ? big(0)//big(1) : kind==:nonunit ? big(3)//big(2) :
        kind in (:rounded_positive,:rounded_negative) ? big(1)//big(1)+big(1)//(BigInt(1)<<55) : big(1)//big(1)
    kind in (:negative_unit,:rounded_negative) && (value=-value)
    values=fill(value,count)
    pass=values->map(value->JSimplex._represent_exact(Float64,value),values)
    return values,pass
end

for kind in (:positive_unit,:negative_unit,:rounded_positive,:rounded_negative,:zero,:nonunit)
    values, pass = unit_exact_representation_probe(kind)
    println(measure_allocations(_ -> pass(values); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **1,483 assertions** and failed only
the four target allocation guards; both controls passed. The file contains
**1,487 new assertions**, all passing after the change. Existing allocation
budgets were not relaxed.

One hundred thirty-five direct scalar cases cover Bool, Int8, Int64, Int128,
BigInt, Float32, Float64, BigFloat and Rational{BigInt}, including signed units,
zero, integer overflow, exact dyadic fractions and nonrepresentable thirds.

Forty-four Float32/Float64 and 110 BigFloat cases probe signed units and neighbors
on both sides, including quarter/half/three-quarter ULP offsets and ties. BigFloat
ambient precision ranges over 16/32/64/128/256. Results must be mathematically
exact or rejected, preserving the requested type and precision. Twelve additional
cases use tails of 2^-200 near ±1 at ambient precision 32/64/256. Other guards
retain rejection of thirds, subnormal underflow and overflow.

Forty-eight complete doubleton models across four numeric types produce ±1 in
alpha, cost, objective constant, matrix entries or row bounds, plus nonunit
controls. They check ratios, exact matrix/bounds/objective, primal/basis
restoration, objective equivalence and source preservation after ordinary output
mutation. Probe result checks and allocation guards cover all six helper batches.

The targeted suite passed **175,417/175,417 assertions** in 3m04.8s.

Independent differential review passed **6,281/6,281 assertions**. The full-model
comparison covered 156 models (132 doubleton, 24 basic), with 112 accepted and
44 unchanged results, 468 primal restorations, 624 basis restorations and eight
staged rollbacks. Another 867 direct helper comparisons covered all nine scalar
types, signed units and neighbors, ties, zero/nonunit/nonfinite values,
underflow/overflow and BigFloat ambient precisions 16/32/64/128/256 with tails
up to 300 bits. Baseline callers explicitly used renamed baseline representation
and bound-shifting helpers. Model, metadata, source and alias-preservation checks
matched. No findings.

The full project suite passed **194,914/194,914 assertions** in 7m29.3s.

Full-suite command:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
