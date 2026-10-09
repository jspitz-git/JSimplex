# Legacy primal fixture repair

Baseline: `6bf7d2f`. This closes the 25 failed assertions and two test errors
identified by `diagnostics/dual-residual-work`. Only tests and diagnostics
change; no production source, tolerance, safeguard, precision or pricing rule
is changed.

## Causes

| Historical expectation | Failures | Cause and repair |
|---|---:|---|
| Entering value absorbs a snapped structural bound | 17 | Nonfixed structural values may now be retained. Test both mandatory fixed-variable snapping and allowed nonfixed retention. |
| Sole/exhausted unsafe candidates return a numerical termination | 4 failures + 2 errors | The original fixtures no longer require snapping and their zero steps are usable. Make the leaving variable fixed to retain the unsafe-path test. The errors were `.status` accesses on the valid `nothing` continuation, not exceptions from the solver. |
| Retry selects a later safe candidate, including beyond eight candidates | 2 | Fix the leaving variable so earlier directions really amplify the forced snap. Add separate retained-value controls. |
| Refresh has the `refactor_residual` reason | 2 | Native row correction leaves a mismatch with the FTRAN pivot, reported as `refactor_pivot`. Keep the one-refresh and FTRAN-work limits, and check original feasibility. |

Commit `47d06ff` introduced structural value retention, explicitly excluding
fixed variables. The older fixtures retained an unbounded opposite bound and
therefore no longer exercised their intended forced-snap branch. They were
not updated when that contract changed.

The fixture probe compares the exact same equations with a nonfixed versus
fixed leaving variable. Nonfixed cases preserve the entire point, with zero
row residual and original primal feasibility. Fixed cases reject the sole or
exhausted unsafe directions without changing the point/basis, or select the
safe fourth/twelfth column. This establishes the reason to change the fixture;
it is not an arbitrary relaxation of an assertion.

The per-bound regression still forces snapping in half its cases, across both
Float32/Float64, both signs, and PFI/FT/SS/BG. The other half checks the retained
point. Candidate tests retain cancellation, cleared rejection lists, exhaustion,
and search beyond eight candidates. Paired nonfixed cases independently check
original feasibility and the row equations. The pricing fixture takes five
FTRAN calls for both 16 and 256 columns, below its retained limit of twelve.

## Verification

One numerical Julia process at a time, one Julia/BLAS thread, existing 8 GiB
VM limit / 6 GiB available-RAM floor / 1 GiB swap ceiling. The established
`dual-residual-work/reproduce/run.py` records source/script hashes and process
outcomes. Raw attempts: `.superpowers/legacy-suite-repair` in the preserved
`simplex-shared-work` checkout. Compact evidence is in `results/`.

- Fresh pre-edit replay: 313 passed, 25 failed, two errors.
- Corrected three-file replay: 520/520 passed with `--compile=min`.
- Adjacent bound-retention, point-recovery, direction-price, correlated-pivot
  and roundoff safeguards: 2,262/2,262 passed with `--compile=min` (includes
  the three corrected files).
- Mutation checks replace one method in a fresh process only, leaving all
  source files unchanged. Returning to accumulated bound violations produces
  64 failed assertions; disabling permitted retention produces 29. Both exit 1
  intentionally. These runs prove that the revised tests detect the prohibited
  behaviors; they are not solver regressions.
- Normal-compilation replay: 520/520 passed (`-O2`, 91.2 seconds in the test
  set, including compilation). This is not a solver-speed measurement.
- `reproduce/audit.py` checks all eight attempt outcomes, exact failure
  counts, successful summaries, probe equivalence and every production-file
  hash against `6bf7d2f`. All runs preserve their pinned sources.

The initial probe was run against the original fixture defaults. It is kept
as `probe-original-v1.jl`; that script belongs to baseline `6bf7d2f`. The final
probe explicitly requests nonfixed construction before applying the fixed
variant, so it remains reproducible with the repaired fixture defaults.

No full external solve or speed benchmark is needed for this test-only change:
all production file contents remain identical to the already validated
baseline. The full project suite was not rerun; its previous compilation
limit and coverage limitation remain. This report closes the specifically
identified 25 failures/two errors, not every possible project-wide issue.

## Work and memory review

There is no change at setup, refactorization, iteration, candidate, recovery or
certification frequency in production: no new scans, solves, conversions,
allocations or retained fields. Tests add only small paired examples and
independent feasibility assertions. The pricing-work cap remains enforced.
Independent review confirms that forced-snap rejection coverage is retained,
while nonfixed retention is checked rather than disabled. Review also prompted
the explicit probe parameter and corrected description of the pivot mismatch
following native row correction.

## Reproduction

From the preserved experimental checkout, with no other Julia process:

```sh
python3 diagnostics/dual-residual-work/reproduce/run.py /tmp/legacy-fixtures-new 300 --compile=min diagnostics/legacy-suite-repair/reproduce/focused.jl
python3 diagnostics/dual-residual-work/reproduce/run.py /tmp/legacy-fixtures-compiled-new 300 -O2 diagnostics/dual-residual-work/reproduce/legacy-triage.jl
python3 diagnostics/dual-residual-work/reproduce/run.py /tmp/legacy-mutation-new 180 --compile=min diagnostics/legacy-suite-repair/reproduce/mutation.jl sum
```

Use a new output directory for every attempt. The last command intentionally
fails assertions. The local Julia wrapper, guard and environments must exist;
Manifest and LocalPreferences are not committed.
