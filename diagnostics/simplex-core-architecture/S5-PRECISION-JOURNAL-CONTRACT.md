# S5-D: precision-transfer journal ownership and evidence

SOURCE/EVIDENCE ONLY. No Julia/import/compilation/native execution, old script or
numerical rerun, model arithmetic, production/test/environment/CI modification.
This contract concerns existing transfer behavior, not a proposal to raise precision.

## Existing execution reconciled first

Both preserved failed CI runs, 38142752357 at b720674 and 38149970679 at 4914cbb,
contain the following independently parsed successful subgroup rows. Each run
remains failed overall. Counts are per run, not a new execution or fullsuite pass.

| Group | Passed/total in EACH run | Scope |
| --- | --- | --- |
| Precision copies preserve stored values and own storage | 22/22 | Numeric copies, BigFloat ownership, CSC arrays, rejected narrowing/exact-float conversion |
| Transfer rebuilds the actual typed basis and retains cumulative work | 1504/1504 | Existing typed manager/backend matrix; no active journal in that matrix |
| Precision transfer owns active perturbation journals | 21/21 | One Float64 -> BigFloat successful active-cost-and-bound transfer and destination restoration |
| Transfer precision includes hidden stored input precision | 26/26 | Four precision locations, including inactive journal original cost |
| Transfer checks invalid bases and shared deadlines | 19/19 | Expiry, invalid/singular basis, callback/observer provenance, cancellation; no active journal |
| Rebuilt steepest-edge weights and exact transfers | 22/22 | Rebuilt weights and same-type rational transfer |
| Transfer never lowers an already wider working precision | 3/3 | Wider stored working state under lower ambient precision |

Total 1617 assertions in seven rows per historical run. results/S5-D/evidence.json
preserves all14 raw and normalized rows, metadata identities and sixteen whole-file
comparisons: simplex_precision.jl, simplex_recovery.jl, simplex.jl and the three
precision test files match both historical sources. simplex_perturbation.jl and
runtests.jl differ in both comparisons; do not claim all dependencies are identical.
The relevant include entries remain present. Historical restoration assertions
therefore remain historical execution, not a fresh current restoration qualification.
No current-master pass is inferred from matching files alone. The nearby S4-C HH
precision subgroup is not the active-journal test. lp_refinement_state_tests is a
source reference for restoration, not a replacement for transfer evidence.

The 21-assertion test proves selected destination aliases, new owner ID, activity,
levels/cooldowns, monitor reset, original-cost nonaliasing, selected source values,
source checkpoint preservation, fresh sparse-pricing matrix and restored values.
Its all(checkpoint predicate, fresh.checkpoints) assertion can be vacuous if empty;
it does not prove nonempty checkpoint publication. It does not check every vector
identity or BigFloat object. The separate 19-assertion test does not install an
active journal. Do not combine their passes into an executed cross-product.

## Ownership and publication order

1. transfer_precision checks type legality, creates the guarded shared deadline/
   user callback, and raises source iteration/refactor counters to budget offsets.
   Before numeric conversion, _check_transfer_journal checks source workspace ID
   and original-cost length. Active costs and active bounds are compared by values,
   not storage identity. Detached but equal-value active vectors are permitted.
   This is not general alias/length validation of every inactive journal field.
2. _transfer_bits scans stored model, costs/bounds, original progress/scaling,
   options/policy and all saved journal arrays. BigFloat conversion uses the maximum
   stored/requested precision in a scoped setprecision context. Equal-precision
   BigFloat scalars are deep-copied when constructor identity would share them.
   Supported rational transfers stay rational; float/exact crossing and narrowing
   are rejected. This preserves stored binary data, not hypothetical decimal input.
3. _transfer_precision independently converts problem CSC/index arrays, options,
   policy, progress values and working costs/lower/upper. Basis constructor copies
   indices/states. Progress shares diagnostics and carries budget.start_ns and
   offsets; it does not copy an observer into isolation. Selected-basis assembly
   validates states and polls stop per selected column.
4. A real new factor is constructed for the selected basis. Its finally block
   increments the SOURCE refactor count and synchronizes the shared budget even on
   a throw. Cancellation may return before any fresh workspace exists. Source
   numerical arrays are not deliberately overwritten by these conversions, but
   source work counters and shared diagnostics do change. Callbacks are arbitrary
   caller code; source immutability is not guaranteed against callback mutation.
5. Fresh workspace owns new numerical vectors, basis, factor and scratch. Journal
   copy creates a new owner ID, separately converts original/active costs and all
   four bound arrays, preserves activity/levels/cooldowns/original_perturbed,
   resets last_monitor to nothing and last_observation to zero. Active storage is
   attached to fresh.costs/lower/upper; inactive copies remain journal-owned. Only
   after the copied object is built is fresh.scratch.perturbations assigned.
6. Refactor policy configuration, recompute!, finite and recomputed-basis checks,
   reset_devex! and recovery-weight rebuilding follow. Old checkpoint/pricing/
   stagnation caches are not transplanted: fresh scratch starts empty, recompute
   invalidates pricing and may establish new verified checkpoints under policy.
   No old weights or working certificate are accepted as original-model proof.
7. The final :refactor_other observer sees the fresh workspace BEFORE the final
   stop guard and successful return. Cancellation there returns nothing, but does
   not revoke an observer-retained reference. An observer exception can likewise
   expose the fresh object without returning it. No transactional invisibility or
   rollback of all callback-visible objects is promised. Stop callback exception
   identity is retained by the guard; diagnostic observer wrapping retains cause.
   The outer finally synchronizes budget regardless of outcome.

## Existing computational work and retention

This is a cold transfer boundary, not an ordinary iteration or candidate path.
Let N=m+n, z=nnz(A), zB=selected basis nonzeros. Active validation can compare three
length-N arrays (cost, lower, upper), with short circuit; owner/length checks are
constant-time. Stored-bit selection scans all listed arrays, including two cost
and four bound journal arrays regardless of activity when present. It may revisit
aliased arrays; equality is not permission to remove scans or copies.

Before journal attachment, three working arrays are converted. A present journal
adds two cost-array conversions and, if bounds exist, four bound-array conversions:
nine length-N outputs across these two steps when both journal kinds are present.
Active attachment replaces up to three earlier working-vector references. These
transient allocations are real existing work, not a proposed redundant-copy removal.
BigFloat adds per-scalar owned storage; rational/float conversion costs differ.
Model copy additionally converts z values plus objective/bounds/progress/scaling,
copies CSC column pointers/row indices and metadata; basis validation/assembly
cost O(N+m+zB). Fresh factor/storage and scalar arithmetic cost remain backend-
dependent. No update history is copied into the new factor; journal history owners
are reset, while the source keeps its own history and factors.

Recompute includes basis/pricing scans, primal FTRAN and cost BTRAN, pricing, and
policy-dependent refinement/checkpoint work. Recovery steepest-edge rebuilding
adds up to m ordinary unit-RHS transpose solves, per-row RHS clear/dot/finite
checks and refinement; other pricing modes return from that helper early. This
paragraph is a work classification, not a complete dynamic operation cap. Failed
attempts can consume all preceding conversions, factors and recomputation; stop
polling is not present between every scalar conversion. Shared diagnostic observers
can retain fresh owners beyond an unsuccessful return, so no native-memory release
or zero-retention conclusion follows. All safeguards remain intact.

No new production computational work, allocation or retained memory is introduced
by this documentation/evidence change. No benchmark or speedup claim is warranted.

## One remaining local qualification boundary

The selected gap is the COMPOSITION of an active cost-and-bound journal transfer
with the final :refactor_other stop/throw boundary, especially detached equal-value
source working buffers. The existing successful active test and no-journal failure
test cover the pieces separately. The source does not demonstrate a defect, nor
prove this composition never executes elsewhere. The next bounded action is an
OFFLINE oracle/source preparation using these existing tests; no numerical run or
new precision strategy is authorized by this report. Capture must distinguish
source array preservation from consumed counters and callback-visible fresh state.
Do not repeat the existing successful-transfer or no-journal failure matrix.

CI stays off, HH reuse disabled, old rejected candidates and S4 bootstrap/cache/
init/public-work/native-retention/fullsuite gates unchanged.
