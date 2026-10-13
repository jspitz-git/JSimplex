# MA-F replacement admission: scoped Test context

This is a separate, single bounded replacement attempt authorized by the user's
renewed MA-F request and standing short-run permission. The failed MA-F attempt-1
is consumed and immutable. Do not reuse its reservation or execution controls.
Only the new MA-F-repair controls and new MA-F/attempt-2 output may execute.

The complete numerical schedule, candidate/fixtures/tests, work ledger, correctness
oracles and benefit thresholds are exactly MA-E/admission-reviewed.md, with ONLY
these explicit changes: driver context entry/exit and new control/config/output
paths. Reference and candidate ordinary overlays remain the original MA-E copies;
the auditor loaded-root anchor explicitly points there. Current baseline is
06172f6c11835259dcba093549d8b6ce3593b590 on codex/simplex-core-architecture;
master/primary6f68e24e8ddac42b948da8fcc2d636c010751194, primarybranchmaster.
Fresh full46PGIDs ANDsessions/noJulia required. Runtime1.13.0 and MA1.8.1 unchanged.

## Context correction and source verification

Original Test.push_testset/pop_testset calls do not exist in installed Test.jl.
Four source predicates fail on the old driver; the existing preserved runtime
UndefVarError is the actual failure evidence. The new driver captures parent and
depth, uses Test.@with_testset around the SAME Base.include, and checks exact
restoration in finally before the unchanged snapshot. Its inverse differs from
the original by exactly one context block. No test predicate or arithmetic changed.
The root is not explicitly finished, avoiding duplicate child recording.

Test.@with_testset delegates to Base.ScopedValues.@with; scoped context/depth
restore through normal/exceptional unwinding. Test's ordinary nested @testset
inherits RecordedTests and finishes once after leaving its child context.
The collector's finish records each child on that restored parent. All qualified
Test symbols, result fields and show methods must be inspected independently;
lexical symbol presence alone is not a semantic admission. Broken lacks source;
existing hasproperty handles this, all nonpass subtypes have orig_expr. Test.jl
and base/scopedvalues.jl are now prospective pins, not retroactive attempt-1 pins.
The repaired S4-AD driver is a source reference, not new execution coverage.

## Boundaries and execution

First independent admission review must accept exact manifest with no unresolved
findings. Then execute this directory's exact absolute seal-reviewed.py seal once,
inspect its hashes/refs/22commands/output, then launcher-reviewed.py run once.
Original MA-E sources never run or change. New copies of unchanged pure auditor,
finite oracle, guard and launcher support this new admission; they do not overwrite
or reinterpret old evidence. The new auditor changes only its loaded-root anchor.

RED<=30s requires exactly two named missing-helper assertions, no errors/broken;
qualification<=120s requires381assertions/48fixturecases/432rowpublications;
20alternating costprocesses<=60s each AND600s combined; entire launcher<=750s.
Julia/BLAS1, heap2GiB, VM8GiB, availableRAM6GiB/swap1GiB; no extra probe/warmup,
retry, longer limit, candidate tuning or assertion/threshold change. Every failure
stops subsequent stages and consumes this new reservation. No automatic additional
attempt. Serial process and post-exit source/refs/pins/resource/PGID AND SID gates
remain byte-identical except the explicitly relocated control paths.

Report first/cold and steady cost separately; all times/events/bytes/GC/compile
and outliers remain. Predeclared promotion thresholds: complete-forward paired
median C/R<=0.95 and>=6/7faster for BF256/BF512/Rational star32 BOTHstorage;
everyhardware/densecontrol median<=1.05. No benefit verdict without complete
measured pairs and all correctness/steadycompile gates. No automatic integration.
No new production work or retained memory; two cold scalar parent/depth bindings
and one context-restoration check per test-driver process, outside kernel windows.
No new scans/solves/copies in candidate or measured kernels. Diagnostic manifests,
imports, serialization and outcome records remain additional cold workflow work.

## Publication and continuation

Preserve every failure/raw/log, independent result/work/memory review then separate
PASS closure and exact complete staged names/blobs BEFORE failfast commit/push.
Actualsrc/test/Project/env/master/CI unchanged; automationpaused/HHdisabled.
MA-F current STATUS/roadmap closure/publication/review hashes map ONLY the new
MA-F-repair before copies after continuation edits. All older mappings unchanged.
Historical broken admission/report/driver and original failure remain frozen.
