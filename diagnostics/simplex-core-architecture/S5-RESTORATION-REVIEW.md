# S5-B final independent review

Reviewer: fresh gpt-6-astra, s5_restoration_final_review, read-only range
fb56929..ef9749d. No numerical reruns, edits or independent host inspection by reviewer.
Verdict: accept the census/ownership conclusions and diagnostic package with one
important next-plan correction. No critical or additional minor findings.

## Important finding and one-pass resolution

S5-C plan and report incorrectly prescribed Base.mightalias as sufficient proof
that a Vector source cannot overlap its destination. Julia compares storage IDs;
offset unsafe_wrap vectors can overlap despite distinct IDs. Two partial-overlap
memmoves need not be idempotent. Author alias-probe-1 independently reproduced
four wrong skips, then checked a diagnostic range predicate in10Float64cases.
Exit0/all12audit checks/586pins/source verified; raw evidence preserved.

Plan/report now require a proven contiguous storage-range predicate covering
actual element stride/reference layout, empty buffers, overflow-safe lengths and
address arithmetic, GC preservation, or retaining the duplicate if proof fails.
No production optimization exists. All-scalar implementation RED/GREEN and cost
gates remain mandatory. One fix pass completed; no second review requested.

## Numerical and computational review

Controls precede instrumentation; parsed arithmetic and original copy calls are
preserved.144selected-state/event pairs match;21audit gates pass. Outcomes are
80original-feasible optima,32time limits,16alien-bound proof rejections and16
preserved observer exceptions. Partial publication, phase invalidation and work
budget ordering are preserved. Census-1 oracle failure and4caseprobe remain raw.
Reviewer reproduced reference/source hashes and relied on accepted full pin audit.

No unnecessary new production work, allocation or retained memory is introduced.
Cold restoration has a potentially avoidable O(N) duplicate cost copy only with
identity plus proven nonoverlap; aliased/detached cases both count3copies/5elements
at N=2,n=1. No evidence supports removing scans, invalidation, reconstruction or
detached journal storage. No speedup is established.

## Declined scopes and rulings

- S5-C correctness/performance: future implementation/cost/review gates; no promotion.
- Natural perturbation frequency: fixtures explicitly publish journals; no frequency claim.
- Full workspace bitwise equality: selected recorded representations/events only.
- Other precisions/managers/large problems/update-chain scaling: retain bounded
  Float64/RationalBigInt and two-HH-backend census scope; implementation must qualify wider coverage.
- Whole-model immutability: input assertion covers objective/column bounds only;
  report now says so, with no implied complete model mutation audit.
- Broad regression/CI: historical failures stay open and CI disabled; reused test
  source is not a passing current-source full suite.
- Current host state: author independently confirmed runner364759/child364760/
  driver364750 absent on boot20de7dde-704e-41c8-bee7-b8511c0a86b0; no Julia.

Master remains322011855af909d0d93b6f9bbecbe4200512fc67. No production diff.
