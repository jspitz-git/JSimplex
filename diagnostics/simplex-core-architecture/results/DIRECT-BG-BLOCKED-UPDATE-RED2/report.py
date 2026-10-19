from pathlib import Path
import sys
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');H=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-RED2-HARNESS';D=H.with_name('DIRECT-BG-BLOCKED-UPDATE-RED2');sys.path.insert(0,str(H));import control as c
s=c.rd(D/'summary.json');c.require(c.bindings(s),'Summary drift')
report='''# Blocked BG RED2: failed cheap-reject allocation assertion

RED2 qualification is NOT ACCEPTED. The one authorized300s attempt reached the repaired ordinary JSimplex package and completed the first panel test unit, then stopped on unexpected P011. The six expected N026 failures were not reached. No GREEN or retry was run. This is not a timeout and a longer timeout does not address the observed failure.

## Exact evidence

Independent admission accepted1,996sealedfiles/1,997receiptbindings after6,938checks. Local/remote diagnosticHEAD b6c37d08e94fc3e6c6b28a967a8f995549929e94 and master26e2291745999f485a74f643298ca997d65c7205 were fixed. One exclusive reservation and one outer release. Driver actual loaded JSimplex path is the repaired task2-master-stage/src/JSimplex.jl; one Julia/BLAS thread. Original missing_NativePivotPolicy loader error did not recur in this attempt; no broader runtime compatibility claim follows.

unit-1.toml records complete=true, all94 panel-site occurrence rules,11,759passes/1failure/0errors/0broken across the four structural testsets. Only failure is P011 at diagnostic panel-tests.jl:103: `(@allocated K._bgb_eligibility(f,1)) == 0`. It uses the n32 all-zero structural carrier immediately after one warm call. P012's zero-work-counter assertion passes. All other panel assertions passed in this run; lifecycle and26streamcells were not entered.

The driver's unit-level acceptance guard runs AFTER saving the completed unit and BEFORE returning its counts to main. It throws on this unexpected failure. Therefore raw.toml deliberately reports complete=false,units_completed=0,totals=[0,0,0,0] despite the saved completed unit. Those aggregate zeros are not zero assertions or a pass. Logs show UNIT BEGIN/END1 and no UNIT BEGIN2. The original audit remains all_passed=false,pure_timeout=false,error=Exact exit. It stopped on process exit2 rather than expected1; no auditor rerun or post-hoc expected-result change occurred. Outer exits2, guard exits1, supervisor accepted=false without timeout/kill.

Inclusive supervisor14.206057686998975s; child/guard process elapsed13.563551717990777s. These include initialization/compilation/diagnostics and are not performance samples.13resource samples, minimum availableRAM21,831,500KiB, swap0, child maxRSS955,848KiB; terminal availableRAM22,573,628KiB. All required guards and immutable input checks passed. External closure includes all271oldgroups plus outer175431,guard175986,child175988 (274total), checking groups AND sessions with boot/start_ticks/command and no visible Julia.

## Narrow source interpretation

The stored failure records only the comparison expression, not the measured byte/event amount or allocation stack. The preserved source returns the dimension-rejection BGPanelDecision before the packed-band scan for n32; source construction of an immutable decision and zero logical counters does not prove zero heap allocation at the compiled call site. The recorder's enter!/finally work is outside the nested @allocated expression. Neither a specific compiler boxing/inference cause nor a production-kernel allocation defect is established by this record. Do not loosen P011, add warmups or tune the candidate on this failed attempt.

Next possible work is a separate source/log analysis of the exact allocation-test call boundary and its compilation context, followed by a concrete independently reviewed diagnostic proposal if existing evidence cannot resolve attribution. No new numerical permission is inferred from this failure. All original tests, tolerances, policies, source/candidate/stage/environment/CI/master remain unchanged; all raw and failed audit records are preserved.

## Work and memory

No production change was made. This attempt ran only the structural panel tests, not the planned stream factor/solve budget. Successful structural arithmetic/work assertions are scoped to this run; they do not establish the blocked BG lifecycle or whole-solver correctness. The zero-allocation requirement failed and no allocation reduction or speedup is accepted. No additional numerical attempt or diagnostic kernel work was used to explain it. Independent saved-result review and diagnostic publication follow separately; diagnostic acceptance cannot qualify RED.
'''
with (D/'REPORT.md').open('x') as f:f.write(report)
ledger=R/'.superpowers/sdd/2026-10-19-direct-bg-blocked-update/progress.md';before=ledger.read_text()
with (D/'progress.md.before-red2-run').open('x') as f:f.write(before)
after=before+'''\nTask2 RED2 attempted once after independent exact admission at b6c37d08. Repaired stage loaded; first panel unit11759pass/1P011allocation failure/0errors/0broken. Unexpected failure stops before lifecycle/stream units; six N026 failures NOT reached. Raw aggregate0/units0 reflect throw before count return, not zero tests; unit-1 authoritative. Juliaexit2/auditall_passedfalse/pure_timeoutfalse preserved, inclusive14.206s. Full274groups ANDsessions absent/noJulia; no timeout/guard failure/rerun/GREEN. Ruling: preserve failed qualification and allocation oracle; exact byte amount/origin unrecorded, no compiler/kernel attribution asserted. Only diagnostic closure allowed; no skill cleanup or suite rerun. Next source/log attribution is separate work, not automatic retry. Broader planopen/masterunchanged.\n'''
ledger.write_text(after)
with (D/'progress.md.after-red2-run').open('x') as f:f.write(after)
raw=D/'outer-console.log';b=raw.read_bytes();c.require(b.endswith(b'\n\n'),'Expected verbatim raw EOF')
c.save(D/'publication-policy.json',dict(raw=str(raw.relative_to(R)),sha256=c.sha(raw),allowed_warning=str(raw.relative_to(R))+':'+str(len(b.splitlines()))+': new blank line at EOF.\n',reason='Preserve exact captured exception log including terminal blank line; no authored whitespace exception'))
print('Saved result report and preserved continuation; numerical qualification remains false')
