# S4-H: borrowed HH assembly/recompute source contract

Source/evidence only on df2a96f/master0eb75c3. No Julia, factor, workspace, solve,
quality or certificate calls; production/test/CI unchanged. Twenty historical
file comparisons,526current hashes. Original offline check24/25,exit1: selected CI
lines contain literal visible `^[[32m` escapes, not ESC bytes. The original parser
left colour numbers in its numeric fields. Original script/result/all_passed=false
are preserved. New log_supplement.py normalizes just eight stored rows:8row checks
plus preservation of24other original checks pass. No old parser or numerical rerun.

## Smallest real setup and work boundaries

initialize_workspace -> _initialize_workspace_state -> one HH(-I) constructor,
then _finish_workspace_initialization! -> recompute!(refactorize=false), one FTRAN
and one BTRAN, reduced-cost reconstruction and :refactor_initial. Initial assembly
storage is the same -I CSC passed to factor creation; native LU owns its copied
CSC and extracted factors own arrays. Configuration reads factor storage/growth,
allocates scratch and copies costs/bounds/objective; setup is not free.

Default legacy/native NumericalPolicy has solve_refinement/recovery/hypersparse
false. Checked solve entry still calls real dense HH ordinary FTRAN or BTRAN,
but neither solve_quality!/refinement nor verified-checkpoint reconstruction runs.
No basis solve is skipped just because RHS is zero. Public initialize_from_basis
is not needed for this focused constructor/assembly qualification.

| Boundary/source | Mutation, ownership and work |
|---|---|
| simplex.jl239–258 validation | Bounds/uniqueness/state checks fill basic_mask; O(m+n). Even failed validation need not restore this disposable mask. |
| simplex.jl260 public basis_matrix | New O(m+nnz(B)) CSC arrays after validation; owned caller result. |
| simplex.jl266 internal _basis_matrix! | Validation then existing scratch CSC for same dimensions. Its rowval/nzval vectors resize to selected stored-entry count; colptr rewritten. Returns borrowed storage until next assembly. |
| simplex.jl279 assembly | Count selected column lengths, then copy every stored entry including zeros, or one -1 slack entry. O(m+nnz(B)); retains vector capacity under shrink, no portable fixed retained-byte guarantee. |
| simplex.jl412 recompute entry | Validate; invalidate pricing pool if present. Native default pool is normally nothing, so do not invent a populated pool for this gate. Logger is caller code, can throw with guard provenance. |
| simplex.jl425–431 pre-factor | Reassemble borrowed CSC; before-refactor adaptive metadata (native legacy no-op); timing wrappers call factor. Existing kernel counter increments in finally including failed factor call. Adaptive cost wrapper can mutate attempts/cycle state and abort metadata; excluded from proposed default-native scope. |
| simplex.jl432–445 successful factor | after-refactor clears native residual_bad, increments workspace.refactorizations, emits requested refactor event, resets nonzero-step count and possibly devex state. This happens BEFORE subsequent reconstruction. |
| simplex.jl447–474 reconstruction | Rebuild RHS from nonbasic bounds, overwrite primal entries, ordinary FTRAN, scatter basics, fill basic costs, BTRAN, rescan full A for reduced costs. O(n+m+nnz(A)) plus two basis solves and optional checked-policy work. |
| simplex.jl475–480 tail | Checked recovery may checkpoint; verbose progress may scan/allocate/log. Native legacy/verbose=false excludes these branches by actual options, not code removal. |
| HH537–589 factor publication | Before mutable LU, conditional candidate pattern compares private native index copies with borrowed B. Successful extracted base does not borrow B. Numeric-LU failure discards refactor workspace without publishing extracted base/history. |

The production borrowed-assembly inventory has thirteen call sites: recompute
(simplex.jl425) and twelve additional consumers:

| Source locations | Consumer |
|---|---|
| simplex_recovery.jl27,104,172 | Refinement, recovery factor construction, reconstructed-basis verification |
| legacy_dual_correction.jl30,113 | Native dual corrections |
| simplex_pivot.jl473 | Pivot validation |
| legacy_primal_pivot.jl52,123 | Price recovery and pivot sensitivity checks |
| simplex_phase_one.jl166; native_phase_transfer.jl175 | Phase transition checks/repair |
| native_cleanup_recovery.jl89; native_certificate_recovery.jl10 | Cleanup and final witness correction |

These consumers can overwrite borrowed arrays outside refactorization. Recovery
also passes borrowed assembly to factor construction. Several consumers run under
native policy; disabling checked-policy features does not exclude them from general
solver execution. S4-I exercises only initialization and explicit recompute, with
no pivots, recovery, phase transfer, cleanup, or certification. Its call budget is
scoped to that lifecycle, not the complete solver. These other consumers remain
unqualified for conditional symbolic reuse.

solver.jl163 and simplex_pivot.jl192 direct refactors use allocating public
basis_matrix; they are separate consumers, not borrowed-buffer execution.

Failure is NOT whole-workspace rollback. Caller-installed basis/states remain;
validation mask and borrowed CSC already reflect the new candidate. An existing
pricing pool may already be invalidated. A throwing factor kernel consumes its
kernel count/time, but success-only workspace.refactorizations/event and
primal/dual reconstruction have not run. Native legacy _abort_basis_refactor!
is a no-op; broader adaptive behavior has its own mutations. Old extracted factor
can remain usable while current workspace.basis names a failed matrix: never
certify that pair or continue simplex with it. A post-LU reconstruction failure
is later than publication and has a different contract, not qualified by G.

## Actual evidence, without pin-as-execution claims

Both historical CI runs independently show the four assembly testsets passing
16,2280,3,12assertions(total2311each), within failed whole suites. All9relevant
assembly/dispatch/test files match current source per run; HH source is the one
of10that differs, and the assembly manager loops exclude HH anyway. These testsets
exercise native/Markowitz × pfi/FT/SS/BG for first two rows; capacity/empty/precision
rows use default PFI. They do not qualify the conditional HH candidate.

Accepted S4-C focused execution includes six named HH files, including
huangfu_hall_integration_tests.jl. Its recorded source/test pins match all10files
examined here; the log explicitly starts that HH integration file, whose public
solves cover both algorithms/strategies/backends. The assembly test file is pinned
but NOT included by that focused driver. Thus native HH public solver behavior
has reused executed evidence; deliberate borrowed overwrite/shrink/failed-publication
under the conditional candidate does not. Accepted G covers direct factor
ownership/history and should not be repeated. Accepted F fallback is native
component-level, not recompute integration. No new whole-suite/platform claim.

## Decision, cost and limitations

The smallest new integration gate is two tiny real workspaces with reference
production recompute versus an exact routing-only recompute clone using the
already-scoped HH conditional clone. Real _basis_matrix! handles structural
same-pattern replacement, actual later assembly overwrite, shrink to slacks,
and one failed singular assembly. No factor adapter/fabricated solve, updates,
solver iterations, auxiliary workspace, private retry or quality/certificate.
A separate S4-I plan freezes exact matrices, calls and observation boundaries.

No production computation/allocation/retention increase in S4-H. The hypothetical
candidate adds O(m+nnz(B))pattern comparison per eligible refactor; existing scans,
CSC copies/native numeric/extraction/reconstruction remain. Default controls/q
are unchanged in this source path, but arbitrary external mutation remains
unqualified; no cached proof about controls is introduced. Empty/nonfinite/shape/
scalar boundaries, native memory and representative cost remain separate before
production enablement. Original certificate boundaries and all rejections stand.

Evidence: results/S4-H/source-contract.json,log-supplement.json,host-preflight.json.
All eight original log locations are preserved with both run IDs. No accepted
exclusive script may be rerun. Host full groups5234/5239 clear, no Julia, same
bootdade7243-9103-4398-bb45-fa28fbc0be72. User hashes preserved.
