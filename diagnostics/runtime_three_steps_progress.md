# Runtime follow-up: approved steps 1–3

Scope: reuse lookup positions; restrict FT/SS trailing-column traversal;
cache Markowitz column maxima within one pivot search. Preserve arithmetic
order, candidate/tie order, mixed precision, errors, ownership and existing
allocation budgets. Continue the user's existing working tree, including the
uncommitted first batch; do not recreate or discard those changes.

Baseline: complete source snapshot at /tmp/jsimplex-runtime-three-baseline/src.
The earlier runtime_before_after.toml identifies this baseline by its after hashes.

- Step 1: complete — 300 lookup assertions and existing column/history reuse tests passed.
  basis_runtime_step1.toml records 216 exact factor/history checks and 810 timing/check
  assertions. Positions stay valid until the corresponding column mutation.
- Step 2: complete — row incidence can remain read-only within one FT/SS elimination,
  because only the target row changes; that row is never a later pivot row.
- Step 3: complete — raw column maxima only; invalidate between pivot searches.
- Final verification: complete — exact differential factor histories and solver
  trajectories, isolated timings, 224,921 production and 456 development/JET checks.

Implementation remains local and sequential. Fresh independent review after all
three changes. Commit and push subsequently requested by the user after verification.

Step 2 decision: build row incidence lazily for spans >=16 with average stored
column length <= span/4; keep range traversal for dense/short updates to avoid
index setup overhead. Retain all row buffers across dimension shrink.

Step 2 evidence: 420 new assertions and 11,963 existing column/history assertions
passed. Step2 probe: 216 exact factor/history comparisons at n=32, 810 timed-case
assertions; band n=128 about 2.1x, n=512 about 6.5x (first cache growth included).
Fixed-width rational fixture limits chain depth to avoid denominator overflow;
arbitrary-precision rational retains the full 32-row chain.

Step 3 focused tests: 90 new cache/precision/storage assertions and 1,337 existing
Markowitz generic/workspace assertions passed. The first microbenchmark showed
common-case overhead, so the final full column scan reads cached maxima but does
not store new ones (there is no later consumer). Cache helper is inlined.

Independent final source review found no production issues; requested explicit
SS last<n branch coverage added (reach=24 in n=32, cross-boundary row incidence).
Earlier batch explicitly outside that review, already reviewed previously.

Final differential checks passed: 432 packed factor/history comparisons; 810 paired
kernel assertions; 192 solver traces / 1,152 states, 32 complete outcomes, all exact.
Whole-solver timings fall within unchanged-control variation; no global speedup claim.
Final complete production suite: 224,921/224,921 (9m29.9s), exit 0.
Final complete development/JET suite: 456/456, exit 0.

Final verification commands and numerical/timing details are recorded in
basis_runtime_report.md. Existing allocation budgets unchanged; no numerical
comparison failed. Source-hash chain checked across all incremental and combined
artifacts. git diff --check passed. Changes remain in the authorized working tree.
