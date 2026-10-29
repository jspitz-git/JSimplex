# Independent review: native quality experiments and integration

Reviewers: native_quality_review (fresh prelaunch context) and native_quality_integration_review (fresh measurement/production review context), independent of implementation. They ran no Julia and modified no files.

## Final gate: QUALIFIED ACCEPT exact c0fa748ffa61ccb7c1caaf248c40324f60bc737b for publication/push

No blocker was found within native A scope. Actual master completed all19 files:54014passed,2failed,0errors/54016. Both failures were unchanged Rational residual-allocation gates at581, residual601 and outer602. Candidate failed residual601 and dual709. Baseline235 failed only outer602. Exact candidate failures were NOT reproduced at baseline. Neither candidate/master focused suite nor broad full suite passed. These allocation outcomes remain unresolved, without a waiver, gate change or promotion of old717.

Acceptance is scoped and source-backed: both timed Rational kernels and helper closure are unchanged from235 and cannot invoke A's new validator. All native numerical/recovery/ownership checks passed. Native measurement864matched pair groups/72fixtures has equal bytes/events in every pair and zero measured compilation/recompilation/GC. A per-fixture median ratios0.794–1.019 support sparse improvement, dense parity/noise only; no end-to-end or invalid-path timing claim.

AGENTS work/memory conclusion: finite-input validation scan counts remain the same (CSCnnz or densematrix, x, rhs, two scratch vectors), with no new solves, copies, conversions, workspace/cache data or dimension/chain-dependent retention. No unnecessary new finite-path computational/memory work was found. Invalid native vectors now incur remaining-tail reads, a disclosed bounded exceptional-path cost.

The reviewer verified commit/actual3blobs, clean master source/tests and all532 master pin hashes/resolutions; elapsed1560.945s,maxRSS3159732KiB,no timeout/swap, postflight no conflicts. Original pin mappings remain explicit, with no retroactive source pins. The final approval retains every failed raw record and prohibits all-pass/old-gate-resolution claims.

## Admission and fixes

Initial concrete measurement review required complete isolated-module dependencies, no shared-exception-as-success, scratch comparisons for every measured fixture and warmed states, separate warmup compilation records, and supervisor acceptance. Existing compensated kernel text was restored unchanged before launch. Final admitted driver SHA2562ecd2aacaa9cb405fc87c6d4a6215028ffa2792adb84dedd3ceaaf33728e730c.

Production review required helper placement before solve_quality!'s docstring, fixed before commit. B/AB rejected for short sparse BTRAN regressions; no production B variant or tuning. Review corrected the author's excessive442-file gate to19 complete affected files without weakening assertions. Full attempts remain wall_time/interrupted INCOMPLETE. One unchanged235 two-file baseline was admitted to investigate real Rational failures, with no candidate retries/fishing. Final scoped acceptance retains the unreproduced allocation qualification.

No deferred minor or unresolved finding within the native implementation was reported; legacy allocation qualification and absent full-suite completion are explicit limitations.
