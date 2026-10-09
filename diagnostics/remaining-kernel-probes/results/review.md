# Independent review

A separate reviewer performed a read-only review of the probes, README and raw
reports. It ran no Julia processes and edited no files.

No blocker was found. Production sources are unchanged from `21a3fae`.
The reviewer independently checked eight successful jobs, two preserved
instrumentation failures, 240 matching manager-vector hashes, 14 fusion cases,
eight row-locality cases, and two complete unique 24-case PFI grids. Medians,
zero allocation results, residual bounds, runtime fingerprints and principal
attribution percentages match the reports.

The inspected prototypes preserve numerical operation order. Correction fusion
validates before mutation. Row indexing preserves per-row CSC term order. PFI
bounds-check removal is limited to validated, fixed experimental payloads.
This does not establish production readiness for mutable payloads, all aliasing
paths or other precisions. Validation is outside PFI timing; future production
invariant maintenance must be included in its work assessment.

The computational-work/memory review found no unnecessary production work or
retention because production code is unchanged. The row-index experiment adds
27,838,696 retained bytes for weak medium-case gains and regressions elsewhere;
rejecting deployment is justified. Instrumentation changes code generation and
must not be interpreted as a whole-solver timing comparison.

Review findings addressed before completion:

- BTRAN backward error uses `opnorm(B,1)`, the infinity norm of the transposed
  operator, rather than `opnorm(B,Inf)`.
- Row-index setup separates first compilation from warmed setup measurements.
- The README explains that fusion timing includes identical reset copies.
- The detailed manager pass includes specialized composed-row helpers omitted
  from the first attribution pass; both reproduce baseline vectors.
- PFI batch calibration is described as targeting about 10 ms in the baseline
  arm, not guaranteeing a minimum duration (the shortest median is about
  7.51 ms).

No unsupported full-solve speedup or new regression-suite pass is claimed.
