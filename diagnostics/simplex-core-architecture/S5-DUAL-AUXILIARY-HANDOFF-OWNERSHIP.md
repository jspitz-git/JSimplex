# S5-J: dual auxiliary original-bound handoff ownership

SOURCE/EVIDENCE ONLY at diagnostic5a2c523 and master513c053. No Julia, import,
compilation, new numerical fixture/arithmetic, driver, old audit rerun or production/
test/environment/CI change. This reconciles one ownership boundary; it does not
reopen HH/DSE or aggregate controller-budget investigations.

## Existing executed coverage first

Both saved failed CI runs38142752357 and38149970679 contain the following passing
rows, separately237 assertions in each failed run. Sixteen exact named test blocks
and their containing test files match the historical sources byte-for-byte.
Eighteen relevant production-file comparisons give16 equal and two known differences
in simplex_perturbation.jl (the accepted S5-C restoration copy change). All eight
other inspected production files, including dual_simplex.jl and simplex_pivot.jl,
match both historical versions. This is source-matched historical execution reuse,
not a new current-master run or successful full CI claim.

| Historical testset | Pass per run | What it actually covers |
| --- | ---: | --- |
| Interrupted auxiliary handoff preserves the live basis and factor | 78 | phase_one false/true × logger/callback/deadline interruption; live basis/primal/factor preservation, explicit factor solves and successful resumed handoff |
| Auxiliary handoff publishes a fresh phase only on acceptance | 19 | success, deadline, and refactor_other observer failure; pricing/stagnation/basis and successful weights |
| Completed auxiliary work survives a callback exception | 3 | shared consumed iteration work despite callback exception in the shared driver |
| Modern auxiliary dual owns its bound and cost model | 12 | separate auxiliary problem/cost/bound model for phase_one true, source bounds preserved |
| Modern auxiliary dual preserves recession and feasibility proofs | 16 | public terminal outcomes, two scalars/two algorithms; not an internal publication snapshot |
| Bound flips and auxiliary dual feasibility | 106 | original-bound successful primal/price/weight/objective and model preservation checks |
| Auxiliary workspaces own their factorization backend | 1 | auxiliary refactor does not replace the original backend |
| Diagnostic observer failures do not become numerical statuses | 2 | generic public observer throws; no selected pending-publication boundary |

Raw row numbers, original ANSI text, normalized rows, original run heads, exact
block/file comparisons and log hashes are in results/S5-J/evidence.json. The
normalizer removes only stored ANSI escapes. Both CI conclusions remain failure.
The78/19 tests already cover private interruption and success; do not repeat them
or present them as a newly discovered gap. The19-test observer targets refactor_other,
which recompute! emits before its FTRAN/BTRAN reconstruction and before publication.
Its :deadline is a callback condition, not evidence of real clock expiry. The78-test
logger marks the refactor entry; its callbacks use that flag, not a clock capture.
S6 staged dual retry fixtures concern another boundary. I's precision-transfer cases
also do not qualify this auxiliary handoff. Broad public tests can traverse parts
of this path without asserting the particular ownership relationship below.

## Source ownership and publication contract

Here "original-bound" means the live working bounds after entry restoration, as
opposed to the auxiliary box. It does NOT assert equality to authoritative problem
bounds for arbitrary caller-altered buffers. In particular, phase_one=false does
not normalize every unowned working cost/bound buffer. The trial feasibility tests
refer to those live working buffers; original-model certification remains separate.

Read src/dual_simplex.jl:_auxiliary_workspace/_make_dual_feasible!, simplex_pivot.jl,
simplex.jl:Basis/recompute!, simplex_pricing.jl, simplex_recovery.jl and diagnostic/
sparse/hypersparse cache helpers. Six exact excerpts bind the principal ordering.

| Boundary | Ownership and changes | Failure/visibility |
| --- | --- | --- |
| Entry before trial | Restore active perturbations on LIVE workspace; optionally restore original costs, recompute and flip bounds. Model order remains structural columns followed by row slacks. | These live changes and restoration callbacks precede private staging. There is no whole-function rollback. S5-B/C restoration contracts are reused. |
| Auxiliary creation | Own lower/upper, copied basis/state/numerical arrays, scratch and copied factor; progress/options are shared. phase_one false retains problem identity despite artificial bounds; true creates an auxiliary problem with its own bound/objective arrays and the same A. Journals do not carry into fresh scratch; primal/dual perturbation flags are disabled. | Reset pricing/history, deep-copy refactor policy, recompute and emit phase_auxiliary. The phase_one true certificate refers to this auxiliary model only. |
| Auxiliary terminal | Optimizer mutates auxiliary; live iterations/refactorizations updated in finally. Nonoptimal auxiliary box cannot establish original infeasibility/unboundedness; negative objective needs recession checks and original feasibility classification. | Consumed work survives throw/return. No copied certificate is adopted. Shared diagnostics can change before handoff. |
| Original-bound mapping | New Basis copies auxiliary indices/states; nonbasic free/upper/lower states remapped using LIVE original bounds. Last pretrial stop is checked. | No column reorder or original/auxiliary matrix equivalence transformation is introduced. |
| Private trial | Candidate owns staged value arrays/scratch but initially shares factor and refactor-policy references. This handoff explicitly replaces factor with a SECOND copy from the live factor and deep-copies refactor policy. Trial problem/options remain live originals, progress retains clock/policy/shared diagnostics counters. | Candidate stage buffers are cached in live scratch, so their allocation/content changes are not exhaustive workspace immutability. Factor-copy/backend sharing contracts remain backend-specific; S4-X HH scope is reused, not expanded. |
| Trial preparation | Invalidate trial checkpoints/cache; assign mapped basis; copy auxiliary pricing/weights/reference/steepest/costs and scalar controls. Reset original-bound pricing history. Refactor/recompute, flip as required, finite and dual tolerance checks, final stop. | Refactor_other and other nonbuffered events can reach the user observer with TRIAL state. Refactor work charged to live in finally. Rejected private trial is not published, but diagnostic/work/stage-scratch changes remain. |
| Publication | Invalidate LIVE checkpoints (including cached stage scratch), copy pivot state into existing live array storage, clear live stagnation, assign trial factor. Refactor-policy reference is adopted by copy helper. Original live problem/options/progress and perturbation-journal slot are not replaced by this helper. | No user callback occurs between these publication statements. This is not a guarantee against arbitrary internal exceptions or allocation failures during copying. |
| Pending events | Iterate trial StageObserver.pending and call _simplex_event!(LIVE, reason) AFTER factor assignment. With diagnostics present, :pricing_phase_reset is buffered when emitted; no pricing state means reset can return without that event. | Ordinary diagnostic recording precedes user observer call; failure becomes DiagnosticObserverFailure(cause). Published state remains published; later queued events may not be delivered. No rollback or callback invisibility is promised. |

StageObserver shares event/count/kernel dictionaries with the live solve. It buffers
only listed completion/pricing events or pending-update/post-iteration events; other
events forward immediately with candidate state. Therefore even a successful pending
replay is not observer neutrality. The live checkpoint invalidation recurses into
cached stage scratch, so do not assume all trial cache entries survive publication.
The copied recovery-rejection list and phase generation must be read with that order.
The guarded public make_dual_feasible! preserves stop-callback provenance; the wrapped
observer failure is distinct from a native singular numerical status.

## Computational work and memory

No new production work, allocation or retained memory was introduced. Source-only
inspection finds no justified optimization to propose here; required copies/checks
preserve independent mutable state and numerical safeguards. No benchmark is needed.

Existing costs occur at auxiliary setup/private handoff, not every ordinary simplex
candidate by virtue of this report. There are two conditional factor-copy call sites
(auxiliary setup and later original-bound trial) and two refactor-policy deep copies.
They are not two new LU calls; backend base/history sharing and update-chain retention
remain as qualified previously. Basis constructors copy indices/states. Auxiliary
arrays scale with m and m+n; phase_one true additionally owns sliced objective/bounds
and metadata, while sharing A. No new scalar conversion/precision promotion is added.

Candidate scratch/value arrays are allocated on first use and then cached on live
scratch. _copy_pivot_state! has18 explicit copyto! sites (17 fixed-shape destinations
plus the resized recovery-rejection vector), plus pricing state/pool, sparse and
hypersparse helper work. It is invoked for candidate initialization and again on
successful publication; these source sites are not observed execution counts or
allocation totals. Some helper caches share immutable matrix-row metadata, while
mutable support/pool state is copied or invalidated. Retention can scale with m+n,
nonzeros, support sizes and recovery/update history; cached scratch and shared factor
bases may outlive one attempted handoff. No native-retention or full-free proof.

Remapping, finite/feasibility checks and pricing resets scan relevant arrays; resets
can rebuild weights if their framework is invalid. Initial/auxiliary/trial recomputes,
conditional bound-flip recomputes, factor refactor and any policy refinements retain
their existing work. S4-X already maps these source-local solve categories. No complete
PREforward work budget, timing, speedup, actual x64 arithmetic cause or broader
precision/backend qualification follows from this source contract.

## One remaining composition and continuation

The inspected source-matched78/19 tests establish private interruption and success,
but not a throwing observer while replaying a pending pricing_phase_reset AFTER a
successful original-bound publication. Generic observer throws and callback tests
do not assert this specific post-publication state/cause relationship. That is ONE
unqualified composition in the reconciled evidence, not a demonstrated defect or
claim that the path has never executed. Its oracle must distinguish the live caller
from auxiliary/trial notifications, and entry mutations from post-publication state.

Next S5-K is an OFFLINE reachability/oracle specification using existing fixture
source only: establish a discriminating existing observer identity/event predicate,
expected selected-state/cause/work semantics, and bounded read-only capture needs.
No new fixture mathematics, Julia, driver, production hook or runtime plan is
permitted. If the boundary cannot be distinguished without hooks/method overwrite/
whole-module cloning or extra numerical work, record that limit and close the route.
Do not repeat already qualified private handoff cases or HH/DSE/controller audits.

The21 source/evidence checks and97 fresh read-time hashes include48 runtime/library
files, relevant source/tests, six exact excerpts, old logs/reviews and protected user
files. Initial host baseline independently rehashed all1322 I pins and I closure.
These are read-time identities, not launch pins; there is no new runtime observation.
Exploratory rg reads guessed nonexistent workspace/pivot paths and an old collector
name; they stopped or returned no match before later reads. Correct paths were found
with rg; these were search errors, not failed numerical runs or rerun audits.
Frozen I/F/G/H/raw evidence, G original false audit and separate supplement remain.
CI stays off, HH reuse disabled; all rejection, historical/full-suite/x64, Q GC/outlier,
bootstrap/cache/init/whole-controller/native-retention and broader stage limits remain.
