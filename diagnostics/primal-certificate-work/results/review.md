# Independent review

A separate read-only reviewer inspected the complete production diff, the
comparison scripts, and the final numerical evidence. It ran no Julia process
and changed no files.

No numerical correctness blocker or remaining material unnecessary work/memory
cost was found. The review verified cache reset, unique internal row selection,
standalone compatibility, unchanged term order/finiteness checks, independent
bound decisions and exact fallback. Its suggestion to replace first-call
per-element appends with bulk resize/fill was applied before final validation.

Memory scales with problem rows and selected-row union, not update-chain length.
Allocated vector capacities can exceed logical lengths. Retained point-buffer
measurements are final-workspace footprints, not separately measured baseline
deltas. No basis solve, precision conversion, full matrix copy or safeguard
relaxation was added.

The reviewer independently verified all 100 expected external combinations,
reference objectives/input hashes, original-model certification flags, both
128-step cleanup event/state hash pairs, and all 12 stage timing ratios. It
highlighted the small consistency-only overhead and the Float32 fast-control
slowdown; both are explicitly documented rather than omitted.

The full runtime result has the expected optimum, 54,591 iterations, 194
refactorizations, original-model feasibility and matching event/state hashes.
The strengthened frozen-reference probe passed 720 explicit acceptance and
960 explicit rejection checks, including mutation of the owned matrix in a
column with nonzero primal value. Both final jobs exited successfully and
kept pinned sources unchanged.

Bounded cleanup runs are trajectory evidence. Their single baseline-first cold
pairs cannot support a cleanup speedup claim. Repeated warmed kernel results
support the certificate-specific gain; full solver speedup remains unproven.
