# S6-AN: native owned-bound cleanup entry interruption qualification

New diagnostic only after fresh independent S6-AM coverage/work review. Not a
historical timeout repair, not a replay of AL or old S5-C tests. No permanent
source/test/workflow changes and no changed successful-test oracle.

## Exact scope and comparability

1. Fresh host boot/start_ticks/command/ref/process check, independently from any
   launch or pinned edits. Pin source/test/runtime/environment/helper/driver and
   actual original inputs/options/policies/threads. Compare exact helper/monitor
   against AL and unchanged native target's six predicates. Validate sixuser hashes.
   Existing guard: one numerical Julia/BLAS1, heap2GiB,VM8GiB,availableRAM>=6GiB,
   swap<=1GiB; forbidden big/largo/AnyMOD and aliases. Freeze pinned files in flight.
2. Exactly TWO new Float64/PFI lifecycles in one guarded process: case :stop and
   case :throw. For EACH call actual shifted_primal_workspace() once, initial
   _primal_optimize!(ws,()->false) once, install default NumericalPolicy(Float64),
   construct one SimplexRunBudget and call public run_from_basis! once. Totals:
   2helpers,2initialoptimizers,2budgets,2drivers. No other workspace, successful
   control, solve(problem), component/quality/certificate/basis call, private
   retry, observer, adapter, factor mutation, microcase, warmup or numerical dry run.
   Preserve helper shift==1 and initialOPTIMAL assertions for each case. Original
   six permanent success predicates/helper source remain byte-identical; AN does
   not call their final-success oracle on an intentionally interrupted case.
3. Defaults stay AL-comparable: primal,PFI/native,steepest_edge,iteration20,time30,
   primal/dual tolerance1e-7,zero1e-12, same represented matrix/objective/bounds.
   Adaptive helper policy/refactor_timing=false; default native replacement after
   initial optimizer. No start_ns assignment/reset, longer/removed limit, sleep,
   warmup, precision/tolerance/global/backend change. Every case owns its original
   workspace start; do not inherit another case's clock or claim paired timings.

## Declared interruption and complete observations

4. Use one fresh bounded callback counter per case, increment BEFORE return/throw.
   :stop returns true at every invocation. :throw throws one precreated
   SingularException(29) instance at every invocation. No callback captures or
   mutates workspace state, performs numerical work or records a growing ledger.
   Catch outside public driver to record identity. Mandatory exactly ONE callback
   call in each case; expiry short-circuiting to zero calls rejects qualification.
   No direct call to the callback as a preliminary test.
5. Enable existing kernel_timing only AFTER real helper setup. Capture setup,
   initial optimizer boundary, native predriver and return/throw boundaries with
   tiny owned selected state, journal owner/identity and storage aliases, original/
   active bounds/costs, primal/prices/rho/basis/states, model/options/policy/scaling,
   budget/progressstart/limits/offsets, counts/events. Serialize/rationalize after
   both numerical windows; snapshots consume the unchanged shared budget and are
   not timing-neutral. Setup zero disabled counters are not zero setup work.
   Pre-forward driver entry counters include throws; internalcalls are not entries.
6. Preserve actual status/message/payload or caught exception, callback count,
   monotonic brackets and all failures. Require initial endpoint bits and selected
   native predriver state to match AL (x=s=-9*representedtol,basis[2],states
   [AT_LOWER,BASIC],active owned bounds). Initial optimizer observed AL work
   2FTRAN/3BTRAN/2pricing/0refactor is a declared comparability gate per case;
   different work must be preserved and reviewed, not silently normalized.
7. Driver expected work in BOTH cases: zero across all existing kernel call
   counters, zero iteration/refactor deltas, same selected values/basis/model,
   same journal identity/owner and active bounds/storage aliases, unchanged clock,
   options restored and budget synchronized. This is not zero total computational
   work: policy/options/budget bookkeeping remains. No new correction, restoration,
   phase_cleanup, certification or failed-certification event.
   :stop expects TIME_LIMIT with exact existing feasibility-recovery message,
   primal/objective/basis all nothing and exactly one added checkpoint event.
   :throw expects the identical precreated exception, no returned result and no
   added event. Do not convert a thrown callback to numerical failure or call any
   recovery/certificate helper merely to inspect the outcome.
8. Callback count1 identifies the declared route. A wholly below30s bracket also
   excludes deadline expiry under monotonic-clock assumptions; a straddling bracket
   must remain classified ambiguous, even with a known callback invocation. If
   callback count0 or any expected gate fails, retain rawfailure/exit and STOP the
   qualification without retry or replacement; do not silently continue to invent
   additional cases. If first case cannot qualify, second may remain unexecuted
   and totals must report actual pre-forward entries, not planned totals.

## Audit and review

9. Fresh separate hostabsence check immediately beforelaunch. After exit verify
   process.json/returncode/reason, identities/pins independently, actual source,
   rawportable hashes and a NEW offline auditor using actual captured bits. Exit0
   alone is not acceptance. Do not execute any accepted AL/AK/AJ/S5-C or historical
   H/I/J/X–AI driver/auditor/parser/corpus/reference/cost run. No CI dispatch.
10. Fresh independent numerical/work/memory review before any separate permanent
    test-only plan. This proves at most two declared native entry contracts. It
    does not measure real deadline expiration, establish oldCIcause, validate all
    recovery lifecycles or satisfy fullsuite/x64/broaderS6. Preserve the older three
    failures and all S2-A/S6-J/wholeAF rejections. Update STATUS and continuation.
