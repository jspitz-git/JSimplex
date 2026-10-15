# Independent Task1 offline review

Decision: NOT ACCEPTED. One actionable P2 test-coverage finding remains. No
production implementation defect was identified in this source review. This is
not runtime acceptance: Julia query/parser/import/compile/numerics and the ordinary
overlay builder remain UNEXECUTED. No production src/test/environment was edited.

## Finding R1 — exercise populated-spare copies and saved copies during failure

Location: candidate/test/native_pivot_policy_tests.jl:140–170.
The sole selected-policy copy fixture constructs a fresh factor and immediately
copies it after one column update. Neither operation populates a spare; therefore
`saved.base.spare === nothing` cannot detect accidentally sharing a populated
spare. The two singular-refactor fixtures retain no saved copy, so they cannot
establish that a failed private `lu!` preserves saved owners, controls, history,
and F/B results. These are explicit Task1 lifecycle requirements and review
focuses, not optional additional stress tests. Existing unchanged default-only
neighbor tests do not demonstrate the selected policy interaction.

For all four ordinary managers and both policies, populate and explicitly observe
a private spare before copying a manager with nonempty history. Observe that the
copy has no spare, keeps the shared active owner and policy, and survives
independent refactors. In a populated-spare singular-failure state, keep a saved
copy and assert its owner/control/history/policy and forward/transpose results
before and after failure and subsequent valid refactorization. Retain the
separate no-spare fresh-failure case. Update the ledger and bindings to describe
actual coverage. This review does not implement those changes or authorize Julia.

## Production source assessment

The appended Symbol leaves SolverOptions' three type parameters intact. The
legacy 16-argument wrapper supplies default; keyword validation and public scalar
conversion validate selection/combinations. Inspection of all source option
construction sites found preservation in `_validated_options`, scalar conversion,
phase, remaining-budget, auxiliary, and precision copies. MOI reconstruction is
intentionally default. Recovery retains the existing options-based factory;
actual recovery trial execution belongs to Task3.

The native policy is a constant UInt8 enum field in the existing nonparametric
backend. Float64 construction uses the more-specific native three-argument
method; other scalar types delegate to their original backend. PFI/FT/SS/BG
constructors and factories route policy consistently. Markowitz and fallback HH
reject nondefault policy before factorization; default forwards to existing
methods. No likely Julia syntax or dispatch ambiguity was identified by reading,
but parser/inference/exception-type verification remains deferred.

Default fresh construction remains literal `lu(B)`. Threshold-one obtains private
default controls and sets only LibSuiteSparse PIVOT_TOLERANCE+1 and IRSTEP+1 before
one LU. Those installed API names/indexing match the accepted design. No global
or active shared-control mutation appears. Legacy two/four-argument raw wrappers
still carry default reconstruction policy. The existing candidate publication,
failed-spare discard/rethrow, empty, dimension/pattern, and manager-history reset
rules are unchanged except fresh LU selection. Copy forwards policy and still
drops the spare; this source finding does not replace the missing test coverage.
Four raw auxiliary LU safeguards in dual_simplex.jl are byte-identical and remain
outside the managed policy, as are HH arithmetic and frozen direct prototypes.

The four test groups use tiny matrices, literal non-Float64 solutions, full20
control bit checks, six representative scalar types, independent fresh owners,
constant-field rejection, option round trips, resized/repeated-empty transitions,
and separate fresh/spare failures. RED has four missing-interface predicates and
no factor/solver calls. Import cost is not asserted to be zero. Besides R1, no
additional actionable source/test defect was identified. Generic other supported
scalar types are not newly runtime-qualified.

## Computational work and memory

No unnecessary NEW production work or memory cost was found. Options validation
and symbol-to-enum conversion add constant work at construction/reconstruction;
options and backend copies carry one Symbol/enum (padding unmeasured). Fresh
threshold-one factorization obtains one default-control vector, makes two scalar
stores, and uses the wrapper's existing control copy and one LU. It adds no
second factorization or RHS solve. Native pivot choices may change fill/native
work materially; no universal cost bound or speedup follows.

Private-spare refactorization retains the existing O(n+nnz) pattern comparison
and lu!, with no added control scan/copy/rewrite. Whole solve/update/pattern
ranges and all triangular code after constructors are byte-identical; the native
refactor body reverses exactly after its sole fresh-call replacement. There are
zero added per-iteration, per-candidate, F/B, or update-chain scans/solves/copies.
No additional native owner, retained control registry, growing cache, or scratch
was introduced. Existing metadata conversion, aliasing, spare lifetime, and
non-Float64 arithmetic remain intact. Tiny test snapshots allocate only in test
code and must remain outside future kernel timing. No elapsed/allocation
measurements were run; Task2 must separately qualify metadata/control overhead
and fill/trajectory costs with its admitted sparse/dense measurements.

## Evidence and limits

Fresh reviewer-check-2.py produced reviewer-check.json: 17/17 checks PASS.
All116 required input files (1,900,114 bytes) were independently read and bound;
all514 baseline hashes and every saved binding map in the required JSON inputs
match, including author6 checks/23 bindings and source15 checks/99 bindings.
All28 edits reverse seven whole source files exactly; candidate.patch regenerates
exactly. The 73/75-file reference/candidate manifests have exactly seven source
substitutions and two added tests. HEAD94ea8af804367f4ae3b2e23c416881809608306b,
master6f68e24e8ddac42b948da8fcc2d636c010751194 and tracked production identity match.
The source check's filtered no_hot_policy_reads assertion is vacuous alone; this
review independently verified complete nonempty ranges instead.

The initial author-check.py failure remains preserved. The fresh reviewer-check.py
also stopped before output because it looked for the frozen direct source in a
nonexistent relative baseline key. Its original bytes and failure record are
preserved; reviewer-check-2.py uses the existing source-check.json absolute binding
and was the only successful reviewer checker. No old prep script was executed.
These checker corrections do not change candidate bytes or conceal numerical
failures. review.json binds all116 required inputs, their list, both checker
sources, failure record, successful checker result, and this report; it cannot
self-bind its own SHA256.

Next boundary is an offline correction and separate review of R1. No acceptance,
RED/GREEN/cost/public launch, production integration, direct comparison, new
runtime allowance, or oldcost2 resumption follows from this review.
