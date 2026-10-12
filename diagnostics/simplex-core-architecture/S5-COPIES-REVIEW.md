# S5-C final independent review

Reviewer: fresh gpt-6-astra/high, s5_copy_final_review, read-only complete change
from diagnostic base83fab02. Verdict: ACCEPT narrow S5-C; critical0, important0,
minor0. No fixes or second review required. No numerical reruns by reviewer.

## Numerical and work/memory findings

The concrete Vector storage-range predicate handles real element stride (including
reference layouts), empty buffers, multiplication overflow and nonnegative pointer
differences under GC preservation. Unknown/union/zero-stride cases fall back to
both copies. First-copy publication and later exception/event order are preserved;
source self/partial overlap and detached destinations retain the legacy copies.
No weakened numerical safeguard or certificate reuse was found.

The reviewer found no unnecessary added work or retained memory: cold restoration
adds O(1) metadata tests in exchange for at most one O(N) cost copy. No new full
scan, basis solve, conversion, scratch allocation or retained cache; no dependence
on matrix nonzeros or update-chain length. All four active bound copies remain.
The legacy oracle matches the old body; actual-body RED/GREEN work counts and
source hashes for GREEN/focused/cost/trajectories were checked independently.

The reviewer recomputed all312 timings and allocation counts. All samples have
compile0 and GC0. Equal allocation-event counts do not establish byte equality:
144/156 pairs differ. Small/detached timing spread remains explicitly reported.
Acceptance is of the proved work reduction with bounded numerical coverage, not
universal elapsed improvement, whole-solver speedup or allocation-byte equivalence.

## Declined scopes and author rulings

- The then-untracked master driver and future integration result were outside the
  reviewed package. Author subsequently ran master-1:668/668 assertions,12audit
  gates,592independently checked pins, actual main source and user hashes verified.
  Production88a2411 was cherry-picked as mastere7014fb. This does not extend the
  independent review to unreviewed future changes.
- Historical full CI and the complete S6 gate were outside acceptance. They remain
  unresolved; CI stays manually disabled. S6-A begins with existing-log inventory.
- Whole-solver speed, natural perturbation frequency and unmeasured combinations
  remain unqualified. No additional benchmark was requested to erase uncertainty.

Separate host call confirmed runner368680/child368681/driver368668 absent, no Julia,
boot20de7dde-704e-41c8-bee7-b8511c0a86b0. Raw attempts and environment are preserved.
