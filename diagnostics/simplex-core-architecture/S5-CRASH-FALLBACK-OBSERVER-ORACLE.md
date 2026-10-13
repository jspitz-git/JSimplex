# S5-W: offline crash fallback observer oracle

One distinct composition remains worth preparing: throw an original caller sentinel
from the INITIAL `crash_fallback` observer after trial work reconciliation and event
recording. This document specifies an UNEXECUTED oracle. It creates no Julia code,
new fixture, driver, launcher, permanent test, numerical admission or LP arithmetic.
It does not demonstrate a solver defect or that the composition has never executed.
Master remains 2b546e9; production/test/environment/cache/CI remain unchanged.

## Reused evidence and fixed context

The new exclusive `results/S5-W/prepare.py` was saved before its single execution.
Fourteen entry checks and nineteen literal source checks pass, with 189 fresh
read-time hashes. V's 166 hashes, 21 checks, author9/seven bindings, closure12/24
bindings, publication7 and complete27 committed paths/blobs are freshly checked.
Its 24 lexical testset slices, 48 original rows and 32 direct historical Git file
comparisons remain exact. Each historical run separately has 511 PASS across those
selected groups; BOTH entire runs failed. No old collector/auditor was executed.
U master1512/GREEN1489 and T891 are rehashed with explicit historical OLD-test ->
U/original-test.jl and old continuation -> U/before-U mappings. U closure123 maps
its later continuation identities only to V/before-V. No old pin was rewritten.
Fresh full20 process groups are absent, no Julia process exists, user6 match and
host/remote refs are 48771ac/2b546e9.

Use only the exact construction frozen in `original-testset.txt`, taken from
`test/simplex_start_state_tests.jl`'s existing final-factorization interruption
case. The entire six-assertion block remains byte-exact in both actual and frozen
files. Its matrix, objective, row bounds and all constructor expressions stay:
Float64 2-row/2-column diagonal [2,3], objective ones(2), row_lower [2,3],
NumericalPolicy(Float64;crash=true), SolverOptions(verbose=false), shared progress,
and `_crash_workspace(initial,()->done[])` with default fill_limit=8.

Source defaults: legacy/native, PFI/native backend, algorithm dual, interval20,
iteration_limit100000/time_limitInf; refinement/recovery/phase_one/hypersparse and
sparse_pricing false; diagnostics kernel_timing false. Preserve every other option,
tolerance, precision and policy default from the pinned constructors, without
reconstructing a convenient subset or tuning. Direct workspace creation does not
run the public presolve/scaling pipeline just because those options have defaults.
The clock and offsets come from the existing progress constructor and are never reset.

Historical reuse stays separate: the six final-refactor assertions check expiration,
INITIAL return identity, iterations2, refactorizations>=2, slack basis[3,4], and no
crash_accepted. Ten pivot-stop assertions and six other-event cause assertions are
also already covered. A throwing observer cannot return `(ws,expired)`, so those
six originals are preserved as existing coverage, not silently weakened or claimed
to execute in this prospective case. New no-return/cause/event assertions are the
meaningful additional composition. No control run or repeated cancellation run is needed.

## Source-supported event sequence, conditional on reaching it

1. Construct INITIAL using the existing setup. An observer present during setup may
   receive refactor_initial before the local INITIAL variable is assigned; until
   armed after setup it must do nothing except bounded accounting if explicitly
   specified later. No callback may dereference an unassigned entry record.
2. Immediately after setup freeze the entry references, selected values and clock;
   arm the proposed probe, with done=false. Call the original private crash entry once.
   phase_crash targets INITIAL. Trial creation shares problem/progress/diagnostics;
   it owns fresh workspace/basis/factor/scratch/value containers. The initial
   refactorization attempt charge occurs before trial constructor assignment.
3. Preserve the original `reason == :refactor_other` done=true behavior. Additionally
   retain that callback's TRIAL reference and two scalar local work counters. The
   expected narrow path has two crash_pivot events then one refactor_other on TRIAL.
   Reject a missing/duplicate/wrong-state event; do not find a different stop point.
   Two pivots are below the untouched scheduled-refactor interval20; this makes the
   selected event the final refactor on this expected path, not by event name alone.
4. `recompute!` publishes refactor_other after its refactor counter increment but
   BEFORE primal/dual reconstruction. With this native policy `_maybe_refine...`
   returns true without consulting stop, recovery checkpoint branch is off and
   verbose=false skips progress reporting. Ordinary reconstruction still performs
   its forward and transpose solves after the callback. Therefore this callback
   is NOT a stop-before-solves boundary or capture of the final trial point.
5. The final guard sees done=true and latches stopped. `_crash_fallback` merges max
   iteration/refactor counters into INITIAL, then records crash_fallback through
   shared diagnostics before observer invocation. Its observer state must be INITIAL,
   distinct from the retained TRIAL. At this point record only fixed scalar metadata
   and the fallback reference, then throw the single original sentinel.
6. Choose one original `SingularException(42)` sentinel, matching the already-covered
   cause class. `_diagnostic_event!` wraps it in DiagnosticObserverFailure; the crash
   numerical predicate excludes that wrapper, so it escapes without another fallback
   or return. The outer timed-crash finally is inactive because kernel_timing=false.
   The caught wrapper's cause must be the identical sentinel. No direct stop exception
   is being injected and this is not proof of `_StopCallback.exception` identity.

All new runtime conditions above remain UNQUALIFIED. Source and historical tests
support the choice, not an executed trajectory. The six old assertions do not prove
this combined sequence or its exact event/callback counts on every architecture.
Missing events, wrong identities, altered values, unexpected work or failure to throw
must preserve raw evidence and STOP future qualification; no numerical retry or tuning.

## Proposed bounded oracle and observation inventory

No implementation exists yet. A later offline candidate must implement these explicit
checks and inventory actual fields/captures; it must not expand into a general recorder.
The following named roles are a source-level schema, not a bound on the retained graph.

| Record | Fields / size | Purpose and timing |
| --- | --- | --- |
| Entry owners | 17 roles: INITIAL, basis, factorization, scratch, basic_indices, states, primal, reduced_costs, costs, lower, upper, problem, progress, diagnostics, options, policy, scaling | Retain once after setup; compare identities after unwind. Options identity is immutable value identity, not mutable storage ownership |
| Entry values | Copies of basic_indices length2; states/primal/reduced_costs/costs/lower/upper length4 each | Seven owned vector containers, 26 copied entries total; no matrix/factor copy |
| Entry scalars | start_ns, iteration_offset, refactorization_offset; iterations/refactorizations | Three clock/offset scalars plus two local-work scalars |
| Probe | done, refactor_hits, fallback_hits, callback_count, pivot_hits, callbacks_after_fallback | Six bounded scalar fields; two retained state references TRIAL/FALLBACK; callbacks armed only after setup |
| Refactor capture | iterations, refactorizations | Two scalars, once on the original refactor_other callback; no numerical values captured there |
| Fallback capture | iterations, refactorizations; event_count crash_pivot/refactor_other/crash_fallback/crash_accepted; callback_count | Seven scalars captured before throwing; event_count dictionary lookups, no event-history copy |
| After unwind | Same seven scalar quantities | Compare once with fallback capture to exclude later selected work/events/callbacks |
| Exception/outcome | Original sentinel, caught wrapper, returned Boolean | Two reference roles and one scalar; returned must stay false |

There are 21 selected reference roles including the 17 entry roles, TRIAL/FALLBACK,
sentinel/caught, plus record containers, ordinary locals and aliases. This is not a
native-memory or graph-size cap. Seven copies traverse26 elements; post-unwind seven
vector equalities visit at most26 element pairs. No callback performs vector scans,
copies, matrix snapshots, solves, refactors, certificates or growing ledger updates.
Identity checks after unwind require no vector traversal. Fixed scalar record/tuple
construction and later assertion/output storage are additional cold diagnostic costs.
No claim of exact Julia allocation count/bytes is made before implementation.

Required prospective checks, grouped by meaning:

- Exactly one armed refactor_other and one crash_fallback hit, two observed crash_pivot
  events; refactor state TRIAL !== INITIAL, fallback state === INITIAL. Capture the
  retained TRIAL only at the chosen refactor event; no extra numerical call to obtain it.
- TRIAL differs from INITIAL in all eleven selected workspace/container roles through
  upper (the first eleven entry roles). Its problem/progress/diagnostics/policy/scaling
  are shared as constructed; its immutable options compare by value. These selected
  identities say nothing about transitive backend owners or deep scalar ownership.
- All seventeen INITIAL entry references still match after unwind; all seven copied
  value vectors still match. The slack basis remains [3,4]. Because FALLBACK===INITIAL
  and source performs no later INITIAL numerical writes on this throw path, these
  are endpoint checks supporting preservation; not a snapshot of values at callback.
- The fallback's local work matches max(entry_iterations, captured_trial_iterations)
  and max(entry_refactorizations+1, captured_trial_refactorizations). Require iterations2
  and refactorizations>=2 as inherited narrow expectations; do not force exact backend
  counts from those bounds. The `_crash_refactor!` finally cannot reduce recorded work.
  After unwind require the same local work and same four selected event counts.
- At fallback crash_fallback count1 and crash_accepted count0; crash_pivot count2 and
  refactor_other count1. These counts verify record-before-observer without calling
  recent_events (which copies the ring). They do not capture the full event sequence.
  callback_count equals its fallback capture afterward and callbacks_after_fallback=0.
- Original caught type DiagnosticObserverFailure, cause===sentinel, returned=false;
  same shared progress/start_ns/offsets/options/policy. No result, certification,
  rollback, original-model certificate transfer or real time-limit expiry is inferred.

The instrumentation does not retain owned trial-vector values. Retained TRIAL and
INITIAL graphs remain mutable until unwind. Post-unwind comparison is not capture
of hidden intermediate values or proof of observer neutrality. Guards may be checked
multiple times; no exact stop invocation budget is inferred from the event names.

## Existing work and continuation

This context executes native initialization/reconstruction and trial construction,
candidate FTRAN/BTRAN/update, final refactor and post-event reconstruction if admitted
later. Factory/backend, factor-history operations, candidate scans and scratch are
additional to the observation inventory. Initial/trial recovery=false suppresses
that checkpoint branch in this fixed source path; it is not a general zero-checkpoint
or zero-internal-work assertion. Kernel timing stays false, so dictionary kernel
counts are not an observed backend work oracle. Source-derived work is not complete
PREforward/import/native accounting. All costs are cold prospective diagnostics;
there is no new production work/memory and no benchmark/speedup claim.

Next S5-X permits only a separately saved UNEXECUTED diagnostic candidate implementing
this one source oracle, with exact construction inverse and complete actual field/
copy/scan inventory, offline checks and fresh independent numerical/work review.
No parser/import/Julia, launcher, permanent test change or numerical admission follows
from W. Preserve all V/U and older failed raw/reviews/audits and all broader gates.
