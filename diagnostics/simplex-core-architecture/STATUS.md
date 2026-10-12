# Simplex core architecture: progress and continuation

Updated: 2026-10-12. This is the entry point after interruption.

## Current state

**S1-A, S3-A/S3-B, S4-A/S4-C and S5-C integrated; master `3c0af5c` (includes S6-C/S6-G/S6-M/S6-T/S6-W/S6-AA/S6-AC test repairs). S2-A rejected; S0-L all four long references audited and complete.**
The source baseline is `fe839aa72171d7496c9c931d9393278448c7317e`.
Initial time-budget diagnostic evidence is commit `6ded1fc`.

Active checkout:
`/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl`
Branch: `codex/simplex-core-architecture`, based on `7d6a8e1`.

Preserved planning checkout:
`/home/jspitz/.codex/worktrees/simplex-time-budget/JSimplex.jl`
Branch: `codex/simplex-time-budget` (unchanged).

- [Implementation roadmap](../../docs/superpowers/plans/2026-10-11-simplex-core-architecture.md)
- [Design and constraints](../../docs/superpowers/specs/2026-10-11-simplex-core-architecture-design.md)
- [Baseline measurements](../simplex-time-budget/README.md)
- [Detailed results](../simplex-time-budget/RESULTS.md)
- [Diagnostic review](../simplex-time-budget/REVIEW.md)

Do not assume master remains at the recorded baseline. Check actual refs and
preserve user changes before creating an implementation branch. At planning,
this checkout contains untracked Manifest.toml and LocalPreferences.toml;
main also has a user-modified .vscode/settings.json. Do not stage those files.

## Stage ledger

| ID | Deliverable | State | Evidence / next action |
| --- | --- | --- | --- |
| P0 | Design, roadmap, continuation record | Done | This documentation; production unchanged |
| S0 | Frozen baseline and coverage plan | Verified | Both counted and plain origins audited; old-baseline only, no current-master comparison |
| S1 | State ownership and validation reuse | Integrated | Inventory and local S1-A contract; master beb161b, report S1-ENTRY.md |
| S2 | Audited incremental primal maintenance | Active | S2-A REJECTED after numerical/cost qualification and independent review; broader pivot controller unresolved |
| S3 | End-to-end exact sparsity support | Active | S3-A/S3-B integrated, latest masterb720674; exact-support consumer savings qualified; broader S3 partial |
| S4 | Refactorization memory lifecycle | Active | S4-A/S4-C integrated; master3220118; Float64 component attribution/cost and exact triplet optimization accepted; bounded scalar component attribution360samples accepted; broader manager/history/medium coverage open |
| S5 | Phase/cleanup handoff contract | Active | S5-A/S5-B accepted; S5-C production88a2411 -> mastere7014fb, reviewed, master668/668; broader handoffs partial |
| S6 | Broad validation and final comparison | Active | S6-A/B triage accepted; S6-C test repair integrated as mastera465da5, focused20/20. S6-G artificial-row test repair master8516e0d; S6-M BigFloat fixture repair master7fea422, focused1477/1477; S6-T no-recession fixture masterafb37d9,focused192/master19; S6-W repeated-price fixture masterb9e7cb1,focused109/master41; S6-AA reliable exchange fixture master74f7835,focused127/master19; S6-AC reconstruction fixture master3c0af5c,focused339/master215; other CI families and full validation remain open |

Allowed execution states: Pending, Active, Blocked (reason required), Verified,
Integrated, Rejected (evidence required). Mark an optimization Verified only after
its acceptance gate. Record individual chunks separately when a stage is partial.

## Exact next action

S6-T accepted and integrated: evidence6574f9a,testfa8144d -> masterafb37d9.
Fresh independent gpt-6-astra review no findings. Structural RED2pass/4expected
failures with zero solves; GREEN192/192 (19affected+17+68+88neighbors),14gates614pins;
actual-master19/19,15gates614pins. Source/pins/user hashes verified. All original
postsolve assertions byte-identical; only no-recession testset constructor/bounds/
comment and six structural checks changed. No production/tolerance/precision/CI edit.
New feasible set preserves no-recession regression intent,not equivalent matrix or
solver repair. Old cancellation stress remains preserved. See S6-NEARLY-SINGULAR-
FIXTURE.md and S6-NEARLY-SINGULAR-FIXTURE-REVIEW.md. No fullsuite/x64/speedup claim.

S6-U accepted, evidence f9cb13b, fresh independent gpt-6-astra review: four original manager cases,
20/20 assertions, exit0,47gates615pins. One correction/publication then injected
price7=-1 is rejected without renewed budget; zero iterations/refactors. Selected
point/basis state unchanged. Initial cached-rho exact residual nonzero, published
rho exact. Not private fresh BTRAN capture or x64 cause. See S6-PRIMAL-PRICE-
REACHABILITY.md. No production/test changes, no accepted full-file rerun. One Important next-plan
gap fixed: mandatory count of fresh cost-RHS BTRAN detects a silently renewed
attempt even when exact residual suppresses correction events. See review report.

S6-V accepted, evidence d6630d5, fresh gpt-6-astra review no findings: qualification-1,124/124,12newidentity
iterations+4negativeboundarycalls,exit0,21gates616pins. Exact/seed/subject controls
show0/1/1freshcostBTRAN and0/0/1correctionBTRAN. Subject keeps all5oldassertions;
negative extra freshBTRAN leaves oldoracletrue but newbudgetoraclefalse, preserved.
No production/test changes; general wrapper lifecycle and x64 remain unqualified.
See S6-PRIMAL-PRICE-BOUNDARY.md. Do not rerun accepted S6-U/V.
S6-W accepted and integrated: test4c42fe3 -> masterb9e7cb1. Structural RED2expected
failures/zero solves,13gates617pins; GREEN109/109 (36target+68neighbor+5state),18gates;
actual-master41/41,19gates617pins. Fresh independent gpt-6-astra review no findings
or unnecessary production work/memory. Every cost BTRAN is counted after one-shot
consumption; all5originalassertions/callback/nativehelper/adjacenttestsets preserved.
No solver/tolerance/precision/CI change, no fullsuite/x64 or general lifecycle proof.
See S6-PRIMAL-PRICE-FIXTURE.md and REVIEW. U/V/W drivers/audits must not be rerun.
S6-X completed and independently accepted:12original exchanges,72/72originaloracle,
exit0,23gates618pins,77sharedsource/runtime/environment. Float32including0budget
accepts without correction,5FTRAN/4BTRAN/2countedrefactors;Float64corrects phase and
temporaryexport separately,7FTRAN/4BTRAN/2countedrefactors. Freshinitfactor is additional
setup.56events+48endpoints,owned snapshots only; no new solver/reference/corpus rerun.
Five relevanttest/sourcefiles byte-identical to failedCI. Historical printedFloat32
phase point row3residual256694483/2^51>tol;local192128033/2^51<tol.52offlinechecks
verify8CIvalues/bits/work; initialparserfailurepreserved. PrivateCIexportpoint absent;
actualrejectbranch/backendcause/observerneutrality/fullsuite/x64 not proved.
No production/test/CI change. Freshgpt6astra nofindings/no unnecessaryworkmemory.
See S6-PHASE-TRANSFER-REACHABILITY.md/REVIEW; acceptedXdrivers/audits NERERUN.
S6-Y completed and independently accepted: components-1,12/12 preservation checks,
exit0,23audit gates,623pins,517sharedpins;8supplementchecks. Exactly3quality and
3original-primal certificate calls, no workspace/factor/basis/public solve. Stored
CI phase point is basis-reliable but original-infeasible; local and exact known
points pass both. Exact row3 residuals256694483/2^51 versus192128033/2^51 straddle
Float32(1e-7). Budget3 versus printed0 only differs in max_refinements, unused by
these calls; no budget0 exchange replay. Actual privateCIcandidate/rejection branch
and backend cause remain unknown. Freshgpt6astra no findings/no unnecessary work
or memory; production/test/master/CI unchanged. See S6-PHASE-POINT-CERTIFICATES.md
and REVIEW. Accepted X/Y drivers/audits must not be rerun.
S6-Z qualified and independently accepted:qualification-1,4new Float32 manager
exchanges,29/29,exit0,23audit gates621pins517sharedpins,9supplementchecks. Identity6
basis and point exact; original4assertions preserved.5FTRAN/4BTRAN/2refactor kernels
per remove,additional fresh export factor setup;no correction events. Production/
test/CI unchanged. Review one scope wording issue corrected offline RED/GREEN:
old det31071 means same structural singleton, not different feasible set;equations,
activity coordinates/sparsity/cancellation differ. Original raw/preflight retained,
plan erratum appended; no numerical rerun. No unnecessary production work/memory.
See S6-RELIABLE-EXCHANGE.md/REVIEW; accepted X/Y/Z drivers/audits NERERUN.
S6-AA accepted and integrated: testf2e7647 -> master74f7835,pushed. Structural
RED2expectedfailures/zero exchanges,15gates621pins; GREEN127/127 (16target+108native
neighbor+3structural/global),17gates621pins; actual-master19/19,18gates621pins.
Source/GREEN identity, raw/portable/driver/user hashes verified. Freshgpt6astra no
findings/no unnecessary production work or memory. Only new identity6 helper and
zero-budget target call; original4assertions/nativehelper/allneighbors unchanged.
Same structural singleton; different equations/activities/cancellation. No production,
options,tolerance,precision or CI change. See S6-RELIABLE-EXCHANGE-FIXTURE.md/REVIEW.
S6-AB independently accepted:16newidentity exchanges,305/305,exit0,27audit gates
622pins517sharedsource/runtime/env,5raw/portable checks,32offline exact checks.
Phase-only declared2^-10coordinate3 after real primalFTRAN causes exactly1correction;
phase4FTRAN/2BTRAN/1update/1refactor/5invalidations/1primalRHS/1correctionRHS/1hit.
Whole remove6FTRAN/4BTRAN/2refactor kernels vs realcontrol5/4/2; freshsetup additional.
All seven original assertions and exact endpoint/certificates; realoriginal/export.
Successful calls only logged; no throwing-attempt proof,copyfailfast unsupported.
Freshgpt6astra accepts; reviewerMinor next-plan missing workoracle regradedImportant
and fixed offline RED3missing/GREEN3checks without numerical rerun. No deferredminor,
production/test/master/CI unchanged. See S6-PHASE-RECONSTRUCTION-BOUNDARY.md/REVIEW.
S6-AC accepted and integrated: test610c4bd -> master3c0af5c,pushed/remote verified.
Structural RED2expected failures/zero exchanges,15gates623pins; GREEN339/339,
20gates623pins; actualmaster215/215,20gates623pins,7supplement checks. Freshgpt6astra
no findings/no unnecessary work or memory. Seven original assertions/native helper/
all neighbors unchanged. Phase-only real-forward identity fixture and one-shot
2^-10 perturbation, pre-forward attempts including throw/afterconsumption; fullphase
4FTRAN2BTRAN/primal1/correction1/update1/refactor1/hit1/invalidation5 and whole6/4/2.
20driver-only accounting checks,zero backend numerical calls,not backendfailureproof.
No growing ledgers/snapshots/extra permanent exchanges. Original/export real;copy
explicit unsupported. Source/GREEN/rawportable/driver/user hashes verified.
See S6-PHASE-RECONSTRUCTION-FIXTURE.md/REVIEW. Production/options/tolerance/precision/
CI unchanged. X/Y/Z/AA/AB/AC accepteddrivers/auditors NERERUN against changed tests.
S6-AD complete as source/exact-offline diagnostic:27checks,7source/evidence/user/host
verification gates,zeroJulia/factor/workspace/solver/certificate calls. Current dual
test matches H;11source files match master. All216original assertions mapped, historical
48failures/run remain accounted. Candidate workspace SHARES factor, no factor copy;
ordinary refactors independent of retry budget, work survives discard. Identity,
below-cutoff and single-injection shortcuts rejected. New conditional4x4dyadicB
(delta2^-23,h2^-22) proof has accepted legacy row residual, eligible duplicate price-h,
exact column pivot0, corrected price0. Requires TWO unit-output declarations in public
and staged attempts; no adapter or runtime qualification yet. Freshgpt6astra accepts
conditional proof/no unnecessary production work/memory. Important H equality scope
fixed offline textual RED/GREEN: non-event compared fields only, events excluded.
Minor DEFERRED: work paragraph 'copy' means factor copy; existing vector copies are
explicitly mapped. See S6-DUAL-CAUSAL-CONTRACT.md/REVIEW,immutable results/S6-AD.
Next: docs/superpowers/plans/2026-10-12-dual-dyadic-component-qualification.md,S6-AE.
First new component-only qualification,Float64 fourmanagers x freshB/-I-refactorB,
8setups4refactors24basis solves +8native compensated-quality entries. No workspace,
publicsolve/dualiteration/adapter,metadata guessing or old accepted reruns. Read
source/interface/options/runtime/pins first, preserve all failures. Exact component
endpoints do not establish public retry/callback/ownership; separate later plan.
Production/test/master/CI unchanged. S6-J/S2-A rejected,actualCIcause/hidden states/
x64/fullsuite/broaderS6 open.


S6-S accepted evidence90811de/closure6c5ef37: fourtype13/13 + factor6/6; initial
comparability30/31false preserved with517pin/current-external supplement; no
retroactive launch pin. Factor19gates615pins/exactLU/primal/dual residuals0.
S6-R accepted08b7485/3baf29b:12/12/21gates613pins,componentdecomposition-1/16.
Do not rerun old N/O/P/Q/R/S/T/corpus/reference/cost drivers against changed tests.
Last fresh host runner407128/child407129/launchgroup407116 absent,noJulia,boot20de7dde-704e-41c8-bee7-b8511c0a86b0.
Verify new host state before edits or any new Julia. User environment/dirt preserved.

S6-Q remains accepted:11events,5/5,24gates611pins,exact S6-N endpoint. Refactor event
precedes FTRAN/BTRAN,certification precedes checks. Final scratch RHS[0,-1] is BTRAN;
primal RHS derives from slack states/bounds. Deferred Q auditor general columnscale
convention is reversed; all captured factors1 and independent correct convention
reproduces results. Preserve artifacts,do not reuse for nonunit scaling uncorrected.
No S6-R/S6-S minors. Current process checkpoint is recorded above; always verify
fresh identities before a new launch.

S6-N/O/P remain accepted diagnostics, not repairs. S6-O changes main presolve route;
S6-P candidate REJECTED with12pass/1equality failure,exit1,two false acceptance
gates/all_passed=false preserved. Do not repeat accepted census/corpus/cost runs.

S6-L/M remains complete: test2c3e0eb -> master7fea422 pushed, qualification300pass,
GREEN1477/1477/master1477/1477 and14master gates, independent review accepted.
No actual x64/full-suite success or end-to-end last-bit sensitivity claim.

S6-H census and S6-K exact tolerance-witness diagnostics remain accepted; do not
repeat them. S6-J permanent explicit-retry substitution remains REJECTED after
review: it still permits native numerical refactors and loses public recovery
coverage. Exact candidate and all local GREEN evidence are preserved; test restored.
Never promote it or weaken its original assertions/safeguards. Broader S2/S3/S4/S5/S6
remain open. CI stays disabled; no accepted reference/cost/corpus reruns.


S3-A production cd91a1a -> masterd8ad4ec5651225a512d5f533f48ce7d8fc8f90cc is reviewed,
integration-tested1645/1645 and pushed. Diagnostics milestone1c6ee5d is pushed.
Main user-file preservation checks passed. S0 counted dual long reference audit
passed; separate plain elapsed and primal-origin coverage remain pending.

S2-A private audited-flip subplan is closed as REJECTED; see S2-FLIPS.md.
Control1000, work RED/GREEN12, candidate960, safety139, dirty-entry26, focused10381
and cost128/64warmups are preserved. Independent review reproduced the cost data
and found no closure blocker. Dense accepted cases regress22–30%; no production
promotion or guessed density heuristic. Diagnostic5321ea1 records the result;
closure documentation is published. Master wasd8ad4ec at S2 closure; old environments preserved.

S3-B subplan docs/superpowers/plans/2026-10-11-pipeline-canonical-support.md is
complete. Productionb6a4064 -> masterb720674, master1611/1611, reviewed and pushed.
ReportS3-SUPPORT.md records1900paired work cases,936cost samples,80exact paired
trajectories,focused10645+9,all5precision contracts and two preserved Float32 cost
fixture failures. No unnecessary work/retention finding; no general speed claim.
Main user/environment hashes preserved; prior runner289833/child289858/driver
separately absent before the new S0 reference. Diagnostic evidence79df8f2 pushed.

S0-L medium-dual-plain-1 completed exit0 with unchanged pins, independently
recomputed inventory and matched513 shared source/environment/driver pins.
OPTIMAL, original primal feasible, exact objective/primal hash,255798iterations,
1612refactorizations match accepted counted dual reference. Plain elapsed
6006.247837068s includes0.020784797s compilation and531.464386642sGC;
408471253952allocated bytes/172692055events. This is one old-baseline sample,
not current-master speedup or a fresh phase-window trace. Full plain audit:
results/S0-L/medium-dual-plain-1-audit.json; all15checks true.
Runner290175/child290176/driver290166 absent in separate host calls before next
launch. Plain acceptance milestone914b59f is pushed.

S0-L medium-primal-counted-1 completed normally (exit0), with independently
reverified immutable pins and source/input hashes. All17 supplemental checks and
all counted-audit gates pass, read_errors empty.350 complete windows sum exactly
to all counters and353468 accepted iterations. Actual phase_two/primal263984steps,
9599.932126833s; phase_one/primal71062steps, cleanup/primal18422steps.
OPTIMAL, original primal feasible, internal certificate observed;
objective2.2389455645278454e7,2240refactorizations,
primalSHAeabfbba9bf2ce9d3f63f5b8cdf21e5831a332ef5f2d4faca7bda12e49ab21197.
Counted elapsed12916.673064291s includes0.0176922s compilation/719.815014698sGC;
548211597024allocatedB/175769276events; bounded recorder2874B.
VM peak4745708KiB, max sampled RSS4000368KiB, minimum available19030460KiB,
swap0. Audit and original report/windows are in results/S0-L/medium-primal-counted-1-*.
This is old-baseline chronology, not current-master performance. Primal and dual
origins have different trajectories/final primal hashes; compare the forthcoming
plain primal only with this counted primal for exact final-result acceptance.
Runner300579/child300580/driver300570 separately confirmed absent after exit.
Primal counted acceptance milestone6e793ec is pushed.

## S0-L complete: primal plain accepted (2026-10-12)

medium-primal-plain-1 completed with exit0 and independently verified unchanged
pins/source/input. All18 checks pass, including568 shared counted-primal pins.
Returned OPTIMAL and original primal feasible; objective2.2389455645278454e7,
primalSHAeabfbba9bf2ce9d3f63f5b8cdf21e5831a332ef5f2d4faca7bda12e49ab21197,
353468iterations and2240refactorizations exactly match counted primal, as do
source/input/options/policy. Plain elapsed13200.181889727s includes compile
0.023769598s andGC732.537595438s;548208082416allocatedB/175674777events.
Peak VM4601128KiB, max sampled RSS3856372KiB, minimum available19042772KiB,
swap0. Plain has no windows/counters and retains no recorder. Portable evidence:
results/S0-L/medium-primal-plain-1-{audit.json,process.json,reference.toml,run.log}.
The final process.json supersedes the launch-time placeholder in current.json.
Runner321988,child321989,driver321979 separately confirmed absent on the same boot.

All four planned old-baseline long references are now accepted. Counted origins
supply actual phase-II chronology; plain origins supply elapsed references. These
are single samples per mode/origin, not an instrumentation-overhead estimate or
current-master speedup. No full trajectory hash follows from final-state equality.
Existing failed/incomplete calibrations and raw attempts remain preserved.
Broader S2/S3/S4/S5/S6 and the historical test.mps failure remain unresolved.

S0-L completion milestoneb6d32ca is pushed. S4-B native component attribution is
accepted:72 warm samples,all13 audit gates,source/pins verified,exit0; residuals,
saved bases, changed pattern/dimension and failed-refactor preservation pass.
Independent review found no blocker/unnecessary production cost. See
S4-COMPONENTS.md and docs/superpowers/plans/2026-10-12-hh-component-attribution.md.
Failed native-components-1 (report dictionary type) remains preserved; corrected
native-components-2 passed. Runner354351/child354352/driver354342 separately absent.
Markowitz component attribution also passed:72 compile0 samples,all17 post-exit
checks, independent pins and fresh review without blocker. See S4-COMPONENTS.md
and docs/superpowers/plans/2026-10-12-hh-markowitz-attribution.md. Active-only pool
count scope is documented. Runner355464/child355465/driver355453 separately absent.
S4-C exact triplet allocation is integrated and pushed: production0f2c468 ->
master322011855af909d0d93b6f9bbecbe4200512fc67. RED/GREEN442,cost84compile0samples
with14audit checks,focused4366/4366,8exact paired trajectories/121assertions.
Fresh independent numerical/cost review approved without blockers/deferred minors.
Master integration1294/1294,all7audit gates,actual source/pins/user hashes verified.
See S4-TRIPLETS.md and2026-10-12-hh-markowitz-triplets.md. Extra O(k+c²) counting
is explicit; all7cost fixtures reduce bytes, mostly-zero256 side-median1.0258
is a timing limitation, not a speedup. No whole-solver speedup inferred.
Runner358060/child358061/driver358052 separately absent on boot
20de7dde-704e-41c8-bee7-b8511c0a86b0; no Julia at this milestone. Always recheck host.
S4-D scalar attribution completed360compile0samples/40cases/10lifecycles on
Float16/Float32/BigFloat256/RationalBigInt/RationalInt64, native and Markowitz.
All22qualified audit checks pass with independently verified pins/source. Initial
BigFloat Serialization hash gate rejected; raw initial audit preserved. Separate
8case canonical/mutation probe proves equal unchanged inputs, not retroactive
canonical hashes for original cost records. See S4-SCALARS.md and scalar subplan.
Fresh independent final review accepted without blockers; no production edits.
One deferred P3: initial audit write_text is not rerun-safe; do not rerun it on
accepted evidence. Committed raw/audit artifacts preserve the original result. Latest hash-probe
runner359346/child359347/driver359331 separately absent on the same boot; no Julia.
Next exact S5-A census plan: docs/superpowers/plans/2026-10-12-cleanup-entry-contract.md.
It selects ordinary original cleanup's discarded default reconstruction, preserving
observer/deadline/checkpoint/recovery contracts before any reuse implementation.
No medium/reference repeats. Native symbolic reuse remains unqualified.
Keep CI disabled as requested; previous failing full CI is not a passing S6 gate.
All original user/environment files and raw attempts are preserved.

## Evidence gaps and traps to retain

- The prefix/cleanup study alone does not cover long reduced-model phase II.
  S0-L now adds both counted origins; event snapshots still are not complete
  pricing-state checkpoints, and current-master full-medium comparison is pending.
- Fresh prefixes are HH/native320; historical cleanup is HH/native160. Both
  cleanup origins execute primal steps. Their origin labels are not algorithms.
- Existing measurements are mostly single paired timings and HH-only. They are
  not complete cross-manager or cross-solver performance comparisons.
- Sampling perturbed prefix timings substantially and cleanup sampling stalled.
  Preserve the failed attempt; use calibrated counters/plain runs for cleanup.
- Refactorization elapsed time includes substantial GC. Allocation event counts
  include presolve. Neither proves expensive ordinary update arithmetic.
- The user's test.mps HH/native320 dual certificate/recovery failure remains a
  separately reported case; these profiling slices do not establish its resolution.
- Existing paired-FTRAN experiments were inconclusive; do not repeat or promote
  them without a new hypothesis. Do not reintroduce removed adaptive heuristics
  into the numerical core while changing architecture.

## Resume checklist

1. Read this file, the plan, spec and latest stage report.
2. Inspect actual branch/ref/status and local instructions; preserve user dirt.
3. Inspect all numerical processes, runner state and logs. If one is active,
   do not start another or edit its pinned source/environment. A stale PID file
   is not proof of a live owned process; verify start identity and command.
4. Audit finished reports and process exit reasons. Missing reports, timeouts,
   resource kills and iteration limits are not successful solves.
5. Preserve interrupted attempts. Restore execution only after confirming process
   ownership, source/input digests and whether the runner safely supports resume.
6. Continue the first unchecked task. Record a changed hypothesis or order before
   spending another long run. Never repeat a completed experiment without reason.

## Per-chunk record (fill when execution starts)

- Stage/chunk ID and hypothesis:
- Status; current owner and checkout/branch:
- Last verified commit; current source/script/environment/input digests:
- Uncommitted files and purpose:
- Baseline/candidate commands and guarded output directories:
- Active runner identity or confirmed stopped state:
- Completed attempts; incomplete/failed attempts and reasons:
- Numerical evidence, work/allocation evidence and timing uncertainty:
- Review findings; commit, integration and push IDs if performed:
- Next exact action; blocker or rejected approach if any:

Keep portable summaries committed; retain large local logs and snapshots in
`.superpowers/simplex-core-architecture/`. Update this ledger before handoff and
after every verified/integrated chunk. Never store secrets in continuation notes.

## Initial execution milestone (2026-10-11)

- Owner: current architecture chat; active checkout above. Last source verified:
  `fe839aa`; documentation base `7d6a8e1`. Source and environment/input digests:
  `results/S0/preflight.json`.
- Host process audit: no Python/Julia numerical runner; all six old attempts
  have process reports. Four measurement attempts exit 0 with matching paired
  hashes; they end at ITERATION_LIMIT. The preserved sampling attempt exits 137.
- Milestone files: baseline, long-run method, ownership inventory, S1-A
  subplan, guard/tests/fixture definitions and compact preflight. Roadmap/STATUS
  record the accepted local deliverables. Local environment copies are untracked and excluded.
- Guard tests: initial 12 absent-runner failures then 12 passes; lifecycle and
  symlink regressions failed before their fixes; final suite 18/18 passed. Two
  independent review findings fixed, no deferred findings; see REVIEW.md. Raw logs live under
  `.superpowers/simplex-core-architecture/S0/`.
- No numerical command has been launched; no production merge performed.
  Milestone commit: `150aea5fea0a441160fd6338efa0de80c201d4a8`, pushed to
  `origin/codex/simplex-core-architecture` and verified with `git ls-remote`.
  Automatic approval initially distinguished diagnostic pushes from the standing
  production-fix authorization; the user then explicitly approved this branch
  push. The refusal is resolved. Master remains at `fe839aa`.
- Local baseline pins: `.superpowers/simplex-core-architecture/S0/expected-pins-v1.json`.
  Before S1-A launch, create new pins including its not-yet-written Julia scripts
  and every transitive dependency; this baseline set is not a complete future
  experiment manifest.
- Ruling: retain the plan's committed STATUS as authoritative and preserve all
  raw attempts instead of deleting execution scratch at finish — explicit user
  preservation requirements override generic skill cleanup. Cost: local disk use.
- Ruling: perform local S0 and S1 inventory before the long phase-II run, as the
  roadmap explicitly permits. S0 remains partial. Cost: no whole-medium evidence
  yet; prevents premature S2 performance claims.

### Local acceptance gate

S0-local and S1-inventory: Verified. Independent review found two diagnostic
runner defects; both have failing-before/passing-after regressions. Author ran
all 18 Python tests after fixes. Source hashes and absence of production diff
verified. S0-long and S1-production remain Pending within their Active stages.
No completed numerical experiment was repeated.

### Published continuation checkpoint

The initial local milestone is committed and pushed as `150aea5`. This small
follow-up records the confirmed remote identity and is pushed on the same branch.
The next task is the first unchecked S1-A characterization gate. No numerical
runner is active; do a fresh host process check before any Julia launch. Long
phase-II measurement remains pending; no prior measurements need repetition
until a new instrumentation or production-change hypothesis requires comparison.

## S1-A execution started

Preflight on 2026-10-11: HEAD 94442cf, master/origin at fe839aa; no numerical
process on host. Characterization completed. New contract tests and dedicated
work-count probe written before production changes. First guarded RED attempt
is about to run under `.superpowers/simplex-core-architecture/S1-A/red-1`.
No other Julia launch is allowed while this attempt owns the guard.

S1-A RED completed: process exit1, unchanged pins, 25 passes / 3 intended
work-count failures (9 vs 7 checks for two pivots). Candidate changes are limited
to dual_simplex.jl and three context-only deadline call sites in solver.jl; new
contract tests are included in runtests.jl. Candidate source patch/new files are
retained with green-1. The first normal-compilation focused attempt is still
running under its 600-second guard; inspect its process.json before any next
launch or pinned-source edit. No production commit/merge has occurred.

S1-A green-1 ended at the 600-second wall limit, exit -15, pins unchanged.
The termination stack identifies Julia type inference/backedge storage in
`simplex_precision_recovery_state_tests.jl:58`; no test-failure output. This is
incomplete evidence, not a passing suite or numerical failure. Host confirmed no
remaining Julia. Next: normal focused tests with per-file output, a separate
compile=min precision-recovery semantic run, then work counts and paired timing.
Static independent review found no production correctness or unnecessary-work
defect; four validation gaps are being closed. Raw attempts remain preserved.

S1-A validation checkpoint: green-2 was deliberately interrupted after about
280 seconds via its verified runner identity. Four completed normal-compilation
files passed 469 assertions (242 new contract, 71 weights, 125 residual, 31
certificate reuse). The remaining dual-entry file was compiling in LLVM at
line 85; guard cleanup ended with -9, pins unchanged. semantic-1 separately
passed precision-recovery-state (30) and dual-entry-phase (182) under compile=min,
exit0/pins unchanged. No timing claim is drawn from semantic mode.

count-1 passed all 41 assertions, exit0/pins unchanged. Two ordinary pivots use
7 instead of 9 finite checks: steepest-edge/Devex visit 112 instead of 144 vector
elements; Dantzig 84 instead of 108. Successful price repair retains its first
entry check; auto/existing-state/adaptive-policy exclusions retain check counts.
The counter sums lengths at each actually executed hardware-float scan, whose
loop visits every element; skipped arrays contribute zero.

paired-1 is now running baseline and candidate in independent modules in one
guarded Julia process, with identical sparse/dense fixtures and all five managers.
It compares full event/state fingerprints separately from three interleaved warm
plain timing/allocation pairs. Both source trees and all shared scripts are pinned.
Inspect its process.json before editing any pinned file or starting another job.

paired-1 deliberately stopped: author found a diagnostic comparator defect.
Baseline used ()->false rather than its real context clock closure. Earlier
state/hash matches are useful, but timings are rejected as production before/after
evidence. Process exited via owned guard cleanup (-9), pins unchanged; old scripts
are saved inside the attempt. The corrected helper uses each revision's actual
context-only stop factory and tests expiry equivalence before measurement.
Next runs: broad semantic boundaries, then corrected paired-2.

Boundaries-1 passed 780 assertions, exit0/pins unchanged. External-1 is active
under a 900-second guard, using the frozen five-case external manifest, both
algorithms, all five managers and native/Markowitz factorization. Its source and
measurement scripts are also copied into source-snapshot/ before later edits.
Measurement review accepted the corrected real-clock comparator but requests
trace/plain cross-checks and complete event-name/count/refactorization metadata
before paired-2. Production source has not changed since the focused tests.

External-1 completed normally: all 100 combinations OPTIMAL, original-primal
certified and reference-objective matched (305 assertions), pins unchanged.
Process group and runner confirmed absent on host before diagnostic edits.
The benchmark review fixes now compare trace/plain entry and final states,
steps/refactorizations and complete event names/counts scoped to the measured
kernel. Unused prototype scripts are retained under unused-prototypes/.

Baseline-precision-1 is active: original project/source at preserved 7d6a8e1,
normal compilation, only the unchanged precision-recovery-state file, 300-second
guard. This control determines whether the earlier compilation problem also
occurs without the candidate; no numerical benchmark is concurrent. Actual test
file and helper outside the baseline test tree are explicitly pinned. The local
launch helper is preserved as attempt-launcher.py for reproducibility.

Baseline-precision-1 ended at its 300-second wall limit, exit -15, pins unchanged.
The old production source also stalls in type inference (precision-recovery-state
line 31; candidate combined run had reached line 58). This reproduces an inability
to finish bounded normal compilation without the candidate; it does not establish
equal compile costs or a full-suite pass. No original checkout file was changed.
Paired-2 is active with the corrected deadline comparator and reviewed metadata
checks, 600-second guard. Both baseline/candidate source trees are pinned.

Paired-2 passed all 10 sparse/dense manager cases, 30 interleaved timing pairs
plus separate traces, exit0/pins unchanged. All entry/final/completion states,
event sequences/counts and step/refactorization counts match; trace/plain checks
also pass. Allocation bytes/counts equal, measured compilation zero. Tiny-case
timing scatter is reported without a universal speedup claim in S1-ENTRY.md.
Medium-dual-1 candidate prefix is active, 600-second guard, 4000 HH/native320
steps plus a separately warmed census with actual vector-element counting.
A new baseline run is justified by this new element metric and production change;
the old report only counted helper calls. No sampling/profiler run is repeated.

Medium-dual-1 completed, exit0/pins unchanged. The 4000-step HH/native320
candidate plain and census runs have identical hashes/events and zero measured
compilation. Candidate also exactly matches the historical baseline status,
iterations, event/state hashes, event counts and input hash. Finite-workspace
calls are 12004 versus historical 16004; actual candidate vector visits are
26287751664. This remains ITERATION_LIMIT, not a solved LP.
Medium-dual-baseline-1 is active on the preserved old source with the same new
element counter; this closes the missing baseline element metric. Runtime dual
paired validation and final acceptance/integration remain pending.

Medium-dual-baseline-1 completed exit0/pins unchanged; its long warm-up did not
hit the guard. Fresh baseline/candidate plaintext and census trajectories match.
Actual element visits: 35047415664 -> 26287751664, saved 8759664000 (24.994%).
Runtime-dual-baseline-1 is active (512-step prefix, old source, 600-second guard);
then run the candidate with identical input/scripts/options and compare hashes.
No production source edits since focused validation; no master integration yet.

Runtime-dual-baseline-1 completed exit0/pins unchanged. On resume the candidate
attempt had not started; runtime-dual-1 is now the sole guarded Julia process,
600-second limit. See its current.json and resources.jsonl. All 507 source/test
files still match seven accepted candidate-validation pin sets. Remote master
is fe839aa and diagnostic branch 94442cf. Final independent review accepts local
integration conditional on the runtime gate; no new blocking finding.

Runtime-dual-1 completed exit0/pins unchanged. Its four-way trajectory comparison
passed, with 62230448 fewer actual element visits; only finite-workspace calls
change (2055 -> 1796). Independent review and all S1-A local gates are complete.
All 507 source/test files match eight candidate validation pin sets. No Julia
process remains; source files can now be committed. Full normal-mode project
suite remains incomplete (old-source compilation timeout also reproduced).
Do not repeat numerical measurements without a new reason.

## S1-A integrated milestone

Architecture production commit 8e0a7c7; master cherry-pick beb161b, pushed. Only
two production files and three test files were integrated; diagnostics remain
on the architecture branch. Final staged whitespace check removed one trailing
blank line from the test helper after the main validation; production code did
not change. integration-1 passed all 242 new contract assertions directly from
master under compile=min, exit0/pins unchanged. No numerical process remains.

Portable results include 15 attempt records and source digests; full raw evidence
is preserved locally. 1807 accepted validation assertions plus 242 integration
assertions passed; no complete normal-mode suite or whole-medium solution claim.
Next: S0 long-run diagnostic subplan, implementation and calibrated short runs.

S0-L started after integrated S1-A: concrete subplan
docs/superpowers/plans/2026-10-11-simplex-long-instrumentation.md. First launcher
call failed before Julia because the new stage directory did not exist; corrected.
counts-red-1 then failed as intended on missing counter implementation, exit1,
pins unchanged. Count-only implementation/tests are uncommitted; normal guarded
counts-green-1 is next. No long solve or calibration acceptance yet.

S0-L counts-green-1 passed 39 assertions with normal compilation, exit0/pins
unchanged. Count-only pilot calibration is next: a new instrumentation test,
not another S1 baseline/candidate benchmark. Sparse/dense HH, five interleaved
pairs of 32 prepared kernels, separate trace verification. L2 chronology and
medium/both-algorithm calibration still pending. Production remains unchanged.

Active S0-L attempt: count-pilot-1, guarded 300 seconds on preserved baseline
7d6a8e1. Inspect process.json/current.json before edits or any Julia launch.
The count-only pilot does not qualify long-run instrumentation; L2 windows and
full calibration remain mandatory. Published diagnostic milestone is 1fcaa16;
master remote verified at beb161b. Current S0-L files are diagnostic-only.

## S0-L2 stopped checkpoint

window-pilot-1 completed exit0/pins unchanged. Sparse chronology overhead 11.90%
exceeds the 5% gate; dense 2.02%. Final state/step comparisons and zero measured
compilation checks passed, but these do not override the performance rejection.
All source/script pins verified again; runner and child absent, no Julia process.
Tests/results/failed attempts and the exact next hypothesis are recorded in
S0-LONG.md. No S0 production changes; no long reference. Stop follows the user's
explicit instruction to continue only until encountering a problem.

Resumed after explicit user request. Preflight: master/origin beb161b, architecture
4070155, user environments/dirt preserved, no Julia or guard process. New
event-ablation-1 isolates none/counts/noop/recorder in one baseline module, with
rotated order and identical operation counts/state. It asserts no cold regions
or periodic writes occur in the measured sparse batch. This tests event overhead
instead of repeating the failed whole-recorder pilot unchanged.

## Static work during the sole L3 process

S3-INVENTORY-NOTES.md maps current exact-support propagation, dense rebuilds,
manager fallback/invalidation and dense consumers. Partial map independently
reviewed; numerical counts and S3 subplan remain pending. S5-INVENTORY-NOTES.md
records phase/cleanup ownership and potential redundant initial reconstruction;
review accepted the partial map; full inventory still pending. Neither document changes pinned code.

S2 bounded proposal docs/superpowers/plans/2026-10-11-primal-flip-audit-prototype.md
has passed independent design review: unchanged-basis flips only, every candidate independently
point-certified, original reconstruction/fallback and mandatory endpoint refresh.
No incremental flags, default change or unsupported forward-error estimate. A1
context/hook/alias ownership and endpoint state table are resolved; freeze, branch
characterization and RED remain pending before implementation. S2 broader
pivot controller remains open. All numerical work waits behind the active L3 job.

S2-A design is independently accepted. New unexecuted control fixtures and
characterization driver cover80 planned cases (Float32/64,5managers,2backends,
4branch recipes). Static review confirms API/reset and scheduled-refactor setup;
its requested reason-specific assertion records exactly one limit refactor and
no other refactor reason, separated from final certification. The census is NOT
run or accepted, and no prototype implementation exists. Execute only after the
current S0 process exits and its host identity is confirmed absent.


S3 static writer review found two pending safety cases: accepted refinement into
an AbstractVector view does not invalidate the owned parent support by identity;
LP witness projection writes rho after refactor_other allows an observer to build
metadata for the fresh zero scratch. New diagnostic pipeline_boundary_regressions.jl
prepares whole-vector/no-metadata controls and view/observer cases. NO Julia run,
RED evidence or production fix yet. Prioritize this narrow reproduction at the
next free serial slot; do not interrupt or modify the active S0 reference.


Diagnostic e519fbe is pushed. Static review accepts the S3-A reproduction and
small subplan 2026-10-11-pipeline-boundary-invalidation.md; its first numerical
step remains RED on unchanged production after S0 releases the guard. The S3
writer map now explicitly qualifies view aliases and observer-created metadata.
S0 partial-attribution snapshot: iteration125952,90247 phase-II steps, no final
certificate. Pins matched at snapshot; raw prefix and compact report preserved.
Refactorization178.2594s includes157.4598s GC, so it is not an arithmetic timing.


Next-slot command is prepared but MUST NOT run before S0 release:
`python3 /tmp/jsimplex-s3-attempt.py boundary-red-1 <active>/diagnostics/simplex-core-architecture/reproduce/pipeline_boundary_regressions.jl smoke --seconds 600`.
The new helper targets S3-A, freezes src/test/environment/scripts and uses the
same existing guard/launcher. It was Python syntax-checked only. Check process.json,
then host runner/child/driver absence in a separate call before launching.
S5 inventory now records callback-visible initial reconstructed state, prior-work
assignment timing and constructor failure ownership; no S5 source change.


## Automatic continuation and live cleanup checkpoint

Diagnostic checkpointbb1bdd5 is pushed. The attached-thread heartbeat
`pokra-ov-n-v-voje-jsimplex` is ACTIVE, checking every5minutes to continue after the
sole numerical job releases its guard. It is instructed to remain quiet while
unchanged, audit final evidence first, then execute the reviewed S3-A RED and
subsequent plan autonomously. This scheduling is not another numerical process.
Respect any newer human stop/scope instruction; disable the heartbeat on completion
or when actual user intervention is necessary. Check app automation state rather
than assuming this local scheduling follows the repository to another host.

The live reference reached original-model cleanup at iteration234380. Completed
phase-II windows and their counters/sections are preserved in
results/S0-L/medium-dual-counted-1-phase-two-end.json with the raw prefix digest.
This remains running partial evidence, NOT an accepted final medium certificate.
Pins matched at capture. The same runner268789/Julia268790 remain active; do not
launch S3 or change pinned files until final report and separate host absence checks.


## Completed S0-L medium dual counted reference

medium-dual-counted-1 exited0, pins unchanged and independently reverified.
Post-exit long_audit JSON passes every gate: OPTIMAL, explicit original primal
feasibility, observed internal optimality certification,256 complete windows with
exact counter sums,198675 actual dual phase-II steps (3634.343694575s).
Total255798 steps includes21418 original-model primal cleanup steps.
Counted elapsed5926.881033309s includes0.022926199s compilation and503.750702521s
GC; this is not a compilation-free or authoritative plain timing comparison.
Objective2.2389455645278454e7; final primal digest and exact baseline source,
allowed medium hash, final reports and phase totals are preserved in
results/S0-L/medium-dual-counted-1-audit.json and companion raw report copies.
Separate plain elapsed and primal-origin references remain pending; no speedup
or whole-S0 completion is claimed. Guard/Julia/driver268789/268790/268787 were
confirmed absent in a separate host call after the final process report.
Next: execute the prepared S3-A boundary-red-1 before any production edit.

S3-A B1 confirmed both hypotheses: boundary-red-1 has27pass/5intended failures,
no errors; controls pass and corrected dense values/certification pass. Exit1,
pins unchanged; host runner/child/driver absent. Minimal invalidation changes
applied after RED; identical smoke GREEN next, no production commit yet.

S3-A identical smoke GREEN passed32/32,exit0/pins unchanged; runner280264/
Julia280265 and driver absent. Extended production regression covers250
precision/manager/backend/destination combinations, all six scratch aliases,
no-cache/rejected-write/model-alias contracts and witness callback provenance.
Extended matrix is prepared, not yet accepted.

S3-A boundary-matrix-1 passed1645/1645 with normal compilation; pins unchanged.
All5precisions/5managers/2backends supported in this fixture. Existing focused
pipeline/refinement/projection/guard regressions are now the sole numerical job
(boundary-focused-1). Production/test changes remain uncommitted pending gates.

S3-A focused-1 completed3214pass/0fail/3errors,exit1/pins unchanged. All three
errors are UndefVarError(lp_recovery_fixture) in lp_refinement_state_tests: the
diagnostic driver omitted its lp_refinement_recovery_tests dependency. Source
unchanged. Ruling: add the missing include and rerun only the LP recovery/state
group, retaining the3214 passed assertions; no repeat of the completed broad
solver matrix. Runner280590/child280591/driver absent before driver repair.
Cost driver additionally asserts actual cache/no-cache setup before timing.

LP recovery/state follow-up passed70/70,exit0/pins unchanged. Cost-1 failed
before producing a report: its measurement row inferred Dict{String,Real} and
could not accept later String labels. No accepted timing evidence from that
attempt. Fix only report container type to Dict{String,Any}; new cost-2 attempt
keeps the measurement workload unchanged. Exit1/pins unchanged, host process
absence confirmed before editing.


## Historical S0/S4 handoff snapshot (superseded)

S0-L2 current calibration gates pass for the actual L3 environment. Kernel10
passes sparse4.64385%/dense2.96326%; full suite3's five other gates pass, while
its medium-primal5.90404% remains explicitly FAIL. The reviewed process-isolated
follow-up completed all12 serial samples, ratio-of-medians0.24214%, compile0,
matching results/options/policy and exact counted window sums, retained2880B.
All process reports are exit0/pins unchanged. Host verified final runner266320,
child266321 and orchestrator264004 absent. Subsequent smoke passed and L3 is
now active as recorded below.
Read results/S0-L/isolated-primal-calibration-1.json and provenance/attempt records.
Independent L2 review accepts this deployment-matching calibration. The isolated
prefix driver returned empty primal_hash/objective=nothing, so matching result
metadata is not a new exact final-state hash check; full suite3's earlier separate
trace gates remain the state evidence. Smoke subsequently passed; long medium certification remains open.

S4-A is integrated and pushed: architecture8701a58 -> master4143dad27581cf1230fa74203306f956b89109a6.
RED6pass/2intended failures, GREEN344pass, normal focused4366pass, paired cost60
records, master integration344pass; all completed pins unchanged. Independent
review accepts the local memory fix, with no unnecessary work/retention finding.
See S4-SCRATCH.md. Same-size allocation cost unchanged; obsolete four-vector
capacity released after dimension changes. No timing speedup or whole-S4 claim.
Master remote identity verified; old worktrees, local environments and main user
files preserved. No S4 runner remains.

driver-smoke-1 passed: exit0/pins unchanged, OPTIMAL/original-primal feasible,
certificate observed,7 phase-II steps,5 complete windows and exact counter sums.
Its JSON chronology_reference_success=true. Host verified runner268482/child268483
absent. Calibration and smoke permit long launch, not a medium-success claim.

Current sole numerical job: S0-L/medium-dual-counted-1,43200-second guard,
counted dual medium, step cap1000000, old planning baseline. Runner268789
(start_ticks16921100), child268790 (start_ticks16921182), boot ID
20de7dde-704e-41c8-bee7-b8511c0a86b0; verify current host identity, not PID alone.
Pins digest a24597f2ddb774e72ade444c01c3f25f255b2c55b40ba4a1a47556f257f5fa7e.
Raw reference.toml/windows/current/resources/process are under the attempt path.
current.json reason=launch_error is the runner's pre-launch placeholder, not a
final outcome; inspect host identity/resources and final process.json.
Do not edit any pinned old src/test/env or active diagnostic Julia file, and do
not launch another numerical process while it runs. Read only completed windows;
no final status/certification is inferred before process exit and JSON audit.

Diagnostic checkpoint8f87306 is pushed. The current diagnostic checkpoint includes S4 inventory/subplan/results,
suite3 attribution and isolated-calibration evidence. Main user dirt and all
worktrees/environments remain intact. S2 static prerequisite mapping is reviewed;
the bounded flip design is accepted for private qualification; pivot controller and numerical work
remain pending. S4 broader attribution
is also pending; the integrated fix concerns four private solve/preparation vectors.

Long reference is now active. Its guarded baseline is the preserved
7d6a8e1 checkout (productionfe839aa), allowed medium hash, live1024-step windows,
1000000-step cap and external12h guard. Preserve every limit/failure as incomplete.
A separate plain elapsed run and primal-origin reference remain later serial work.
User explicitly requested continuous execution through diagnostic failures.

S1-A production commit `8e0a7c7def505604ccfe50cdbc2cf9cee453092d` was integrated
as master `beb161b310afd9dc7126eca98e3c15898a69efbf` and pushed. Its accepted behavior remains in the subsequent S4-A production
tree. Diagnostics/experiments are separate on the architecture
branch (published S1 evidence: 1fcaa16). All worktrees and local environments,
including main's modified .vscode/settings.json, remain preserved.
Read [S1-ENTRY.md](S1-ENTRY.md) for accepted local savings and coverage limitations.



## S3-A integrated milestone

Productioncd91a1a -> masterd8ad4ec; reviewed and pushed. Smoke32,extended1645,
focused3214 successful assertions plus missing-fixture errors closed by targeted
LP70, cost120, allocation-attribution28, master integration1645. All attempts and
failures preserved; no source change after first smoke GREEN. WholeVector body
unchanged, measured0B/0events; timing mixed, no speedup. Alias invalidation adds
bounded6metadata checks and necessary later support rebuilds. Generic view
benchmark boxing and nonspecialized single-call overhead explicitly documented.
No broader S3 completion or whole-medium improvement claim. Next S2-A census.


S2-A control-census-1 is active under the guard; runner282455 (start_ticks17692061), Julia282456 (start_ticks17692145), boot20de7dde-704e-41c8-bee7-b8511c0a86b0. Verify current identity. No S2 candidate exists.
A new unexecuted primal_flip_work_contracts.jl specifies the first intended RED:
four actual flips, certified final optimum, target5FTRAN/1BTRAN including mandatory
endpoint refresh versus the unchanged control expected8/4. Run only after census
acceptance and separate host absence; no private candidate before that RED.

S2-A control-census-1 completed1000/1000 assertions and80/80rows,exit0/pins
unchanged; source hashes verified. Host runner282455/child282456/driver absent.
Next work-red-1 on unchanged control; no candidate implementation yet.

S2-A work-red-1 produced the intended RED:6state/certificate checks pass,
2work assertions fail (actual8FTRAN/4BTRAN versus target5/1),0errors,exit1/pins
unchanged. Host runner282737/child282738/driver absent. Private AST-clone
implementation may now begin; production remains unchanged.

S2 work-green-1 failed at module loading (unspaced bang-symbol Pair syntax in
RENAMES evaluated an undefined target name), before numerical tests. Exit1/pins
unchanged, host absence verified. Replaced only the rename dictionary entries
with explicit Symbol constructors; work-green-2 next. Production unchanged.

S2 candidate-matrix-1 passed960/960 across80cases,exit0/pins unchanged.
Host runner283268/child283270/driver absent. Flip->pivot reduces4/3solves to3/2;
flip-chain8/4 to5/1; scheduled flip unchanged2/1; flip->unbounded increases3/1 to4/1
due required endpoint refresh and repeated direction. No timing saving claimed.
Two private context-dispatch hooks now allow tests to inject apply/certificate
failures without replacing any production helper. Default hook bodies call the
unchanged helpers. Next safety/unsupported/exception qualification.

S2 safety-contracts-2 passed139/139 (118 fault/publication +21 scope/precision),
exit0/pins unchanged; host runner283985/child283986/driver absent. Successful
rejection reconstruction, before-write overflow, time/iteration limits and owned
callback/numerical exception provenance passed. BigFloat and Rational Int64/BigInt
use the original8/4 path. Injected reconstruction exception is not coverage of
all ill-conditioned recovery failures. Next focused existing regressions.

S2 focused-1 passed10381/10381 across9existing primal-update/point/direction-price
files in normal compilation (783.6s test time), exit0/pins unchanged. Host
runner284158/child284159/driver absent. No repeat needed. Next dirty-entry-1
then cost-1; both prepared at diagnostic3b164ea.

Dirty-entry-1 passed21/failed1: the alleged infeasible slack=-1 was actually
within its one-sided (-Inf,5] row bounds, so a later certificate fallback repaired
it without the expected early-bound refresh. Correct the fixture to6 and assert
the actual guard fails before invocation. Both final optima and expired limits
passed; no prototype defect inferred. Exit1/pins unchanged, host285025/285026/
driver absent. Next dirty-entry-2; production unchanged.

Dirty-entry-2 passed26/26 with explicit failed guard preconditions, exit0/pins
unchanged. Both nonfinite and out-of-bound dirty points refresh successfully;
expired attempts return TIME_LIMIT without reconstruction or published primal.
Host285110/285111/driver absent. Sole next numerical job: cost-1.

S2 cost-1 completed128samples/64warmups, exit0/pins unchanged, all outcome hashes
match and plain compilation=0. Host285175/285176/driver absent. Sparse median
ratios0.472–0.753, dense1.219–1.302; reject-all1.105–2.202. Extra allocations
1040–4976B, retained point buffers968–4872B. Proposed broad eligible path is
rejected pending independent review; do not merge or add an unreviewed density
heuristic. See S2-FLIPS.md. No numerical process remains.

S2-A final independent review accepts REJECTED closure, with no critical/important
blocker and no hidden unnecessary copies or retained global workspace. Extra
certificate/fallback work and point-buffer memory are necessary for this design,
so the design is rejected instead of removing protections. Both minor report
wording/current-status corrections applied. Continue broad S3 inventory/census.

S3-B subplan prepared: docs/superpowers/plans/2026-10-11-pipeline-canonical-support.md.
New pipeline_support_census.jl instruments unchanged parsed method bodies in an
isolated process, counting output-consumer compaction separately from producer/
input work and dense rebuilds. Full census covers5types/5managers/2backends,
zero/one genuine pivot history,3input shapes,forcedsparse/dense,3operations and
external fallback. No production edit. Host has no numerical process before
launch; sole next job S3-B/support-census-1 via /tmp/jsimplex-s3b-attempt.py.
After census acceptance run its small red mode before proposed production edits.

S3-B support-census-1 passed20000/20000 assertions across1900cases, exit0/pins
unchanged, current source hashes verified. Output consumers executed992 extra
compactions visiting5156support entries;600empty cases contribute calls but no
entries. All source-type/backend/history modes and exact values/support passed.
Host runner286446/child286450/driver absent. Next support-red-1, unchanged source.

S3-B support-red-1:74pass/6intended failures,0errors. Sparse FTRAN/BTRAN/pricing
output consumers each compact once (1/1/3entries); dense/external controls pass.
Exit1/pins unchanged; host286814/286815/driver absent. Minimal production change
adds a local canonical flag after successful indexed/empty production only;
generic calls/dense rebuild/external checks unchanged. Permanent boundary tests
prepared/registered. Next identical small support-green-1 (driver red mode).

S3-B identical small GREEN passed80/80, exit0/pins unchanged, no output-consumer
compaction. Host286907/286908/driver absent. Next support-qualification-1 runs
new permanent tests then the extended1900case work matrix on the candidate.
Source/test remain uncommitted until acceptance.

S3-B qualification-1 passed1611permanent assertions plus20000work-matrix checks,
exit0/pins unchanged. All1900paired cases match modes/support/rebuilds; total
compaction reduction exactly992calls/5156entries. Source hashes match. Host
287028/287029/driver absent. Only runtests include indentation changed afterward.
Focused driver now includes sparse-pricing signed-zero/order tests, existing
full-solver pipeline matrix and explicit HH supplement. Next support-focused-1
under1800s guard, then prepared whole-pipeline cost comparison.

Static dependency check while support-focused-1 runs found that the added
sparse_pricing_edge_tests requires sparse_pricing_workspace from the omitted
sparse_pricing_integration_tests. Do not mutate the pinned driver. After final
report/absence, include that dependency for future driver use and run only the
affected alias/storage testset using prepared pipeline_support_pricing_followup.jl.
Do not repeat completed full-solver or broad factorization groups for this harness
issue. Confirm actual final error output before classifying the attempt.

S3-B focused-1 completed10645pass/0fail/1missing-fixture error. Targeted pricing
follow-up passed9/9,exit0/pins unchanged; runner288131/child288135/driver separately
absent. No broad repetition. Sole next run support-cost-1: three interleaved warm
pairs, fixed actual kernel modes, unchanged numerical arithmetic/control clone.

S3-B cost-1 failed before measurement: AST clone renamed the return-annotation
wrapper rather than the pricing function call signature. Exit1/pins unchanged;
host288220/288221/driver absent. Unwrap ::/where before renaming; source unchanged.
Preserve failed attempt; cost-2 executes the same planned workload.

Cost-2 ended exit1/pins unchanged after828samples/276warmups/23setups; the next
Float32/Markowitz PFI dense/history8 fixture returned a status before8pivots.
No claim of complete cost acceptance. Host288358/288359/driver separately absent.
Next targeted old/new fixture probe; preserve successful pairs and do not repeat
them. No tolerance or arithmetic change will be used to rescue this fixture.

Fixture probe confirms both old/new PFI/HH Float32 dense/history8 stop at the
third pivot with identical NUMERICAL_ERROR: primal point could not be certified.
Exit0/pins unchanged; host288739/288740/driver absent. Ruling: preserve this known
fixture limitation without weakening guards/tolerances; all5Float64 managers cover
dense/history8. Run remaining3 HH/Float32 fixtures only; timing coverage26/28.

S3-B cost completed936samples/312warmups/26fixtures (2known Float32 dense/history8
fixture failures excluded with old/new evidence). All156groups have exact paired
output hashes,compile0 and identical allocation bytes/events. Sparse group median
ratio0.9367, dense1.0020; broad pair noise prohibits universal elapsed claims.
Remaining attempt exit0/pins unchanged; host288828/288829/driver absent.
Next support-trajectory-1:80paired full solver state/event comparisons.

S3-B support-trajectory-1 passed1041assertions/80exact paired traces,exit0/pins
unchanged; host288952/288953/driver absent. Cost data/source/frozen baseline helper
hashes independently verified. Final review requested before production commit.

S3-B final independent review approves with explicit no-unnecessary-work/memory
finding. Cost/work/trajectory/source hashes independently reproduced; scope limits
accepted and no deferred minors. Productionb6a4064 -> masterb720674; preservation
hashes match. Sole guarded job support-master-1; do not push until acceptance.

S3-B integrated milestone: productionb6a4064 -> masterb720674, master1611/1611,
exit0/pins unchanged, separate host absence, authorized push and remote verification.
Independent reviewer accepts source/work/cost/trajectory proof with no findings.
All old worktrees/env/user dirt preserved. S0 final window allocation attribution
was aggregated without another Julia run; S4/S5 maps now cite completed evidence.

S0 plain reference launched after reviewed/pushed S3-B integration. Sole Julia
identity290176 verified with start_ticks/boot ID; guard290175 healthy, memory within
limits and no swap. This is only an active attempt, not accepted final evidence.


S0-L plain dual acceptance: exit0/pins independently reverified, all15audit gates
true; exact final result/configuration matches counted baseline. Separate host
absence verified before further Julia. Committed compact report copies preserve
elapsed/compile/GC/allocation/resource evidence; no repeated numerical measurement.

S0-L medium-primal-counted-1 launched with calibrated existing instrumentation,
unchanged old baseline and guard settings. Runner300579/Julia300580 identities
verified; session38999; no concurrent Julia. Await actual final audit before claims.

## S5-A cleanup entry census (2026-10-12)

Census-1 completed184 exact control/instrumented pairs, exit0, all20audit gates,
independent source/pins verified. See S5-ENTRY.md and cleanup-entry subplan.
Native initial1FTRAN/1BTRAN/1pricing/1basis-validation; checked same kernels plus
5validations/1checkpoint. Observer/deadline/caller exception contracts pass.
Unconditional omission rejected; no production change or speedup claim.
Two diagnostic world-age warnings retained; future Julia/Revise portability open.
Runner361287/child361288/driver361278 separately absent, same boot20de7dde-704e-41c8-bee7-b8511c0a86b0.
Fresh gpt-6-astra review accepted, no blockers. Deferred minor: exact means recorded
representation/fields, not bitwise full workspace; BigFloat signed zero is canonicalized.
See S5-ENTRY-REVIEW.md. Evidence43dfa89; closure push follows.
Next concrete plan:2026-10-12-objective-restoration-contract.md.
Broader S4/S5/S6 remain open; CI stays disabled.

## S5-B objective/bound restoration census (2026-10-12)

Census-2 completed144selected-representation pairs/all21audit gates, exit0, source
and whole pins independently verified. Report S5-RESTORATION.md; independent review accepted with alias-proof plan correction.
Census-1 overconstrained alien-bound oracle failed; probe-1 showed valid original
optima. Both attempts preserved. Corrected existing working-infeasibility fixture
rejects alien proof. Current result80OPTIMAL/32TIME_LIMIT/16NUMERICAL_ERROR/16throws.
Identity-aliased cost copies are a candidate only with a nonoverlapping-source
guard; bound deduplication excluded due intervening writes/source aliases.
Next exact RED/GREEN plan:2026-10-12-restore-alias-copies.md, after final census review.
Production unchanged/master3220118; no speedup claim. Runner363940/child363945/
driver363931 separately absent on boot20de7dde-704e-41c8-bee7-b8511c0a86b0.
CI disabled, historical failures and broader S4/S5/S6 remain open.

S5-B final review closed: evidenceef9749d, no production changes. One important
next-plan correction: Base.mightalias alone misses offset unsafe_wrap overlaps.
Alias-probe-1 proves4counterexamples; diagnostic range predicate passes10Float64
cases,12audit checks/586independent pins. It is not all-scalar production proof.
S5-RESTORATION-REVIEW.md records accepted scope and all declined-review rulings.
Next exact action:2026-10-12-restore-alias-copies.md; establish storage-layout/range
contract then focused work RED, preserving every overlap/failure/event safeguard.
Keep both copies when disjointness cannot be established. Bound copies excluded.
Last runner364759/child364760/driver364750 separately absent; no Julia, same boot.
S5-C implementation/cost/regression/review gates and broader S4/S5/S6 remain open.

## S5-C qualification in progress (2026-10-12)

Minimal cost-copy guard implemented on architecture branch, not integrated.
Layout184, RED462semantic/12expectedworkfailures, GREEN504, focused1463,
cost312compile0samples/52fixtures,152exact trajectory pairs/153assertions.
All process/source/pin gates verified. Report S5-COPIES.md; final review pending.
Cost events equal; bytes differ144/156pairs, initial analysis assumption rejected
and preserved. Large eligible timing ratios0.4496–0.9354; small and detached
spread explicitly documented, no universal speedup/no-byte-growth claim.
Last runner367367/child367368/driver367359 separately absent, no Julia, same boot.
Master remains3220118. Next final independent numerical/work/memory review.

## S5-C accepted and integrated (2026-10-12)

Fresh independent gpt-6-astra review accepts with no findings; no unnecessary
scan/solve/allocation/cache/retention found. Production88a2411 -> mastere7014fb.
Master-1 passes668/668,all12audit gates/592pins, actual source and user hashes.
Separate host check: runner368680/child368681/driver368668 absent, no Julia,
boot20de7dde-704e-41c8-bee7-b8511c0a86b0. Source benefit is one O(N) copy removed
at eligible cold restoration; cost-byte differences and detached/small timing
uncertainty remain explicit. See S5-COPIES.md and S5-COPIES-REVIEW.md.
Next S6-A failure/coverage inventory uses existing logs, without rerunning accepted
measurements. Ruling: triage historical CI now before more optimization so broader
validation blockers are explicit; this is not closure of broader S2/S3/S4/S5.
CI confirmed disabled_manually; two old runs cancelled. Extended validation is a
separate active workflow, not launched here. Master push verified by ls-remote:e7014fb92ae6dce633afc714793a2f89b39aea76.

## S6-A/B inventory and first failure cause (2026-10-12)

S5-C diagnosticsbb074ac and mastere7014fb are pushed/remote verified. Historical
CI inventory:source4914cbb197failures+1error,sourceb720674200+1;tests/src identical
between these refs, both Julia1.13.1x64. All failures accounted,5audit checks.
S6-B original preference oracle reproduced2pass/2fail/1error on currentmain1.13.0
AArch64,10audit gates. Observations show valid tolerated flip bypasses intended
refresh path. Harness1/2failures and3oracleASTfailure are explicitly preserved;
only3twins and separate cleanoracle-1 qualify. See S6-FAILURES.md.
S6-C synthetic bound1e8 probe5/5,12gates/exact twins, one refactor/no flip proves
intended path. Test-only correction being checked; no production solver change.
Focused-1 precondition placement error preserved; focused-2 is current attempt.
Final review/integration pending; never claim full CI/S6 complete.

## S6-A/B/C accepted and integrated (2026-10-12)

Fresh independent gpt-6-astra review accepts inventory/reproduction/test correction
with no findings and no unnecessary production work/memory. Test3e91736 integrated
as mastera465da5, pushed/remote verified. Focused master-1 20/20,exit0,11audit gates,
independent pins/source and user hashes. Separate host runner371705/child371706/
driver371697 absent,noJulia,boot20de7dde-704e-41c8-bee7-b8511c0a86b0.
Reports S6-FAILURES.md,S6-FIXTURE.md,S6-FIXTURE-REVIEW.md retain every failed harness
attempt and limited scope. Two trailing spaces in a raw failed log are preserved.
Next bounded S6-D artificial-row recovery reachability subplan; historical96CI
assertions are not yet diagnosed. Full CI/S6 and broader S2/S3/S4/S5 remain open.

## S6-D/E diagnostic closure (2026-10-12)

Current census28pairs/168pass/13gates; private exact-row counterfactual28pairs/
72pass96expectedfail/17gates. Same failed CI predicates and76nonstate evaluated
values; full-state comparison rejected/preserved (original column1 vs CI7).
Both failed parser attempts preserved. Fresh independent review accepts, two minor
publication clarifications applied without code/rerun. No production/test changes.
Last runner373223/child373224/driver373214 separately absent,noJulia,sameboot.
Next S6-F controlled test adapter qualification; all current results localAArch64,
actualCIbackend/row cause unresolved. Never relax safeguards to force a test outcome.

## S6-F/G controlled fixture accepted (2026-10-12)

Qualified one-shot declared unreliable row through a test-only forwarding phase
factor. All original assertions preserved, neighboring testsets unchanged. No
production/tolerance/workflow edit. Fresh independent review finds no numerical,
dispatch, ownership or unnecessary production work/memory issue. Qualification
564pass/14gates, RED196pass56intendedfail/7gates, GREEN348pass/12gates600pins,
master348pass/13gates. Testa9be911 -> master8516e0d. Source/pins/user hashes checked;
separate process absence recorded above. Accepted local denseFloat64native scope
and actualx64/downstream arithmetic limitations remain explicit in report.
Next S6-H census uses unchanged duplicate-column dual fixture before any fix.
