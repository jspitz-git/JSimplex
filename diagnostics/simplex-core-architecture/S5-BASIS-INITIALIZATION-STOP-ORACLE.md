# S5-Q: supplied-basis checkpoint stop oracle feasibility

The selected composition has a source-supported discriminator. S5-Q freezes ONE
prospective exception oracle using an existing setup as source material. It does
not create a numerical fixture, Julia candidate, driver or launcher, and does not
execute Julia, parsing/import/compilation, a factor, solver, certificate or old
script. Runtime reachability and all proposed assertions remain UNQUALIFIED.

## Existing construction and preserved evidence

Use only the Float64 / PFI / native-backend setup already present in
`test/simplex_precision_tests.jl`, testset "Transfer rebuilds the actual typed basis
and retains cumulative work". `results/S5-Q/existing-setup.txt` is a verbatim text
excerpt, with its terminating newline; it is not an executable new fixture.
It contains the existing 2-row/2-column matrix, model metadata and bounds, supplied
basis [1,2], SolverOptions and NumericalPolicy. No new matrix or arithmetic witness
is introduced. Do not run the later transfer, direct solve, weight checks, success
control, resume or any loop over other types/managers/backends.

The selected policy has native numerical_profile, recovery=true and implicit
solve_refinement=false. Its adaptive strategy, sparse/hypersparse flags,
phase_one/crash flags, max_refinements=4, refactor_timing=false and all other fields
stay as written. This is recovery-enabled native policy, not the full checked
profile. Those flags do not themselves call crash or precision transfer here.
Original options use devex, iteration_limit=30, verbose=false and the unchanged
infinite default time limit. No tolerances, precision or clock are tuned.

The only prospective setup adaptation is diagnostics: replace the existing
Nothing-typed progress construction with a progress value having the ordinary
observer's concrete diagnostics type. Preserve its start time, objective vector,
constant, scaling, offsets7/11 and policy. Enable existing kernel timing to observe
its limited counters. Add the explicit guarded stop and original exception
sentinel. No production hook, method overwrite or module clone is needed. These
are source-level adaptations to be made reviewable by an exact inverse in a later
separately admitted stage; no such implementation is present now.

Two stored CI rows record 1504/1504 separately in EACH historically failed run.
Both complete test files match current source. This count covers the entire
transfer testset, including later work and multiple combinations, not the selected
setup alone or this new stop composition. P's 400/group coverage is reused, not
rerun or added to 1504 as independent new coverage. Historical pin membership alone
is not execution evidence.

New evidence has18 literal checks and178 fresh read-time hashes. Preparation was
saved before execution and is self-bound. Full P157, author7 and closure25 bindings
were freshly verified before changes; P's12 closure,5 publication and4 whitespace
checks remain preserved. P's two collector failures, five exact source EOF warnings,
O rejected admission/correction and all older false audits remain unchanged.
Initial host refs match remote: diagnostics4cd0d7a, master35a6a9f. Complete fourteen
prior groups are absent and no Julia exists on the recorded boot. Protected user
files are hashed again. No production/test/environment/cache/CI edit is made.

## Discriminator and selected oracle

The proposed fixed observer/stop state machine is specified in oracle.json.
It relies on source order rather than counting arbitrary quality/refinement stops.

1. The default recompute can call its checkpoint observer before refactor_initial.
   Count this callback, but it cannot arm the explicit stop. Its stop is the default
   clock guard, not the supplied explicit callback.
2. Exactly one refactor_initial callback latches the workspace and the two default
   basis-vector owners. Only after it returns does initialize_from_basis install
   policy, copy the supplied basis, validate bounds and invalidate checkpoints.
3. Exactly one refactor_other callback on that same workspace, with local
   refactorizations=1, marks the imported stage and retains the two imported basis
   owners. Its event is recorded before this observer; this callback precedes the
   imported primal and transpose solves.
4. Only the subsequent checkpoint observer on that workspace, after both latches,
   arms the throw. `_remember_verified_basis!` has already passed its first stop,
   checked reliability and allocated the candidate checkpoint. Its very next
   statement after the observer returns is the second stop, BEFORE storage and
   checkpoint-event recording. No refinement callback can intervene at that source
   boundary. The ordinary observer is not _StageObserver.
5. The armed stop throws the original sentinel. Retain the explicit _StopCallback
   guard so its exception identity can also be checked. The observer itself does
   not throw: the expected caught object is the sentinel, not a diagnostic wrapper.
   Missing, duplicate or out-of-order latches/hits must fail the prospective oracle.

The concrete implementation must retain every selected assertion family in
oracle.json: no returned workspace, caught/guard original exception identity,
exact latches/throw/callback counts, caller basis identity and value preservation,
imported basis ownership relative to caller/default vectors, shared problem and
progress metadata, consumed work at throw/unwind, empty imported checkpoint history,
phase generation, and selected recorded-event counts. The retained workspace is
mutable until unwind. This is not a full vector snapshot, backend-factor capture,
whole-function rollback, arbitrary callback-mutation contract or collection proof.

Under the selected successful-prefix preconditions, two explicit stop calls are
expected: before imported checkpoint quality and after its observer. Refinement is
false, so there is no extra explicit refinement stop. Four observer callbacks are
expected: default checkpoint, refactor_initial, refactor_other, imported checkpoint.
Only three diagnostic events are recorded; checkpoint count stays1, and the final
recorded event is refactor_other. The imported checkpoint observer is not a second
recorded checkpoint. The earlier checkpoint has already been removed locally by
invalidation even though its historical diagnostic count remains.

The selected workspace has iterations0/refactorizations1 at throw and unwind.
Clock/start/offsets7/11 and diagnostic/objective/scaling references remain shared;
mutable diagnostic work is not rolled back. These assertions do not prove real
clock expiry; the original infinite time limit is retained. Unreached or failed
reliability makes the future qualification fail and stop, not justify retuning.

## Conditional work and diagnostic cost

This is a conditional source accounting table, not a new runtime measurement or
complete PREforward/native/import budget. m=2, n=2 and v=4 in the existing setup.

| Work before the proposed throw | Conditional source expectation |
| --- | --- |
| Default construction and imported reconstruction | One factor factory and one imported refactor entry; four counted base solve entries, FTRAN2/BTRAN2, refactorization1. Factory/backend/internal work is additional. |
| Refinement | Zero correction entries with unchanged solve_refinement=false; max_refinements4 does not enable it. Existing quality checks remain enabled through recovery. |
| Checkpoint admission | Two checkpoint constructions, five copied vector containers each:10 containers and2(m+4v)=36 copied elements. First is stored then invalidated; second allocated before observer but not stored after throw. |
| Checkpoint reliability | Up to four solve_quality! entries over the two calls, with fresh assembly, RHS, gathers and quality scratch; failure short-circuits. On a reached second observer, both checkpoint reliability calls have passed. |
| After targeted stop | Imported checkpoint store/record, outer finite/reliability check and final outer reset_devex! are unreached. The imported refactor's devex reset has already occurred. |
| Supplied input preservation instrumentation | Two caller-basis copies totaling m+v=6 elements before invocation. No model/sparse-matrix copy, callback array scan/copy, extra solve or growing ledger. |
| Fixed observation metadata | Nine listed reference roles (workspace, default/imported/caller index/state owners, sentinel, guard), plus fixed latch/callback/stop/throw counters, ordering/armed flags and selected work/event scalars at throw. Caller model/progress/diagnostics, closures and record containers add aliases. |

Hypersparse is retained from the existing policy. Existing counter values do not
prove four backend solves: an empty pipeline route may satisfy an entry without a
backend solve, while support/caches/graph/scaling work may be additional. Do not
assert all hypersparse counters are zero or reopen a general pipeline-budget audit.
This stage does not establish complete factor-internal attempts, allocation traffic,
retained native memory or import work. Sparse/model/residual scans and scratch costs
still scale with dimensions/nonzeros; scalar precision changes costs. No new
precision cases are authorized by this Float64 selection.

The input copies protect the original Basis container contents, not every object
reachable from an arbitrary callback. Nine reference roles are not a graph-size or
GC bound; retained workspace/factor/cache objects can outlive the throw. Callbacks
add fixed scalar and identity work only. Post-unwind basis comparisons visit up to
six saved input elements, plus six imported-vs-supplied elements if both basis
vectors are compared; scalar/identity/policy checks add bounded cold work. No
benchmark is warranted because production is unchanged. No unnecessary NEW
production work, allocations or retained memory are introduced; no speedup is claimed.

## Decision and next boundary

The offline discriminator is feasible and the selected assertions address P's
unqualified composition. It is not runtime qualification, a solver defect or proof
that the path never ran. Any future syntax/import/resource/numerical/assertion/cost
failure must be preserved and stopped, without silent repair, retry or tuning.

S5-R may separately prepare ONE unexecuted candidate with exact source provenance
and bounded observations, then obtain fresh review. No launch, actual test edit or
numerical qualification follows from Q. Preserve reliable-equation versus original
feasibility/certificate distinctions, CI-off, HH-disabled and all broader gates.
Independent review and separate PASS closure precede diagnostic publication.
