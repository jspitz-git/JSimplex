# S6-U: repeated primal price recovery reachability

Diagnostic-only. Production, tests, options, tolerances, arithmetic precision and
CI are unchanged. The four original Float64 manager cases pass all 20 original
assertions locally (Julia 1.13.0 aarch64). This does not establish the historical
Julia 1.13.1 x64 cause or a full-suite pass.

## Reconciled evidence and entry contract

S6-A / results/S6-U/existing-failure-map.json preserves twelve failures per CI run:
four compound NUMERICAL_ERROR assertions and eight event-count assertions showing
0 instead of 1. The compound result assertion does not disclose the actual status.
S2-A/focused-1 included this file among nine files, with 10381/10381 assertions.
That accepted full-file run was not repeated. The new census extracts only the
unchanged helper and repeated-budget testset. Its original five assertions per
manager and publication injection remain text-identical after removing recording.

- `_legacy_primal_iteration!` clears exclusions, owns a local one-attempt price
  recovery flag across both candidate passes, and clears exclusions in `finally`.
- Pricing uses default steepest-edge weights. `_primal_iteration_unchecked!` solves
  the selected direction and checks price agreement before ratio/pivot publication.
  A mismatch on an unchanged basis marks selected_row=-2. The outer loop consumes
  its attempt before invoking `_try_native_primal_price_recovery!`.
- Price recovery requires native Float32/Float64 primal policy, enabled legacy row
  validation, positive refinement budget, and no stop. A fresh BTRAN must have a
  finite, nonzero compensated residual; then cleanup must produce a reliable
  candidate (strict residual improvement when forced on a reliable solve).
- Only finite changed prices are copied with rho, invalidated, and published via
  `primal_prices_corrected`. The original callback then writes reduced_costs[7]=-1.
  A second disagreement cannot renew the local attempt, even though candidate
  exclusions are reset after the successful correction.
- Stop checks can return TIME_LIMIT; observer errors propagate through the
  diagnostics wrapper. This census exercises neither cancellation nor exceptions.
  It returns an internal DualTermination, not a public Solution/certificate.

The preflight identified missing CI status, private fresh BTRAN candidate and
budget-local observations. Existing events expose selected boundary state but
not those private variables. Added snapshots own their arrays and safely classify
non-workspace states; they never call solves, refactors, certificates or workspace
mutators. The existing fault injection is the only callback mutation. Timing
instrumentation counts kernel calls; no observer-neutrality or timing claim follows.

## Observed result

Raw: `.superpowers/simplex-core-architecture/S6-U/census-1`; portable copies:
`results/S6-U/census-1-*`. Exit0, 20/20, all 47 diagnostic checks and 615 launch pins
passed, including independent hashes/membership and actual source. The helper,
original oracle and reversal of recorder additions were checked independently.

All four managers have the same observed sequence after initialization:

1. Pricing selects column 13; selected direction disagrees with its cached price.
2. `correction_attempt` sees selected_row=-2, before corrected rho is published.
3. `primal_prices_corrected` exposes exact rho=[1,1,0,0,0,0] and price7=0.
4. The original injection changes only price7 to -1.
5. Pricing proposes column 7; `pivot_rejected` sees another row=-2 disagreement.
6. A final pricing pass exhausts candidates. Return NUMERICAL_ERROR with message
   "primal reduced cost disagrees with its direction". No second correction.

There are two pivot proposals, one rejection, one price publication and one
correction attempt per case. Initial/terminal primal, costs, basis, bound states,
iteration count, factor-update count and refactorizations agree. Zero iterations;
exclusions empty at return. Prices retain the deliberate corruption at column7.
This is selected-state equality, not equality of the entire workspace.

Each iteration records 6 FTRAN, 2 BTRAN, 3 pricing kernel calls, zero refactor calls,
5 scored entries and 63 scanned entries. Source attribution: two selected-direction
FTRANs plus four steepest-edge weight FTRANs; fresh price BTRAN plus its correction.
These counts include work used to select directions, not just accepted pivots.
They exclude initialization. No additional numerical work occurs in callbacks.

The exact initial cached-rho residual cB-B' rho is nonzero (full fractions in audit).
For example its first component is
28304666636389453/162259276829213363391578010288128.
The published rho has exact zero residual. At the first disagreement the captured
column13 implied price is -1306941474680515/5070602400912917605986812821504,
versus cached -4998383642159429/20282409603651670423947251286016.
At the second it is -1819914369543449/40564819207303340847894502572032 versus -1.
Offline rational arithmetic uses the owned matrix/basis/directions/costs. It does
not reconstruct private fresh BTRAN internals from an event emitted before their
publication. Source flow establishes that the correction branch was reached, but
neither that fact nor initial cached rho captures its exact private input.

## Decision, cost and limitations

Accepted by fresh independent gpt-6-astra review as current-source reachability
evidence. The review found one Important gap in the unqualified next plan, fixed
by requiring a budget-sensitive fresh-cost BTRAN count and negative check; see
S6-PRIMAL-PRICE-REACHABILITY-REVIEW.md. No
repair is promoted and no historical x64 arithmetic cause is asserted. The test's
entry depends on native roundoff creating prices that reach a demonstrated recovery;
the old CI zero counts alone cannot choose among the missing prerequisites.

No production work, allocations or retention changed. Diagnostic recording stores
four 6x15 matrices, 44 event snapshots and eight iteration boundary snapshots;
its small bounded copies are necessary to preserve pre/post-injection evidence.
Kernel timing and snapshot overhead are not a performance experiment; no benchmark
or speedup claim. No accepted corpus/reference/cost run was repeated.

Next: S6-V diagnostic qualification of an explicitly controlled price-recovery
boundary, preserving public native integration coverage. A separate RED/GREEN
plan and review are required before permanent test changes.
