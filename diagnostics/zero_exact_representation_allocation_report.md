# Avoid rational roundtrips for converted zeros

Round 176 changes only `_represent_exact` in `src/presolve.jl`, a common exact
representation gate used throughout presolve. After the original conversion and
finite-value check, a converted zero is accepted if the exact input is also zero,
and rejected otherwise. This avoids converting the stored zero back to
`Rational{BigInt}` just to compare it with the original exact input.

The distinction is essential: a nonzero rational may underflow to floating zero,
but that rounded zero must never be accepted. The shortcut explicitly checks
both sides. The original conversion still determines the returned type, zero
sign and BigFloat precision; existing exception handling and nonfinite rejection
remain unchanged. Every nonzero converted result retains the original exact
rational roundtrip. Input values are not mutated.

## Method and results

The baseline includes the preceding 175 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 56 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each probe maps `_represent_exact` over 128 preconstructed exact rationals,
alternating signs for nonzero inputs. Measurement includes the result vector
and the complete helper calls; input construction is outside measurement.
These are focused helper benchmarks, not whole-program memory reductions.

- `zero_float32` and `zero_float64`: exact zero, converted to the named type;
  every result must be its positive zero.
- `underflow_float32`: signed 2^-151, below half the smallest Float32 subnormal.
- `underflow_float64`: signed 2^-1076, below half the smallest Float64 subnormal.
  Both underflow probes must return `nothing` for every element.
- `nonzero`: signed 3/2 converted to Float64, exactly representable and nonzero.
- `inexact_nonzero`: signed 1/3 converted to Float64, nonzero but inexact;
  every result must still be rejected.

Each target skips 128 exact roundtrip conversions. Both controls preserve
allocation counts.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| zero_float32 | 79,920 | 37,440 | 53.15% | 1,538 → 386 |
| zero_float64 | 80,880 | 37,984 | 53.04% | 1,538 → 386 |
| underflow_float32 | 79,408 | 36,928 | 53.50% | 1,538 → 386 |
| underflow_float64 | 79,328 | 36,928 | 53.45% | 1,538 → 386 |
| nonzero | 91,648 | 91,840 | — | 1,922 → 1,922 |
| inexact_nonzero | 91,760 | 90,208 | — | 1,922 → 1,922 |

Target allocated bytes decrease by **53.04–53.50%**.
Cross-process byte differences on unchanged paths alone establish no benefit.

- `zero_float32` saves **1,152 allocations per call**, or 9 per skipped roundtrip.
- `zero_float64` saves **1,152 allocations per call**, or 9 per skipped roundtrip.
- `underflow_float32` saves **1,152 allocations per call**, or 9 per skipped roundtrip.
- `underflow_float64` saves **1,152 allocations per call**, or 9 per skipped roundtrip.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 747 → 747 | 39,552 → 40,992 |
| afiro | sparse | 3,736 → 3,502 | 175,488 → 166,736 |
| afiro | propagation | 2,437 → 2,437 | 93,752 → 93,288 |
| afiro | presolve | 15,410 → 15,257 | 700,408 → 693,976 |
| afiro | dual | 16,225 → 16,072 | 835,992 → 830,184 |
| afiro | primal | 16,131 → 15,978 | 813,768 → 807,928 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 554 | 60,816 → 59,088 |
| adlittle | sparse | 1,572 → 1,518 | 126,840 → 125,160 |
| adlittle | propagation | 18,182 → 18,173 | 641,944 → 640,968 |
| adlittle | presolve | 80,377 → 80,215 | 3,260,264 → 3,253,976 |
| adlittle | dual | 82,392 → 82,230 | 4,049,192 → 4,042,680 |
| adlittle | primal | 83,190 → 83,028 | 4,325,480 → 4,319,416 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,768 → 461,464 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,392 → 607,008 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 1,915 → 1,492 | 104,488 → 88,168 |
| kb2 | sparse | 1,999 → 1,765 | 127,000 → 118,104 |
| kb2 | propagation | 12,948 → 12,948 | 455,712 → 454,800 |
| kb2 | presolve | 227,017 → 226,297 | 10,563,800 → 10,539,656 |
| kb2 | dual | 228,219 → 227,499 | 11,016,856 → 10,992,200 |
| kb2 | primal | 228,386 → 227,666 | 11,029,720 → 11,005,816 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,176 → 877,920 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,832 → 260,848 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 5,489 → 4,859 | 264,128 → 241,680 |
| sc50a | propagation | 6,020 → 6,020 | 223,360 → 222,448 |
| sc50a | presolve | 64,941 → 63,825 | 2,762,624 → 2,725,440 |
| sc50a | dual | 66,013 → 64,897 | 3,108,944 → 3,071,376 |
| sc50a | primal | 65,958 → 64,842 | 3,061,872 → 3,024,208 |
| sc50a | dual_no_presolve | 961 → 961 | 306,368 → 306,192 |
| sc50a | primal_no_presolve | 964 → 964 | 232,216 → 232,216 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 3,956 → 3,812 | 151,208 → 144,952 |
| flugpl | propagation | 3,253 → 3,253 | 123,968 → 123,280 |
| flugpl | presolve | 25,726 → 25,339 | 990,600 → 976,152 |
| flugpl | dual | 26,397 → 26,010 | 1,100,608 → 1,085,840 |
| flugpl | primal | 26,746 → 26,359 | 1,144,864 → 1,131,072 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

Full presolve and each solve with presolve save 153 allocations on afiro,
162 on adlittle, 720 on kb2, 1,116 on sc50a and 387 on flugpl. Standalone sparse
aggregation saves 234/54/234/630/144 respectively. Singleton aggregation saves
54 on adlittle and 423 on kb2; propagation saves nine on adlittle. In total,
23 reference model/stage counts decrease and the remaining 27 are unchanged.
None increase.

All 30 model snapshots (five fixtures × basic/doubleton/singleton/sparse/
propagation/full presolve) matched exactly: CSC arrays, objective and constant,
sense, bounds, domains, names, and original column count. All 20 whole-solve
combinations remained `OPTIMAL`, with identical status, objective, full primal
vector, and iteration count (`isequal`).

Machine-readable results:
[`zero-exact-representation-allocations-before.toml`](zero-exact-representation-allocations-before.toml)
and [`zero-exact-representation-allocations-after.toml`](zero-exact-representation-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=zero-exact-representation-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
function zero_exact_representation_probe(kind; count=128)
    T=kind in (:zero_float32,:underflow_float32) ? Float32 : Float64
    value=kind in (:zero_float32,:zero_float64) ? big(0)//big(1) :
        kind==:underflow_float32 ? big(1)//(BigInt(1)<<151) :
        kind==:underflow_float64 ? big(1)//(BigInt(1)<<1076) :
        kind==:nonzero ? big(3)//big(2) : big(1)//big(3)
    values=[isodd(i) ? value : -value for i in 1:count]
    pass=values->map(value->JSimplex._represent_exact(T,value),values)
    return values,pass
end

for kind in (:zero_float32,:zero_float64,:underflow_float32,:underflow_float64,:nonzero,:inexact_nonzero)
    values, pass = zero_exact_representation_probe(kind)
    println(measure_allocations(_ -> pass(values); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **1,087 assertions** and failed only
the four target allocation guards; both controls passed. The file contains
**1,091 new assertions**, all passing after the change. Existing allocation
budgets were not relaxed.

One hundred thirty-five direct scalar cases cover Bool, Int8, Int64, Int128,
BigInt, Float32, Float64, BigFloat and Rational{BigInt}, including zero, signed
integers, integer overflow, dyadic fractions and nonrepresentable thirds.
Results must preserve the requested type and exact value, or return `nothing`.

Thirty-two signed subnormal cases cover exact zero, quarter/half/three-quarter
rounding around the minimum subnormal, exact subnormals and halfway nonzero
rounding for Float32/Float64. Additional cases check maximum finite values,
overflow and nonzero half-ULP tails. BigFloat tests verify positive zero at
ambient precision 32/64/256, exact tiny nonzeros, and rejection of 256-bit tails
when the ambient precision cannot represent them.

Forty-eight complete doubleton models across four numeric types and signed
pivots produce zero alpha, cost, objective constant, matrix entry or row bound,
plus nonzero controls. They verify exact matrix/bounds/objective, sparse zero
removal, substitution ratios, primal/basis restoration, objective equivalence
and source preservation after ordinary output mutation. Probe result checks and
allocation guards cover all six helper batches.

The targeted suite passed **173,930/173,930 assertions** in 3m02.5s.

Independent differential review passed **4,771/4,771 assertions**. The full-model
comparison covered 144 models (132 doubleton, 12 basic), with 100 accepted and
44 unchanged results, 432 primal restorations, 576 basis restorations and eight
staged rollbacks. Another 515 direct helper comparisons covered all nine scalar
types, signed subnormal ties/underflow, overflow, rational infinities and BigFloat
ambient precisions 16/32/64/128/256. Baseline callers explicitly used renamed
baseline representation and bound-shifting helpers. All results, metadata,
stored representations and source-preservation checks matched. No findings.

The full project suite passed **193,427/193,427 assertions** in 7m17.1s.

Full-suite command:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
