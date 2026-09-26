# Simplex performance follow-up

Base: `b69e266`. Work in progress; no default strategy change or general speed
claim. The [plan](../../docs/superpowers/plans/2026-09-26-simplex-performance.md)
records the user constraints and validation sequence.

## Native residual checks

Long residuals previously triggered arbitrary precision based on a pessimistic
length bound, even when the computed residual was zero. Float32 also silently
accumulated residuals in Float64. The new fallback uses compensated arithmetic
in the input scalar type, with an enclosure for both residual and denominator.
An inconclusive enclosure or exceptional numerical range retains the existing
BigFloat check. Basis factors and ordinary corrections stay in input precision.
Explicit precision recovery and the stronger legacy 256/512-bit last-resort
repairs remain separate.

Regression tests first failed the allocation bound twice (18 passing checks).
The completed focused run passed 593/593 checks, covering exact-input oracles,
normal and transpose refinement, precision, cancellation, exceptional ranges,
caller failures and staged pivot state. An intermediate integration failure
identified the Float32 quality cache's old hard-coded Float64 type; it was fixed
before that passing run. Full-branch validation is still pending.

The [microbenchmark record](native-residual.json) contains five warmed samples
of 1,000 calls for each type and orientation. On a synthetic 300-term residual,
Float64 medians improved from about 0.140 seconds to 0.00166 seconds per 1,000
checks (about 84 times), and allocations fell from 256,896 to 32 bytes per call.
Float32 stayed in Float32 but took about 1.6–1.8 times the former widened-check
time on this example (roughly 1.65 microseconds per check). This is a deliberate
working-precision tradeoff, not an unreported speedup. These small kernel
measurements do not establish complete-solver speed or solved coverage.

The implementation follows the compensated dot-product enclosure in
[Ogita, Rump and Oishi, Algorithm 5.8](https://www.tuhh.de/ti3/paper/rump/OgRuOi05.pdf),
with a conservative allowance for the componentwise scale's rounding.

## Consume only the required dual breakpoints

The legacy bound-flipping test sorted all eligible candidates before consuming
the prefix needed to repair the leaving violation. It now builds a heap in the
existing candidate buffer and extracts that prefix. The comparison preserves
the former stable ordering, including signed zeros and equal breakpoints. The
fallback to Harris and the treatment of exhausted/rejected candidates remain.

The 4,096-candidate allocation regression failed at 32,840 bytes before the
change and passes a 4-KiB ceiling after it. All 1,924 checks in the focused
breakpoint, ratio and dual-simplex suites passed, including full exhaustion,
ordered bound flips and all supported arithmetic types. Complete LP timings
and the final full-suite gate remain pending.

## Vectorized workspace validation

Repeated full-vector validity checks were a substantial cost in all three
legacy dual profiles. Hardware Float32/Float64 vectors now use a SIMD boolean
reduction: every value is checked, and steepest-edge weights must still be
strictly positive. Floating arithmetic and generic scalar checks are unchanged.
All 176 targeted checks passed, including invalid values at vector-block edges,
signed zeros, extreme finite values and the Dantzig weight-check exception.
The combined breakpoint/validity/ratio run passed 467/467 checks.

[Five warmed kernel samples](workspace-finiteness.json) show about 2.1–2.2 times
faster Float64 and 4.4 times faster Float32 checks at 63,009 and 420,526 columns,
with zero allocation in both versions. These are kernel measurements only.

### Bound the cost of long flip sequences

Pure heap extraction was 3.0–3.3 times faster for short prefixes but 3.3 times
slower when consuming all 4,096 candidates. After `max(32, n/16)` flips, the
implementation now sorts the remaining tail in place with the original-index
tie key. The added 128-candidate tests exercise this transition for Float32,
Float64, BigFloat and exact rational arithmetic; all 28 breakpoint checks pass.

[All three measurements](dual-breakpoints.json) are retained. The hybrid is
3.1–3.6 times faster for the measured short prefixes with zero allocation.
Full exhaustion still costs about 2.1 times the old full sort (0.181 versus
0.085 milliseconds per call). This remains a measured limitation, not a claim
that every ratio test got faster. It will be weighed against complete solves.
