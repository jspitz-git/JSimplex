# MA-U independent offline review

Accepted for MA-T Task1 source preparation only. No Critical, Important, or Minor
findings requiring a change. This does not accept a Julia run, runtime allocation
claim, speedup, complete DenseLU candidate, or production integration.

Reviewed branch codex/simplex-core-architecture at
a9d0a7c684c18c84a2baba14aa482882b7a14f9a; master remains
6f68e24e8ddac42b948da8fcc2d636c010751194. Review performed by the independent
mau_candidate_review agent. No Julia/parser/import/compilation/numerical execution,
old script rerun, or git mutation was used. Only this review.md and review.json
were written. Independent Python byte/hash/arithmetic checks supplemented manual
source review; author checks were read, not rerun.

## Candidate and numerical contract

- candidate.jl:1-8 implements exactly the specified current-scope union assertion,
  no-scope/no-key true branches, one locally annotated existing dictionary lookup,
  typed `only(v)` and live global comparison. Installed mpfr.jl:113,247-256 and
  scopedvalues.jl:203-216 establish the no-default-key equivalence. Explicit equal
  scoped/global modes remain eligible. Unexpected private-state lookup/type errors
  propagate. Concurrent unsynchronized global writes remain outside the contract.
- candidate.jl:13-18 retains every original type/storage/shape/n16 check in order.
  Independent removal of the helper and reversal of the single return expression
  reproduces MA-R/candidate.jl bytes exactly. All 12 product sites and the complete
  arithmetic tail are unchanged. candidate.jl:23-35 still delegates a complete
  mismatch call before product construction or destination mutation.
- No Base method replacement, HAMT clone, effect assertion, cache, tolerance change,
  dropped coefficient, or precision increase was introduced. This is tied to the
  pinned installed sources; a future external pre-load drift check is essential.

## Test and interface review

- guard-tests.jl:15-21 normalizes exactly to the original eligibility definition
  after removing only the name and P qualification changes. Lines 39-53 cover all
  five global modes, six scope states, three precisions and 0/8/64 unrelated keys.
  Existing context uses an active precision scope; these are absent-key cases,
  not evidence of a physically absent task scope.
- Lines 55-139 cover 7 nested, 3 unwind, 10 inherited-task/yield/nested-equal, and
  5 consecutive global-change records. The sentinel is identity checked. Tasks
  are scheduled and joined serially on the successful path before global changes.
  A third task reports whether current_scope is truly nothing, without mutating
  private task state; unavailable remains a coverage limitation. Each candidate
  call rereads task scope, so no stale scope or mode can be retained by the helper.
- Lines 147-198 cover 720 mode-grid + 80 special + 20 small + 4 other-scalar +
  16 mixed-precision cases. Four retained-output repeats give 844 direct calls per
  original/new/instrumented arm and 2532 direct arm invocations. There are 840
  bundles, including 4 PFI constructors and 4 PFI copies. These are not a complete
  internal/delegated-call budget; MA-V must enumerate native setup work, fallback
  reference delegation, wrappers, driver additions and failure paths separately.
- The named predicate ledger checks out: 840 old-eligibility calls; 2528 new
  eligibility calls; 804 initial cases reaching the rounding clause plus 4 repeats;
  2420 new guard calls in whole comparisons; 2715 or 2716 named new guard calls
  overall and 1099 or 1100 named old rounding expressions. Base arithmetic/context
  lookups are additional. Predicate records are 270 + 25 + optional 1.
- Original tests.jl:91-150 retains exact finite value/precision/sign and NaN/Inf
  tokens, factor/RHS/old leaf identities and values, alias maps, retained outputs,
  exception type/message and post-unwind destination state comparisons. Instrumented
  route/scratch checks remain separate from candidate cost measurement. Tests and
  fixtures are copied exactly; no weakened oracle or invented numerical fixture.
- reference.jl imports installed dependencies and defines MADenseProbe; candidate
  and instrumented files must be included into that module, then sibling test
  modules loaded. No auto-qualification call was added. Qualified private names,
  do-block argument order, sibling module bindings and return after @testset are
  source-consistent. MA-S-LOAD/driver.jl:91-102 demonstrates the relevant outer
  invokelatest boundary; MA-U provides no launch driver. Source review cannot prove
  parsing, dependency availability, world-age success, or compilation.

## Work, allocation and retained memory

No unnecessary NEW production computational work, allocation source, or retained
memory was found. Production files are unchanged; within the diagnostic candidate,
only the final otherwise-eligible FTRAN/BTRAN predicate changes (also applicable to
recovery/certification callers). It still does at most one persistent lookup and
one present-value comparison. No added vector/matrix scan, solve, copy, conversion,
refactorization, per-element operation, or history-sized retained object appears.
Lookup traversal scales with scope storage/hash structure, not problem n/nnz/update
chain length. The scope is only a local value and no cache retains a task or factor.

The existing lookup's HashState/tuple values and local inline expansion may still
allocate or increase compiled code size. No elimination, allocation count or speedup
is inferred from source. The three Ref counters, 3 deepcopies per comparison,
ownership/token snapshots, and retained case outputs are explicit cold diagnostic
costs; their total native-memory bound is not established. Numerical safeguards
remain intact. The authorized offline boundary prohibits the focused runtime
comparison here; MA-V must measure each required context/process with compilation,
setup, ordinary calls and cleanup separated, preserving GC/outliers. Sparse solver
performance is not measured or claimed by these dense/zero-heavy fixtures.

## Evidence and continuation

Fresh independent read-time verification confirmed all 34 source-green bindings,
its 19 recorded passing checks, entry's 15 recorded checks/6 bound files, author-fix's
4 recorded checks/4 bound files, all five exact copies, and all 16 MA-T relevant
source pins with the original-plan mapping applied. Eight continuation mappings
match the exact historical hash and before-copy bytes; source-red's original test
binding maps only through author-fix to guard-tests.jl.before-author. The two author
textual corrections are accurately described and do not claim a Julia failure.

Entry/host evidence is accepted as recorded historical evidence, not a fresh launch
inventory; this review does not repeat the full 166-group/514-source archive audit.
The source-red markers establish an absent helper seam only, never numerical or
allocation RED. Existing MA-S-FALLBACK aggregate evidence is not object attribution.
The byte-identical instrumented copy retains its original terminal blank line.
No author closure/publication draft or future whitespace artifact is approved or
bound here; those require their own execution evidence.

STATUS.md:50-69, roadmap.md:2440-2461 and the preparation report retain the right
boundary: broader plan OPEN, MA-S-2 rejected48/52 with Rational controls unresolved,
no old rerun or gate waiver, and next work only MA-V admission preparation.

## Declined to judge

Julia syntax/parser acceptance; dependency imports and world-age runtime behavior;
numerical execution of new cases; actual absent-scope attainability; concurrent
global MPFR writes; runtime allocations, code growth, timing or causal attribution;
full setup/delegation/native-memory budget; anti-hoisting implementation; any MA-V
launch readiness, raw records, or performance gate; full DenseLU/Rational acceptance;
production integration; fresh host-wide process absence; and publication completion.
