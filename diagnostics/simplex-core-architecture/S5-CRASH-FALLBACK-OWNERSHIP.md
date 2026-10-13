# S5-V: crash fallback ownership and publication contract

Source and historical evidence support reuse of existing crash success, fill/quality
rejection, stop-latching, final-refactor interruption, precision and phase-one tests.
They do not yet qualify ONE narrower composition: an observer exception at
`:crash_fallback` after private-trial work counters have been merged into the initial
workspace. This is an unqualified selected composition, not a demonstrated defect,
not a claim that it has never executed, and not authorization for a numerical run.
No Julia, parser/import/compile/native operation, LP arithmetic, new fixture/driver,
production/test/environment/cache/CI change or old script execution occurred.
Master remains2b546e9; starting diagnostic refa4f4cca is published and verified.

## Evidence and preserved lineage

The new exclusive collect.py was saved before execution. Its21 literal checks pass;
166 fresh read-time hashes include selected source/test/runtime/library/user files,
U admission/results/reviews and four exact source excerpts. U1512 actual-master pins,
1489 historical GREEN pins, T891 and U24-check/123-binding closure, six publication
checks and exact126 committed file/blob membership were independently reread.
Only historical OLD target-test identities map to U/original-test.jl; old bound
STATUS/roadmap map to U/before-U. No manifest or launch pin was rewritten.
U's two numerical allowances remain consumed. Both rejected U admissions and all
older false audits/raw attempts remain preserved. Current full20-group/Julia scan
is empty on bootdade7243-9103-4398-bb45-fa28fbc0be72; user6 hashes match.

The five inventoried files are simplex_start_tests.jl, simplex_start_state_tests.jl,
simplex_start_guard_tests.jl, simplex_start_exact_tests.jl and
simplex_phase_one_completion_tests.jl. Their24 exact lexical testset slices and48
original log rows are saved in evidence.json with source offsets, hashes and raw
ANSI-bearing rows. Lexical slices end before the next testset and can include
intervening module/helper syntax; they are not Julia AST extraction. ANSI handling
only removes the recorded real/caret escape color sequences for count parsing.

Each historical run38142752357 and38149970679 has511 PASS across these24 groups,
SEPARATELY. Both entire CI runs have conclusion failure. The511 includes adjacent
non-crash/imported-start/phase-one groups and is not a511-assertion fallback oracle.
All32 whole-file comparisons (five tests plus eleven production files per historical
ref) are byte-identical to current files. This supports source-matched execution
reuse, not present-day CI/full-suite success, actual private runtime-state capture,
or proof of arbitrary cross-products of independently covered conditions.

Existing coverage specifically includes:

- Owned diagonal structural basis across five scalar types/four managers/two
  backends, with original-model values and caller/imported basis ownership checks.
- Legal fixed/upper/free states, empty/dependent/zero-column models, tiny pivot and
  fill rejection, objective-aware state rejection and exact arithmetic overflow.
- Existing clock and completed-step limits; stop after crash pivot with latching;
  stop after final refactor returning initial identity, slack basis and retained work.
- Wrapped observer causes at phase_crash/crash_pivot/crash_accepted; unchanged logger
  exceptions; stored BigFloat precision and extension of a partially feasible crash
  basis into phase one without slack restart.

Textual search finds four literal `:crash_fallback` test references, all event-count
assertions. The scoped observer-throw loop covers three other events, not fallback.
This search is supporting static evidence, not a global proof that dynamically
constructed callbacks cannot target fallback. No equivalent success/stop census is
needed; existing qualified branches should be reused.

## Ownership, work and publication

`crash_basis` wraps the stop callback; an initial true guard returns a newly owned
slack Basis before progress/workspace construction. Otherwise it creates progress
and initial workspace within the stored-precision scope and finally copies the
returned workspace's basis vectors. The private `_crash_workspace` interface takes
an existing initial workspace and preserves its existing clock/progress context.

`_crash_workspace_impl` creates a latched guard and starts with trial=nothing. It
checks stop/deadline and iteration limit, computes baseline violation/storage limit,
charges initial.refactorizations BEFORE constructing a second fresh slack workspace,
and passes initial.problem/options/shared progress to that construction. The trial
receives completed counters and then sets scratch.recovery_active=true. Constructor
work before that assignment is real and may perform policy-dependent checkpoint or
quality work; the assignment is not evidence that initialization had no such work.

The workspace constructor owns fresh cost/bound/basis/point/price/weight containers,
factor factory input and scratch; problem and progress are shared. Bound vcat owns
container storage, not a deep ownership proof for arbitrary scalar objects. Native
factor storage and update-chain retention are not captured by this source audit.
Shared diagnostics and caller observers remain capable of external mutation; the
contract never asserts immutability under arbitrary user callbacks.

The trial performs objective-aware nonbasic setup, reconstruction, ordered sparse
column scoring, guarded FTRAN/BTRAN and validated updates. Ordinary updates and
refactors change trial-owned numerical state. Fallback does not copy those trial
numerical vectors back. `_crash_fallback` merges max(initial,trial) iteration and
refactor counts (if trial exists), then emits crash_fallback on INITIAL, then returns
(initial,expired). If trial construction threw before assignment, trial remains
nothing but the earlier attempted-work charge on initial remains.

`_simplex_event!` forwards to `_diagnostic_event!`: record_event! updates count and
bounded history BEFORE invoking the observer. Thus a fallback observer may see the
initial workspace with merged work counters AND an already-recorded fallback event;
throwing there prevents the return. DiagnosticObserverFailure preserves its cause
and is not one of the numerical exceptions swallowed by crash fallback. A direct
stop/logger exception tracked by the guard is rethrown with its original identity.
These are SOURCE interpretations; the selected fallback-observer combination has
not been newly executed. Observer-retained initial/trial objects remain mutable.

The final acceptance path invalidates trial checkpoints, refactors/reconstructs,
checks the guard, evaluates finite/quality/violation/fill conditions, resets devex,
clears recovery_active, emits crash_accepted on TRIAL and returns it. Event delivery
still precedes the return. Acceptance need not mean primal feasibility: phase_one
or non-primal algorithm permits a partially feasible basis with non-worsening
violation. Numerical basis reliability is not an original-model feasibility or
optimality certificate. Existing phase-one coverage already exercises this limit.

`_crash_refactor!` finally preserves at least one attempted refactor charge even on
an exception; this is not necessarily one successful/native backend factorization.
The outer timed crash kernel increments in finally for entered try bodies, including
exceptions. phase_crash is emitted before that try, so an exception at that initial
event need not contribute the timed crash entry. No total backend budget is inferred.

## Computational work and memory

No unnecessary NEW production work, allocation or retained memory was introduced:
only diagnostic text/evidence is added. No benchmark is warranted or was run.
Existing work is classified from source, not newly measured:

| Boundary | Existing work / storage | Scaling and limits |
| --- | --- | --- |
| Stored-precision entry | BigFloat precision scan of matrix/objective/bounds; scoped precision restoration | O(nnzA+n+m); existing arithmetic policy, no new promotion |
| Initial and private trial setup | Fresh slack factor, owned vector/scratch construction, reconstruction and optional policy work | O(n+m) containers plus factor/scratch/backend costs; no deep/native graph bound |
| Crash entry | Primal violation and factor-storage inspection; second workspace attempt charge | Scans and factor metadata depend on implementation/type/history |
| Column ordering | n-column list/count storage, sparse coefficient scan and sort | O(n+nnzA) scan, sort normally O(n log n) |
| Candidate | Prepared FTRAN, row selection, candidate-score scans, fill count, selected BTRAN and validation | Row selection and each score can scan m; bounded candidate list does not remove solve/scan costs |
| Pivot/refactor | Factor update, candidate preparation, event; scheduled/final refactor/reconstruction and quality checks | Type/nonzero/update-chain dependent; optional refinement and backend work additional |
| Final acceptance | Invalidation, violation/finite/quality/fill checks and devex reset | Vector/matrix traversals and temporary quality storage remain; no omission proposed |
| Fallback/public return | Two scalar max merges and event; public interface copies two basis containers | Fallback itself copies no trial numerical vectors; public Basis copy O(n+m) |

The candidate loop allocates columns/counts (length n), four explicit length-m
vectors (rhs,column,unit,rho), and a row list; policy/factor/quality helpers may add
other storage. The event ring is bounded64 but an observer closure may retain whole
mutable graphs. Scope exit is not native deallocation, GC timing, rollback or memory
confinement proof. Neither unchanged counters nor historical successes demonstrate
observer neutrality, real wall expiry, complete PREforward/native/import work or
speedup. Numerical safeguards and all tolerance/precision choices remain intact.

## Next bounded step

S5-W is OFFLINE oracle preparation only, using the existing final-factorization
interruption fixture and the source-supported INITIAL fallback event discriminator.
First specify exactly which owner/value/work/event/cause observations distinguish
that one composition and avoid duplicating already-covered cancellation/success.
Do not create a driver, launcher, permanent candidate or numerical admission yet.
Preserve failure possibilities and require fresh independent numerical/work review.
All prior S2/S6 rejections, CIoff/HHdisabled, Q GC dominance/outlier, bootstrap/cache/
init/controller caps/native retention and broader S3/S4/S5/S6/full-suite gates remain.
