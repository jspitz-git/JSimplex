# S6-U final independent review and disposition

Reviewer: fresh-context gpt-6-astra/high, task /root/s6_primal_price_review.
Reviewed range: 3b5b477a5b46727c69f4f263f5b1e54938a5c650..
f9cb13b6a6b9dc0b615cd693eeb7722a8ad196a4. Diagnostic-only. No Julia, auditor rerun,
file edit or CI change by reviewer. One review; executor makes one fix pass.

## Verdict and finding

S6-U is acceptable as diagnostic current-source reachability evidence. No blocking
finding in S6-U. One Important/P2 finding applies to the unqualified S6-V proposal:
a one-shot cost-BTRAN perturbation on an exact identity factor could hide a renewed
budget. A second invocation returns false on zero fresh residual at
legacy_primal_pivot.jl:60 before correction_attempt, so all five old assertions
could still pass. Recording work alone is insufficient. Require exactly one fresh
cost-RHS BTRAN, separately from residual correction, preserving all five assertions.

Executor verified this control flow and agrees with Important severity: without
it a future deterministic unit test could falsely appear to enforce its budget.
Fixed in ONE documentation pass: S6-V now requires one fresh cost-RHS BTRAN, one
correction BTRAN, total two after initialization, counting forwarded calls even
after injection consumption. It additionally requires a narrowly scoped negative
sensitivity check. The original explicit zero price-tolerance call is recorded.

Verification is static source/control-flow and plan-diff inspection. This fixes a
future plan obligation; no executable test/production repair exists yet. Executable
RED/GREEN and negative qualification remain future gates. No accepted numerical
census was repeated, no source/test assertion weakened, no second review requested.

## Independent evidence checked

- No production or permanent test diff; all 615 pin hashes/resolved paths/membership.
- Exact helper/original testset/five assertions/injection preserved; recorder
  reversal reconstructs the original source. 47 audit gates, exit0,20/20.
- Recomputed rational residuals and implied prices match all four manager records.
- Observed correction/publication/column7 corruption/rejection sequence; initial
  cached rho nonzero residual and published rho exact zero residual.
- Per iteration6FTRAN/2BTRAN/3pricing,63scanned/5scored,zero refactor calls;
  initialization excluded. Recorded runner/child/driver absent; no Julia.

## Numerical/work/memory review

No unnecessary production work, allocation or retention increase found. Diagnostic
snapshots copy eight vector fields,44event+8boundary snapshots and four6x15matrices.
Storage is bounded O(events*(rows+columns))+O(rows*columns) for these fixtures.
Copies prevent aliasing and retain no factor/workspace references. Callbacks add
no solves/refactors/certificates. Timing overhead is not performance evidence;
no benchmark is warranted for this diagnostic-only change. No deferred minors.

## Executor rulings on explicitly declined claims

1. Historical x64 status/arithmetic cause: unresolved because original CI contains
   no such state. A local pass is not that proof; treating it as proof could mask
   still-failing CI. CI stays disabled.
2. Private fresh BTRAN input/local budget flag: not directly captured. Only source
   flow and published selected snapshots support the stated inference. Pretending
   to capture internals would misidentify the recovery cause.
3. Whole-workspace equality, observer neutrality, time/allocation improvement:
   not measured. Only named selected fields agree; recording adds real cost.
   Extending that claim could conceal scratch changes or biased measurements.
4. Portability/full-suite/broader S6: open. This four-case aarch64 result does not
   close other failures or certify x64; treating it as complete would skip gates.
5. Permanent repair/S6-V acceptance: not authorized by this evidence. S6-V remains
   an unqualified diagnostic proposal with explicit additional budget count gates;
   bypassing qualification/RED-GREEN could ship a test that misses regressions.

All boundaries are retained in STATUS and the next plan. Raw/portable evidence and
user files remain preserved. Main stays afb37d9; only diagnostic branch advances.
