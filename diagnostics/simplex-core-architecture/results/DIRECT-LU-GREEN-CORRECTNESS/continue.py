"""One-shot continuation after independent result acceptance."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[4];D=Path(__file__).resolve().parent
review=json.loads((D/'review.json').read_text())
if review.get('accepted') is not True or review.get('findings')!=[]:raise SystemExit('Result review not accepted')
status=R/'diagnostics/simplex-core-architecture/STATUS.md';roadmap=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
if status.read_bytes()!=(D/'STATUS.md.before-green-correctness').read_bytes() or roadmap.read_bytes()!=(D/'roadmap.md.before-green-correctness').read_bytes():raise SystemExit('Continuation moved')
s=status.read_text();start=s.index('## Exact next action\n');end=s.index('## Previous missing-zero experiment',start)
new='''## Exact next action

Corrected Direct LU / Markowitz GREEN is independently accepted for scoped
Tasks1–2 component/lifecycle correctness. See DIRECT-LU-GREEN-CORRECTNESS.md and
results/DIRECT-LU-GREEN-CORRECTNESS/review.md/json. One new process:19,557PASS,
0FAIL/ERROR/BROKEN,exit0,all12groups,15auditgatesPASS,11postchecksPASS.
Inclusive40.831812370s is NOTbenchmark time. All4616launch/4614sealedpins and
514baselinepaths unchanged. Stage admission bound4383paths.40resource samples
plus terminal:minRAM21,909,480KiB,swap0; full202groupsANDsessionsabsent/noJulia.
No WARNING marker in this run. ReservationCONSUMED; no repeat/tuning.

PrivateCSC/nzval repair passed export130 assertions; three directmanagers,
native/Markowitz, normalization/orientation, ownership/copy/update/refactor and
fallback fixtures passed. Otherprecisions qualify testedfallback only. Source
work ledger remains source-derived, not instrumentedbackend/allocations. No
speedup/native-refinement-equivalence/fullsuite/x64/publicsolver claim or
productionpromotion. OriginalRED3expectedFAIL remainsaccepted; oldGREEN89PASS/
1ERROR/falseaudit unchanged. All old and new executed artifacts remain frozen.

Next concrete work: original Task3 OFFLINE cost-driver/input/admission preparation
in docs/superpowers/plans/2026-10-14-direct-lu-markowitz.md. Freeze n32/96 x
sparse/dense inputs and entering/DSE/B4/B8 bits;24manager/backendcells,
3warm+7measured alternating pairs, two serial <=90sprocesses in later separate
exactadmissions. Include wholeconstruct/eightupdates/tworefactor costs, bytes/
events/compile/GC and finalreachablememory. Preserve original per-cellselection
rules and second-refactor bufferreuse costs. No cost driver/run prepared by this
result step. Standing short permission sufficient; exact independent admission
still required. Task4publicintegration/promotion remains later, neverautomatic.

Admission closure/closure-final/publication-final/publication-review CURRENT
STATUS/roadmap hashes map ONLY to DIRECT-LU-GREEN-CORRECTNESS before-green-
correctness copies (eight exact continuation.json mappings). Earlier maps and
raw/rejections stay unchanged. Master6f68e24 unchanged; CIoff/HHdisabled/
automationpaused. Broader architecture plan OPEN.

'''
status.write_text(s[:start]+new+s[end:])
with roadmap.open('a') as f:f.write('''
## 2026-10-15: corrected direct-LU GREEN accepted

One independently admitted correctedGREEN completed19,557PASS/0FAIL/0ERROR/
0BROKEN,exit0,12groups,15auditgates and11postchecksPASS. Full4616launch/4614sealed
pins/514baselinepaths unchanged;40.831812370sinclusive NOTbenchmark.40samples+
terminalminRAM21,909,480KiB/swap0,full202groupsANDsessionsabsent/noJulia.
Independentresultreview accepts scopedTasks1–2 correctness, no unnecessarynew
productionwork/memory. Report DIRECT-LU-GREEN-CORRECTNESS.md. OriginalREDaccepted,
oldfailedGREEN89PASS1ERROR/falseaudit preserved. Allslotsconsumed/no repeat.

Next originalTask3 OFFLINE costinputs/driver/admission preparation:four n32/96
sparse/densefixtures,24cells,3warm+7measuredpairs perprocess,twoserial<=90sprocesses
onlyafterseparateexactadmissions. Include construction/export, eightupdates and
tworefactor lifecycle, bytes/events/GC/compile and finalreachablememory. Keep
originalselectionrules; no tuning from output, no automaticpromotion. No current
costrun/driver/publicsolverintegration. Task4 later. Correctness is notspeedup,
fullsuite/x64 or nativecombined-refinementequivalence. Eight prioradmission
closure/closure-final/publication-final/publication-review continuationkeys map
ONLY to newbefore-green-correctnesscopies; alloldermapsfrozen. Master6f68e24/
CIoff/HHdisabled/automationpaused unchanged; broaderplanopen.
''')
with (R/'.superpowers/sdd/2026-10-14-direct-lu-markowitz/progress.md').open('a') as f:f.write('''
- CorrectedGREEN executedONCE after freshseal+independent4383bindingadmission.
 19557PASS/0FAIL/0ERROR/0BROKEN,12groups,exit0,15audit/11postcheckPASS,
 40.831812370s inclusive (notbenchmark);40samples+terminalRAMmin21909480KiB,
 swap0;separate202PGIDANDsessionclosure/noJulia. Independentresultreviewaccepted.
 ScopedTask1–2correctness gatecomplete; candidateprivate/productionunchanged.
 NextoriginalTask3offlinecostdriver/input/admission; no costexecute/promotion.
 AllpriorRED/failedGREEN andnewrawscripts frozen, no cleanup/rerun.
''')
print('Scoped correctness continuation updated after independent acceptance')
