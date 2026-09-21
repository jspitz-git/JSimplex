# Generic Markowitz allocation counterfactuals

Read-only investigation for allocation-plan step 5. Production source, tests,
Project files and git state were not edited. The frozen baseline is
`/tmp/jsimplex-markowitz-after-csc.jl`; each alternative is evaluated in its own
Julia module, leaving the loaded package methods untouched. The probe is
`diagnostics/markowitz_generic_probe.jl` and raw results are in
`diagnostics/markowitz_generic_counterfactual.toml`.

Command: `julia --startup-file=no --compiled-modules=existing --project=dev diagnostics/markowitz_generic_probe.jl`.
BLAS uses one thread. Each fresh backend constructor is warmed twice and measured
three times, with input construction and explicit GC outside measurement.
These are direct constructor counts, not a reused-workspace refactorization
claim. Other Julia workloads were running; timing is informational only.

## Recommended small changes

### Markowitz-local BigFloat magnitude

Use a Markowitz-local helper so other factorization and solver paths remain
outside this change's scope:

```julia
_markowitz_magnitude(value::Real) = _pivot_magnitude(value)
function _markowitz_magnitude(value::BigFloat)
    signbit(value) || return value
    result = BigFloat(precision=precision(value))
    ccall((:mpfr_neg, Base.MPFR.libmpfr), Cint,
          (Ref{BigFloat}, Ref{BigFloat}, Base.MPFR.MPFRRoundingMode),
          result, value, Base.MPFR.MPFRRoundNearest)
    return result
end
```

Replace only the four magnitude calls in the Markowitz implementation. Julia's
generic `abs(x::Real)` uses eager `ifelse(signbit(x), -x, x)`, so the old path
constructs a negated BigFloat even when it returns the original positive value.
The old path also enters `setprecision` for every candidate. The proposed
negative branch allocates exactly one result with the input's stored precision.
MPFR negation is exact at that precision; explicit nearest rounding therefore
matches all tested ambient rounding modes. The positive branch returns the
same original object the baseline returns.

Ownership audit: column maxima and best magnitudes only retain and compare
references. The threshold helper allocates its own `product` and mutates only
that product. No caller mutates a returned magnitude. Negative results own fresh
MPFR storage. Keep these rules if adding future reusable scalar scratch space.

### One private elimination zero

Create `entry_zero = zero(T)` once after the sparse/dense early exits, then use it
for the eager `get(rows[row], column, entry_zero)` fallback and the three pivot
entry-deletion call sites. Arithmetic treats this value as read-only; deletion
only checks `iszero`, never stores it. A constructor-local value is simplest and
cannot escape into caller-owned input or reusable output slots.

Do not replace the update with `-multiplier * upper_value` on missing entries:
that changes arithmetic grouping and potentially floating signed-zero behavior.
Retain the original `entry_zero - multiplier * upper_value` operation.

### Rational{BigInt} division by integer ten

This independent specialization avoids constructing `Rational{BigInt}(10)` and
uses rational/integer division, which also avoids rational/rational denominator
work:

```julia
_markowitz_threshold_pass(magnitude::Rational{BigInt},
                          column_maximum::Rational{BigInt}) =
    magnitude >= column_maximum / 10
```

Keep the specialization restricted to `Rational{BigInt}`. Changing intermediate
arithmetic for fixed-width rationals could change overflow behavior.

## Optional independent rational column-threshold cache

Cache only within each visited column's existing doubleton or general scan;
there is no persistent cache or invalidation state. Replace both occurrences of
`column_maximum = _markowitz_column_maximum(column_data)` with
`column_maximum = _markowitz_column_threshold(_markowitz_column_maximum(column_data))`,
then replace their candidate predicate with `_markowitz_candidate_pass`:

```julia
_markowitz_column_threshold(x::Real) = x
_markowitz_column_threshold(x::Rational{BigInt}) = x / 10
_markowitz_candidate_pass(x::Real, m::Real) = _markowitz_threshold_pass(x, m)
_markowitz_candidate_pass(x::Rational{BigInt}, threshold::Rational{BigInt}) =
    x >= threshold
```

The singleton-row path can keep calling `_markowitz_threshold_pass` directly.
No dictionary mutation occurs inside a scan, so its column maximum stays valid.
The rational result is exact and equivalent to computing the division for every
candidate. Float32/Float64 and BigFloat use the original predicate through
dispatch. This requires two loop-site edits and the helper dispatches, but no
pivot-selection algorithm or tie-breaking change.

## Precision and scope traps

- Keep the existing BigFloat exact `magnitude * 10 >= maximum` implementation.
  Dividing the maximum at ambient precision is wrong for stored higher-precision
  inputs. Multiplying by ten at ambient precision has the same defect.
- Plain `-value` or `abs(value)` without the stored-precision guard rounds
  negative high-precision inputs when ambient precision is lower.
- Do not convert BigFloat values to exact rationals to compare thresholds: huge
  binary exponents can cause allocation proportional to the exponent.
- A future reusable BigFloat threshold product must grow to at least
  `max(precision(magnitude), precision(maximum)) + 4` and must remain private.
  This investigation deliberately does not propose mutable-arithmetic rewrites.
- Retain `signbit`, which handles negative zero and negative NaN consistently;
  `value < 0` would handle them differently.
- Allocation byte totals for Rational{BigInt} can vary slightly between isolated
  variants with identical allocation counts, because GMP capacity differs. Do
  not interpret those small byte differences as an improvement.

## Verification

Each alternative is checked against the baseline for sparse pivot count, row and
column orders, diagonal values, lower/upper indices and values, dense LU factors,
and unchanged CSC input. Fixtures cover Float64, BigFloat and Rational{BigInt},
16 and 32 rows, band and fill patterns.

Additional checks cover stored 256-bit BigFloat values under ambient 24, 128 and
512 bits, nearest/up/down/toward-zero rounding, positive and negative zero,
infinities and NaNs, million-bit binary exponents, magnitude precision and
identity, unchanged ambient precision, and negative-result mutation isolation.
Exact rational thresholds cover ordinary and boundary values, huge integers,
tiny fractions and positive infinity. The existing production regression suite
was not altered; integration still needs its normal focused checks.

## Measured 32-row cases

All 5,703 counterfactual checks passed. Columns show bytes / allocation count.

| Variant | BigFloat band | BigFloat fill | Rational{BigInt} band | Rational{BigInt} fill |
| --- | ---: | ---: | ---: | ---: |
| baseline | 135,040 / 2,237 | 1,986,736 / 40,911 | 190,368 / 4,382 | 2,677,504 / 80,601 |
| zeros | 124,768 / 2,130 | 1,957,552 / 40,607 | 177,440 / 3,954 | 2,643,456 / 79,385 |
| magnitude | 88,384 / 995 | 933,552 / 9,631 | 190,368 / 4,382 | 2,677,824 / 80,601 |
| rational10 | 135,040 / 2,237 | 1,986,736 / 40,911 | 181,360 / 4,274 | 2,344,800 / 76,249 |
| rational_cache | 135,040 / 2,237 | 1,986,736 / 40,911 | 181,360 / 4,274 | 1,821,072 / 56,801 |
| combined | 78,112 / 888 | 904,368 / 9,327 | 169,264 / 3,846 | 1,787,056 / 55,585 |

`rational_cache` includes integer-ten specialization; `combined` includes zero, magnitude and rational caching. Float64 counts and bytes are identical across all variants: 43,264 B / 525 allocations (32-row band) and 55,632 B / 486 allocations (32-row fill).
