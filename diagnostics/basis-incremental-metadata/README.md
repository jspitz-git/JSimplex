# Incremental triangular metadata

Baseline: a5fdf58 (selective preparation). This change retains the proven
unchanged prefix of the active-upper-column list and clears only populated
FT/SS incidence rows. Invalidation precedes coefficient mutation and accumulates
the earliest changed column. Generic arithmetic and sparse graph invalidation
remain unchanged.

## Validation

The triangular, selective-preparation and new metadata suite passed 32,732
assertions. Independent review found no blocking defect; an additional regression
covers mutation after partial invalidation without an appended update.

Three alternating paired repetitions replay 320 exchanges for all three managers.
Both sides use ordinary auxiliary FTRAN. Outputs, stored coefficients, permutations
and histories agree exactly; independent scaled residual checks pass at 20, 80,
160 and 320 updates. First exchange is excluded from timing. Julia 1.13.0,
Linux aarch64, one Julia and BLAS thread. Ratios below are medians of paired total
update + two-FTRAN + BTRAN times (candidate / baseline), not whole-solver speedups.

| History | Manager | Ratio |
|---|---|---:|
| ft-late.toml.history.30000.bin | BartelsGolubFactorization | 0.976 |
| ft-late.toml.history.30000.bin | ForrestTomlinFactorization | 0.956 |
| ft-late.toml.history.30000.bin | SuhlSuhlFactorization | 0.989 |
| ft-late.toml.history.40000.bin | BartelsGolubFactorization | 1.006 |
| ft-late.toml.history.40000.bin | ForrestTomlinFactorization | 0.978 |
| ft-late.toml.history.40000.bin | SuhlSuhlFactorization | 0.981 |
| medium-history.bin | BartelsGolubFactorization | 0.894 |
| medium-history.bin | ForrestTomlinFactorization | 0.933 |
| medium-history.bin | SuhlSuhlFactorization | 0.795 |

Large-basis measurements vary noticeably between repetitions; raw samples are
retained. No claim about iteration count or end-to-end speed follows from these
fixed histories. External corpus passed in the predecessor (80 solves); arithmetic
is unchanged here. The predecessor's normal-compiled full-suite attempt timed out
in LLVM compilation; this stage does not claim a full-project test pass.

Reproduction: run reproduce/paired.jl with JSIMPLEX_BASELINE_SOURCE pointing at
baseline src, JSIMPLEX_BASELINE_REVISION=a5fdf58, JSIMPLEX_PROBE_REPEATS=3,
then output directory and history paths as arguments. Histories are identified by
SHA-256 in the raw TOML results and are not redistributed.
