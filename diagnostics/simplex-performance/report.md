# Simplex performance follow-up

Base: `b69e266`; final production changes: `6a88469`. The default strategy and
feasibility tolerances are unchanged. The
[plan](../../docs/superpowers/plans/2026-09-26-simplex-performance.md) records
the user constraints and validation sequence. All final regression gates passed.

## Complete-solver results

The [measurement record](solve-measurements.json) contains all twelve
baseline/current configurations. Fast0507 has a full warmup and three measured
repeats per configuration; the table uses their medians. Runtime and medium
each have one small AFIRO compilation warmup and one measured attempt with a
360-second limit. Remaining compilation is not separately excluded for those
large cases. All jobs ran sequentially with one Julia and one BLAS thread.

| Input and method | Baseline seconds | Current seconds | Result in both versions | Baseline / current iterations |
|---|---:|---:|---|---:|
| fast0507 dual | 10.090 | 8.255 | Optimal, original primal check passes | 6,624 / 6,624 |
| fast0507 primal | 12.947 | 12.688 | Optimal, original primal check passes | 4,806 / 4,806 |
| runtime dual | 360.013 | 360.002 | Time limit | 73,091 / 74,146 |
| runtime primal | 3.314 | 3.270 | Numerical error: primal feasibility lost | 767 / 767 |
| medium dual | 360.002 | 360.008 | Time limit | 28,946 / 31,242 |
| medium primal | 360.004 | 360.004 | Time limit | 20,807 / 21,619 |

Fast0507 dual takes 18.2% less time, with the same iteration/refactorization
counts and objective. Cumulative allocations fall from approximately 1.238 GB
to 0.843 GB. The roughly 2% primal difference is small. More iterations within
a fixed budget on medium do not establish a reduction in completion time.
Solved coverage on these three inputs has not improved: runtime and medium
remain unresolved. Medium's observed peak process RSS is at most 5.19 GiB,
including compilation; its hundreds of gigabytes of cumulative allocations
are not simultaneous memory use. There was no observed out-of-memory failure.

## Final validation

All four final gates passed sequentially against the frozen production changes
at `6a88469`. The [verification record](verification.json) retains exact commands,
elapsed times, source/test inventory and harness hashes, log hashes and actual
test summaries. Source/test and harness integrity checks passed before and after
each gate.

| Gate | Passed / total |
|---|---:|
| Complete native production suite | 254,083 / 254,083 |
| Development suite, 69 testsets | 1,208 / 1,208 |
| JET checks, included in development total | 249 / 249 |
| Numerical suite compared with GLPK | 6 / 6 |
| External corpus checks | 104 / 104 |

The production suite ran in normal Julia compilation mode, with a wrapper that
only adds per-file progress messages to the actual `test/runtests.jl` inventory.
Its wall time was approximately 125 minutes; this is a validation cost, not a
solver performance comparison. The complete source/test inventory remained
`bd55d3811a2c386f621efc03ec151042faea03403fb54d34811f0e30e427791e`.

The [external corpus record](quick-corpus.json) contains 32 successful solves:
NetLib afiro, adlittle, kb2 and sc50a, plus MIPLib pk1, flugpl, stein9inf and
markshare_4_0, each with primal/dual and legacy/adaptive configurations. Every
solve passes the original-input primal check and matches a hash-matched GLPK
reference objective. MIP cases are LP relaxations. These are correctness checks,
not warmed performance measurements, and do not remove the runtime/medium gaps
reported above. Large excluded inputs were not solved.

## Native residual checks

Long residuals previously triggered arbitrary precision based on a pessimistic
length bound, even when the computed residual was zero. Float32 also silently
accumulated residuals in Float64. The new fallback uses compensated arithmetic
in Float32 or Float64 itself, with an enclosure for both residual and denominator.
An inconclusive enclosure or exceptional numerical range retains the existing
BigFloat check. Basis factors and ordinary corrections stay in input precision.
Explicit precision recovery and the targeted legacy 256/512-bit small-pivot
and lost-feasibility repairs remain separate. Existing BigFloat residual
checks retain their previous wider evaluation; this change targets the hardware
floating-point paths.

Regression tests first failed the allocation bound twice (18 passing checks).
The completed focused run passed 593/593 checks, covering exact-input oracles,
normal and transpose refinement, precision, cancellation, exceptional ranges,
caller failures and staged pivot state. An intermediate integration failure
identified the Float32 quality cache's old hard-coded Float64 type; it was fixed
before that passing run. Final full-branch validation is recorded above.

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
and final full-suite validation are reported above.

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
0.085 milliseconds per call). This remains a measured limitation, even though
the complete fast0507 dual solve improved.

## What the profiles establish

The [baseline diagnostic records](profiles.json) retain all five observations.
Fast0507 with the initial update interval 20 completed 6,624 steps and 90
refactorizations; interval 500 took 6,884 steps and 16 refactorizations. The
paths differ, so this is not a matched basis-kernel comparison. PFI solves
became more visible with the longer history but were a minority in these
profiles. Repeated full-vector checks, sparse pricing and breakpoint sorting
were substantial costs. The adaptive profile spent significant time evaluating
wide residuals and repeatedly refactorizing.

Runtime and medium were first profiled as 60-second diagnostic prefixes. They
are not completion runs. Medium loaded 586,972 rows, 420,526 columns and
1,446,423 nonzeros; no memory exhaustion was observed. Its 31.4-GB allocation
counter is cumulative allocation, not resident memory. These profiles do not
establish that all long-history update implementations are efficient, nor that
all old stabilization techniques are unnecessary. No feasibility safeguard or
configured tolerance was removed, and no basis-update backend was rewritten
without evidence that it was the dominant measured cost.

The [review and repair record](review.md) explains the sparse audit regression
caught before final validation. Kernel measurements above belong to their
individual feature stages; final solve records identify the tested production
fingerprint separately.

### Longer runtime observation

A separate [360-second runtime diagnostic](runtime-diagnostics.json) reaches
74,121 iterations and 12,245 refactorizations. Refactorization timers account
for 165.54 seconds, about 46% of elapsed time. FTRAN takes 25.19 seconds, BTRAN
24.48 seconds and pricing 18.47 seconds. Timers can nest and are not an additive
partition of total runtime. This instrumented run is distinct from the primary
uninstrumented comparison above.

There are 3,964 residual-triggered refactorizations and 8,280 interval-triggered
ones, plus two initialization/other refactors. The longest observed update chain
has 160 entries. The legacy dual solver already adjusts its interval: repeated
updated-basis repairs shorten it, while clean cycles allow it to grow again.
The new adaptive-policy flag is not required for this older behavior. These
results identify frequent refactorization as a major cost later in runtime,
which the short prefix alone did not establish. They do not establish that
long update histories are cheap on every input.

### Recovery and policy experiments

The [primal recovery probe](primal-recovery-probe.json) retains runtime's failed
workspace after the solver returns and recomputes it with a fresh native factor.
Primal infeasibility remains `3.328600000309123e-5`, despite discarding eleven
updates. A simple extra refactorization would therefore not repair this failure.
This is a negative diagnostic result, not proof that the exact basis itself is
infeasible: both native calculations could share conditioning error. No new
post-failure retry was added from this unsupported hypothesis.

[Policy experiments](policy-experiments.json) also retain unfavorable results.
Enabling stable ratio tests, incremental primal updates and sparse pricing
together on the legacy core causes numerical failures on fast0507. That bundle
does not isolate the responsible feature. The full adaptive dual configuration
also fails or reaches its 60-second diagnostic limit. Neither was promoted to
the default. These short diagnostic runs are not runtime completion attempts.

The next evidence-driven targets are the legacy refactorization interval's
response to residual repairs, matched-history basis-kernel replay, and the first
primal pivot that loses feasibility. Sparse/hypersparse policies should be
isolated individually from ratio-test and incremental-update changes. These
are follow-up investigations, not claims of improvements delivered here.

## Reproducing the measurements

Scripts under [reproduce](reproduce) are the exact small kernel, profile and
solve harnesses used here. Run with Julia 1.13, one Julia/BLAS thread and a
24-GiB address-space limit. `solve-bench.jl` takes input, algorithm, strategy,
time limit, measured sample count and output TOML; its optional seventh
argument is `default` (or the diagnostic `selected` policy), and eighth is
`full` for a full-case warmup or `afiro` for a small compilation warmup. Parsing
is outside solve timing. The output records both solver and outer elapsed time,
source/input hashes, allocation and peak process RSS. Peak RSS is cumulative
for that process and includes compilation. Large-case single observations are
not repeat distributions. No timing or sampling diagnostics are enabled during
these complete solves.

The canonical production fingerprint hashes each relative path, a NUL byte and
its contents for `Project.toml` and `src/**/*.jl`, sorted by the full relative-path
string. Baseline: `b38a8a2f5c6e69515ee55d740f3846c76f285f56868ff521f02bf2858d069cf8`;
final: `b68c5dcc1d933c4e4816bee36f432630663c6ac4f15201094e7d4da5521ed6d4`.
Kernel records may identify an earlier feature commit, as explicitly recorded.
The complete regression gate separately fingerprints source, tests and developer
checks; those broader hashes are not directly comparable to production hashes.

The runtime diagnostic and primal recovery scripts are also included. They use
the original `/home/jspitz/mps/runtime.mps` path and write TOML beside the script.
Run them from the repository root with `--project=.`. They are diagnostic tools,
not default recovery behavior or benchmark configurations.

## Independent HiGHS observations

The [reference record](highs-reference.json) retains one run per case and method
using the installed HiGHS 1.15.0 C API: one thread, simplex, presolve enabled,
explicit LP relaxation and a 360-second limit. Algorithm choices follow the
[HiGHS option definitions](https://ergo-code.github.io/HiGHS/dev/options/definitions/).
Reading the input is outside the recorded `Highs_run` time.

The exact reference and certification scripts are included under `reproduce`.
To repeat them in this environment, copy them to `.superpowers/performance/`,
run `highs-reference.py` from the repository root, then run `certify-highs.jl`,
`medium-reference-check.jl` and `medium-reference-exact.jl` with `--project=.`.
The Python script names the installed HiGHS library explicitly; another machine
must supply its own matching library path. Saved binary solutions are local
artifacts, identified by SHA256 in the reference record.

| Input | Dual seconds | Primal seconds | Independent original-input primal check |
|---|---:|---:|---|
| fast0507 | 2.13 | 9.88 | Both pass |
| runtime | 18.27 | 80.85 | Both pass |
| medium | 108.53 | 224.12 | Both fail the strict absolute `1e-7` check |

HiGHS reports all six as optimal. The distinction in the last column matters:
exact arithmetic on the stored input coefficients finds one medium row
(index 481811) violated by approximately `1.78e-7` in both solutions. Ordinary
Float64 activity accumulation hides that violation; only three rows needed
exact fallback inspection. Column bounds pass and no nonzero input coefficient
is at or below `1e-9`. The record retains these findings alongside HiGHS's own
reported infeasibilities. Medium's reference times are context, not accepted
same-tolerance solves. This does not justify weakening JSimplex's tolerance.
