# S5-AA: crash fallback observer test integration

Exact Z candidate ce256932a4bbda14bb9c55678525d6506a8e63732683442def57b22873b0415f
was installed as test-only c5c31473614298a6e1f2c4cacb8b2461dedd1c71 and cherry-picked
to actual master d02416c108f06fcd41d58e0a1980b70a51fef9ef. The4774-byte original
start-state test remains a byte-exact prefix; only193 lines are appended, including
explicit top-level LinearAlgebra:SingularException and50 explicit Test assertions.
Six historical final-stop assertions remain in the prefix. The separate unchanged
start-guard file retains ten pivot-stop/six observer-cause evaluations; they were
not rerun or falsely attributed to the prefix. Production, environment configuration
and CI are unchanged.

## Executed scope and evidence

Exactly TWO new Float64/PFI/native lifecycles ran: one GREEN and one actual-master,
each with one INITIAL initialization and one crash invocation. No old testset,
control, warmup, manager/scalar loop, extra solve/certificate or numerical retry ran.
Each focused actual-test extraction produced52/52 passes (50 permanent plus2 driver),
no failures/errors/broken, four entry counts[1,1,1,1], all50 literal true predicates,
33 audit gates, and10 separate author postchecks with9 bindings. GREEN has1468 launch
pins, master1493; original admission1464 and mandatory1463 were independently reviewed.
Each has eight original/portable raw files and three bound invocation/reservation/log
files. Master stage acceptance has36 bindings including all23 GREEN evidence paths.

The driver verifies complete actual-test/prefix/suffix hashes and loaded module source
root. Five unique insertions have an exact byte inverse: four PRE-entry counters
(case, initialization, crash, testset) and one post-unwind fixed raw serialization
before assertions. All50 assertions and the canonical numerical core remain unchanged.
The explicit import survives suffix-only extraction; rejected initial Z source is
never used. Raw early failures would fail closed; no such numerical failure occurred.

Admission, GREEN and actual-master admission were independently accepted before their
respective authorized actions. The final actual-master result review is a separate
required gate; its precise verdict is in the companion review record. Exit0 alone
is not acceptance. Separate closure/publication must pass before diagnostic push.

## Observed boundary

Both runs preserve the original SingularException(42) as the identical wrapped cause
in DiagnosticObserverFailure, with no crash return. Exactly one captured TRIAL
refactor_other occurs before ordinary reconstruction; the original done latch stops
at the later guard. INITIAL fallback applies work maxima and records crash_fallback
before invoking the throwing observer. Both runs observed entry work0/0, refactor2/2,
and equal fallback/after records: iterations2,refactorizations2,crash_pivot2,
refactor_other1,crash_fallback1,crash_accepted0,callbacks6. No later selected work or
callback was recorded. One refactor hit, one fallback hit and two pivot hits were
captured; trial_present/done/cause_identity true and returned false.

All17 INITIAL identity roles and seven selected vector values remain preserved;
11 TRIAL container roles differ, while problem/progress/diagnostics/policy/scaling
are shared and immutable options retain value identity. Clocks42906190618053 GREEN
and43552939605211 master must be read against their raw records; offsets stay zero.
Native refinement/recovery and kernel_timing are false; default routing/tolerances,
Inf, interval20 and original stop callback remain unchanged. These selected endpoints
are not callback-time snapshots: retained TRIAL stays mutable until unwind.

## Process and resource scope

GREEN runner89398/start4290119/PGID89395 and child89399/start4290167/PGID89399;
master runner90322/start4354790/PGID90313 and child90323/start4354840/PGID90323.
Boot dade7243-9103-4398-bb45-fa28fbc0be72, all26 prior groups/sessions absent postexit,
no Julia remains. Each run has six resource samples. Minimum RAM22137132/22070736KiB,
maximum swap0; terminal RAM22583232/22516760KiB and swap0. Inclusive elapsed
6.012333269005467/6.011550006995094 seconds covers launch/import/compilation/setup/
serialization and is NOT a benchmark or speedup comparison.

Julia/BLAS1, heap hint2GiB, VM8GiB, RAM>=6GiB, swap<=1GiB and terminalwall120 were
admitted. New local guard retains shared advisory ownership, exclusive attempt/output
reservation, atomic metadata and prefolder failure logs. Current/terminal process
identity, exact command/pin/path/log linkage, positive pid/pgid/start_ticks and boot
are checked. Terminal RAM/swap is separately recorded and audited. Source-supported
compiled-modules=existing prevents ordinary fresh compilecache workers; it is not
cache/import confinement or hidden loader/method execution capture.

## Preserved offline failures and corrections

The first new entry audit retained three false gates for historical continuation
texts (Y publication and Z initial/reviewed inventories). Separate entry-2 uses only
exact Z.before-Z mappings and passes38 gates. All old evidence remains unchanged;
Z report/next-plan before-review mappings, Y before-Y, X before-X and U before-U/old
precision-test mappings remain explicit. Current changed start-state test maps to
AA/original-test.jl only for its exact historical47b2cc12... hash.

Preliminary independent admission review identified missing old-session membership,
insufficient identity field validation and absent terminal memory capture. Draft
common.py.before-session-fix and all three before-identity-fix sources remain
preserved. One session correction and one identity/resource amendment add only
Python guard/auditor checks; source RED/GREEN and27 amendment tests pass. Initial
source-preparation13/guard-source byte identity describe the initial guard, while
identity-fix.json and final manifests bind the corrected guard. New92 synthetic
failure tests and15 linkage tests pass; reviewer exercised77 additional read-only
gates. None is a Julia regression test. Synthetic prefolder refusal/log and exclusive
write pending file remain preserved. No failed numerical attempt was hidden or rerun.

## Computational work and retained memory

No new production scans, solves, copies, conversions, allocations or retained memory
are introduced. Independent reviews explicitly found no unnecessary NEW production
work/memory. No before/after benchmark is justified for the unchanged production path.

The new cold permanent case has11-field probe plus done Ref, three17-role owner
tuples (TRIAL conditional), seven vector copies26 entries, fixed clock/work/event
records,50-Bool result tuple and50 Test assertions/result storage. Endpoint comparisons
visit at most26 vector pairs plus two slack indices; owner comparisons cover11 distinct,
17 preserved and six shared/value roles. If generalized, copies/equalities scale with
m and n+m. Callback work is bounded counters/references/fixed scalar records, without
array scans/copies/conversions/numerics/growing ledger or matrix/factor snapshots.

Driver-only additions are four counters, one output Ref, fixed raw dictionaries90
entries plus report/Test bookkeeping, source/extraction/instrumentation strings and
serialization. These are nonzero cold costs; no claimed neutrality. Existing factory,
backend, validation, reconstruction, candidate scans, updates and factor work remain
additional and dimension/nonzero/history dependent. Timing-disabled counters do not
prove zero work or complete PREforward/kernel/native/import accounting.

Probe, closures, owner tuples, exceptions and aliases retain transitive mutable graphs
until unwind; bounded reference counts are not graph byte caps, native-free or GC
proof. No full-state rollback, certificate transfer, real expiry, observer neutrality,
precision-wide behavior, full-suite/x64 success, historical CI cause or speedup is
claimed. Both numerical allowances are consumed. All AA/Z/Y/X/W/V/U and older raw,
launchers, drivers, audits, failures and reviews are frozen after closure.

Next S5-AB is source/evidence-only reconciliation of the original S5 handoff inventory
against accepted coverage, to avoid repeating qualified work and identify only concrete
remaining obligations. CI remains off, HH reuse disabled; broader S3/S4/S5/S6/fullsuite,
bootstrap/cache/init/wholecaps/native-retention/Q GC/outlier and rejections stay open.
