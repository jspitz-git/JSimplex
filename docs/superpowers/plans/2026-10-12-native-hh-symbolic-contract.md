# S4-E: native HH symbolic construction contract (source/evidence only)

Select one remaining architecture obligation from the S4 roadmap after the local
S6-AO coverage milestone. S4 is independently allowed when an earlier experiment
is rejected. Historical cleanup cause and full-suite/x64 validation remain open;
this is not S6 closure and does not authorize more cleanup runs.

## Question and fixed scope

Can a narrowly defined native Float64 HH construction lifecycle safely retain
symbolic state, and what evidence is missing before a bounded qualification?
Current HH lu! explicitly uses reuse_symbolic=false. The PFI pattern helper and
spare lifecycle are existing mechanisms, not proof that HH may copy their policy.
Equal dimensions/pattern alone never authorizes symbolic reuse: native symbolic
construction also receives numerical values and may affect ordering/scaling,
threshold choices, factor structure and downstream arithmetic.

This stage executes NO Julia, factorization, solve, numerical component, corpus,
benchmark, old parser/driver/auditor or test. No production/test/environment/CI
change, new adapter or speculative cache. Native symbolic reuse stays unverified.

## Source and evidence inventory

1. Read STATUS, the main architecture roadmap/design, S4-INVENTORY-NOTES.md,
   S4-COMPONENTS.md, S4-SCRATCH.md, S4-TRIPLETS.md, S4-SCALARS.md and their accepted
   reviews. Verify actual host refs/process identities and preserve user dirt.
   Reuse saved evidence only with exact source/runtime/environment hash scope;
   later test-only changes do not create new backend measurement evidence.
2. Trace current src/huangfu_hall_factorization.jl native Float64 setup/refactor/
   extraction/copy/failure publication, src/factorization.jl PFI spare and
   _same_umfpack_pattern, basis-matrix assembly ownership and actual pinned Julia
   SparseArrays/UMFPACK implementation. Inspect installed source matching saved
   runtime pins; do not substitute newest documentation/API or invoke Julia to
   query a runtime. Include lu!/symbolic/numeric control/default dispatch and
   matrix-index/value ownership. Keep native non-Float64 and Markowitz separate.
3. Write an ownership/compatibility table: dimensions, exact CSC colptr/rowval,
   values, ordering/control/scaling, stored symbolic/numeric object and exposed
   L/U/permutations, alias/copy lifetime, failed candidate mutation, old-base/
   saved-factor preservation, prepared-cache invalidation and publication order.
   Identify every existing O(n+nnz) scan/copy and the frequency of any prospective
   guard. Do not infer bounded native retained memory from Julia field lengths.
4. Map actual existing tests by source and accepted executed evidence: changed
   values with same pattern, changed pattern/dimensions, empty/singular/nonfinite
   or failed refactorization, saved-copy isolation and borrowed CSC lifetime.
   Pin presence alone is not execution. Do not rerun completed HH/component or
   manager/allocation tests; do not assume PFI tests establish HH semantics.
5. Reconcile saved native component cost attribution with the exact proposed
   boundary: time/GC/bytes already measured are not proof that symbolic cost is
   avoidable or that reuse is a speedup. Keep original failed hash/parser attempts
   and all accepted S4 evidence untouched. No single-pair current-master claim.

## Decision and review

6. State one precise candidate eligibility/invalidity rule ONLY if source/evidence
   supports it. Otherwise state which native API/ownership/numerical dependency
   prevents a justified proposal. Never enable symbolic reuse in this stage.
   Same-pattern changed-value arithmetic is not promised bitwise identical.
   Original-model certification, tolerances, precision and safeguards remain.
7. If justified, prepare a NEW separate bounded numerical qualification plan with
   exact small matrices/scalars/cases/calls and reference/candidate provenance,
   solve/residual/factor/permutation checks, failed-publication/alias probes,
   work/allocation/retention accounting and resource limits. Bound the number of
   fresh factorizations/refactors/solves before launch. No matrix search, broad
   sweep, medium/reference/cost replay or implementation by analogy. If not
   justified, document the blocked hypothesis without manufacturing a numerical
   experiment; select the next concrete supported roadmap obligation.
8. Fresh independent numerical/work/memory review of this source contract and any
   proposed separate qualification, then update STATUS/continuation and push the
   diagnostic branch. No new runtime claims, no native-symbolic acceptance, no
   S4/S6 closure. S2-A/S6-J/wholeAF remain rejected; CI stays disabled.
