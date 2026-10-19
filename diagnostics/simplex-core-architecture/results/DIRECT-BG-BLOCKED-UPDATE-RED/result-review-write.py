"""Publish independent diagnostic-preservation review; does not admit qualification or execution."""
from pathlib import Path
import sys,json
H=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-HARNESS');D=H.with_name('DIRECT-BG-BLOCKED-UPDATE-RED');sys.path.insert(0,str(H));import control as c
r=c.rd(D/'result-independent-check.json');diag=c.rd(D/'source-diagnosis.json');summary=c.rd(D/'summary.json');run=H/'runs/red300';outer=H/'outers/red300'
c.require(r['all_passed'] is True and r['qualification_accepted'] is False and r['check_count']==46 and c.bindings(r),'Independent evidence drift')
c.require(diag['all_passed'] is True and len(diag['checks'])==14 and all(diag['checks'].values()) and c.bindings(diag),'Source diagnosis drift')
c.require(summary['qualification_pass'] is False and c.bindings(summary),'Summary drift')
c.require(not (run/'result-review.json').exists(),'Qualification review must remain absent')
report=(D/'REPORT.md').read_text()
c.require('did **not qualify**' in report and 'cross-file API' in report and 'separate offline staging repair' in report,'Report conclusions')
body='''# Independent RED result review — preserved failure accepted, qualification rejected

Accepted only the integrity, diagnosis and preservation of this single failed diagnostic attempt. RED qualification is false, GREEN remains blocked, and no retry, repair or timeout extension is admitted. This receipt is deliberately outside `HARNESS/runs/red300`; no accepted qualification result-review receipt is created there.

The new `result-independent-check.py` ran 46 read-only saved-data, source and fresh-host checks successfully. It did not invoke Julia, the original auditor, the closure writer or any numerical algorithm. The original 1,880-file seal and exact launch inventory still match current resolved paths and contents. Original admission, release, reservation, command, invocation, process identities and saved pins remain linked. All 17 run files and all four outer files are present with exact expected membership; the saved summary binds all of them. Audit, closure and summary hashes match. `REPORT.md` and its 14-check `source-diagnosis.json` are consistent with the independently inspected record and source.

## What actually ran

One Julia child was admitted under the sealed `red300` command. It exited 1 after 4.510998418 seconds including launch. The supervisor completed in 5.089358246 seconds; the outer returned 2 after 17.369819137 seconds including its checks and original auditor. No timeout or kill flag was set. The original auditor rejected the attempt with `all_passed=false`, `pure_timeout=false`, `Missing raw/units`.

The log fails at `using JSimplex`, driver.jl line3, before diagnostic test-module includes or main. It contains no driver BEGIN, UNIT BEGIN or TEST FAILURE record. There are no unit files and no raw.toml. Therefore zero assertions executed; zero named expected failures executed. The six expected N026 failures are unmet requirements, not six successful RED failures. There is also an explicit module-load error; zero recorded Test errors in the summary does not mean an error-free run. Exit1 alone was never sufficient, and the fail-closed auditor correctly prevented that false acceptance.

## Source cause and review gap

The staged `direct-factor.jl` defines DirectLowerBackend starting at line3 and types its policy field as `_NativePivotPolicy` at line10. Staged JSimplex includes factorization.jl at line20, then direct-factor.jl at line79. The staged source contains uses of the policy API but no definition of it. Its factorization.jl is byte-identical to the diagnostic checkout's older file. Verified production master `26e2291745999f485a74f643298ca997d65c7205` defines the enum at factorization.jl line17 and supplies the accompanying policy-aware factorization methods.

Task2 fixtures.py lines64–66 copy the diagnostic checkout's `R/src`; lines70–72 add the original factory/export and their includes. The overlay manifest confirms those source hashes. The immediate cause is an incompatible source-baseline composition: an adapter requiring the policy API was placed over a base that lacks it. Moving includes cannot supply a definition absent from the stage. This evidence identifies the first load blocker, not every possible downstream incompatibility.

My prelaunch admission review missed this static cross-file dependency. It verified hashes, exact inverses, provenance and top-level definition order, but treated matching the selected baseline as sufficient source compatibility. The previous offline author and independent reviews had the same gap. Their statements that runtime loading was unproven were accurate, but do not excuse overlooking the visible missing definition. Preserve those original receipts unchanged; this result records the adverse evidence and corrects the interpretation. The sealed inputs did not drift after admission, and the candidate arithmetic was never reached.

## Closure, resources, work and memory

The saved external closure and a fresh independent full-host inspection cover the 268 prior group/session identifiers plus outer163746, guard164456 and child164461: 271 identifiers total. None remain in either PGID or SID, and no Julia is visible through stat/comm/argv0/readable executable checks. All stat identities were readable. Inaccessible executable symlinks are listed in the receipts and remain an explicit visibility limit. Fresh boot and local/remote refs matched the sealed run. Review-time available RAM was 22,555,096 KiB; swap usage was zero.

The command and unchanged guard source retain Julia one thread, GC threads1,0, BLAS environment one thread, heap hint2GiB, address-space cap8GiB, available RAM floor6GiB and swap ceiling1GiB. These were configured constraints; the driver's runtime thread/loaded-path assertions were not reached. Four saved resource samples stayed within the RAM/swap limits: minimum available RAM22,412,188KiB and maximum swap0. Recorded child maxRSS was540,740KiB. The guard's292-second deadline and inclusive300-second supervisor limit were preserved, with ample time remaining at failure.

No unnecessary new production computation, allocation or retained-memory cost was found: production, candidate, tests, stage, numerical policy and environment remain unchanged, as supported by fresh source/runtime/stage and seal checks. This review adds only cold metadata hashing and diagnostic receipts. The failed initialization gives no measured update, solve, factor-copy, residual, allocation-saving or throughput result. The cold O(n^3) exact-rational test cost and full roster feasibility remain unknown because none of those tests ran. No performance conclusion or benchmark claim follows from the short elapsed time or RSS observation.

## Proposed separate boundary

Prepare a new ordinary stage against the verified accepted production baseline that supplies the policy API. Preserve the failed stage and every existing run artifact. Reconcile all differing baseline files and complete adapter dependencies; retain exact candidate/test bytes, original numerical predicates, native/Markowitz pivot policies, precision and tolerances. Do not supply an isolated enum shim or weaken the test oracle to bypass this load failure. Review changed manifests, source inverses and resource accounting independently before a separately admitted RED attempt. No repair or additional execution was performed by this review.
'''
with (D/'result-review.md').open('x') as f:f.write(body)
extras=[D/n for n in ['summary.json','REPORT.md','report.py','source-diagnosis.json','result-independent-check.py','result-independent-check.json','result-review.md','result-review-write.py']]
files=sorted(set(r['sha256'])|{str(p) for p in extras})
v=dict(accepted=True,findings=[],scope='BG blocked U failed RED diagnostic preservation and source diagnosis',phase='red300',qualification_accepted=False,numerical_acceptance=False,performance_acceptance=False,launch_admitted=False,green_admitted=False,expected_red_failures=6,assertions_executed=0,observed_test_failures=0,observed_blockers=['ordinary staged JSimplex load error: missing _NativePivotPolicy','no raw or unit outputs; RED qualification not reached'],sha256={n:c.sha(c.path(n)) for n in files},sealed_sha256=c.sha(run/'sealed.json'),launch_pins_sha256=c.sha(run/'launch-pins.json'),evidence_checks=46,scope_note='Accepted means failed-attempt evidence is sound. It does not mean RED qualification or permission to retry.')
c.save(D/'result-review.json',v);c.require(c.bindings(c.rd(D/'result-review.json')),'Published result-review drift')
print(json.dumps(dict(accepted=True,qualification_accepted=False,bindings=len(files),result_review_sha256=c.sha(D/'result-review.json'))))
