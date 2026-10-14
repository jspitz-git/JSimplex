# MA-S driver loading correction — offline preparation

A separate, UNEXECUTED driver in results/MA-S-LOAD changes exactly two expressions
in the frozen MA-S driver. It enters the latest Julia world around the complete
correctness phase and around the complete cost phase after the candidate methods
are loaded. No production code, MA-R arithmetic/tests/fixtures, cost schedule or
acceptance threshold changes. Runtime success, allocation reduction and speedup
remain unverified. MA-S/run-1 stays a failed qualification and must never be rerun.

## Cause and narrow correction

The original run recorded smoke16PASS, exactRED2expected failures, then15partial
PASS/2ERROR at eligibility and reset_route_counts!: world42871 versus42908. Source
shows Base.include inside the already executing main() before direct calls into
preexisting qualification() and costs(index). The previous independent result
review accepted that diagnosis, not candidate numerical equivalence.

New driver line97 is records[]=Base.invokelatest(TST.qualification); line102 is
raw["costs"]=Base.invokelatest(costs,index). Both callable bindings already exist
before main starts. Newly loaded candidate/instrumentation bindings are looked up
inside these latest-world phase calls. The installed Base_compiler.jl documents
most-recent invocation and aliases Base.invokelatest to Core.invokelatest. That
source is freshly hash-bound as read-time evidence, not retroactive MA-S launch
coverage. Correctness exceptions still propagate to the same @testset/catch;
finally still writes raw and verifies ambient precision/rounding restoration.

No invokelatest is inserted in batch, window, any backend call or numerical helper.
The complete helper prefix including costs() is byte-identical. One boundary is
reached before all correctness work in process1, and one before all cost work in
each process: at most4phase invocations across the prospective3-process sequence.
The latter surrounds the complete cost loop, so every timed reference/candidate
call executes from the same latest-world context. It is outside the internal
@timed batch. No warmup, first-call solve, calibration or per-window latest call
is added; compilation may still affect first warm windows and measured compile/
recompile must still be zero. Invocation dispatch can cost time/allocations and
impairs caller return inference; these are cold phase-boundary effects included
in guarded process time, not claimed to be zero. Return values already enter
Ref{Any}/Dict{String,Any}. No new retained arrays, factor copies, scans or solves.
No unnecessary NEW production computation/allocation/retained memory was added.

Moving include earlier would invalidate the original missing-route RED. A complete
toplevel driver rewrite would alter more of the raw/finally contract. The selected
two phase boundaries preserve that control flow and avoid per-operation overhead.
The change is source-supported, not a tested runtime repair or general loader proof.

## Offline evidence and preserved scope

Fresh entry12checks: HEADf86674cde521d139c885e66ba64f77967f91cf64 and remote,
master6f68e24e8ddac42b948da8fcc2d636c010751194, linked worktree, full160groups
ANDsessions/noJulia,514source identities,6protected files, all4262old launch pins,
49result-review bindings and failed-run/no-later-run state. No old stored script,
Julia query/parser/import/compiler/numerical call, launcher or guard was executed.

New prepare.py was saved before execution and executed once. Python source RED
finds two missing latest-world markers in the original driver; this is not new
Julia RED or an independent reproduction. Source GREEN11checks/13bindings verifies
both boundaries, exact whole-driver inverse after exactly two substitutions,
identical helper/timed prefix, include-before-boundary order, raw/finally/tail,
original smoke/RED-before-include and same relative path depth. The prior actual
world-age failure remains the runtime regression evidence. No Julia syntax,
dispatch, correctness or performance PASS is inferred from these text checks.

The new driver sits at the same directory depth, so ../MA-R and ../../../../src
resolve to exactly the original sources. Existing MA-S driver/launcher/auditor,
all reservations, raw and false gates remain frozen. The original audit17true/
6false stays all_passed=false, with empty-window truths vacuous. The previously
noted duplicate cold Python memory validation remains a nonblocking deferred minor
in the old auditor; this correction does not edit it.

Current MA-S result-review/execution-closure/execution-publication STATUS/roadmap
bindings map ONLY to MA-S-LOAD/STATUS.md.before-MA-S-LOAD and roadmap.md.before-MA-S-LOAD
through six explicit entries in continuation-map.json. Older execution-before and
preparation-before mappings remain intact. Source pins/entry are read-time checks,
not a fresh numerical admission. See plan.md for the next separate admission.
Independent review is recorded in results/MA-S-LOAD/review.md and review.json.

Production/test/user environment/master unchanged; CIoff, HHdisabled and automation
paused. Broader plan open. This step prepares and reviews the correction only;
it neither launches a new experiment nor enables conditional production Task3.
