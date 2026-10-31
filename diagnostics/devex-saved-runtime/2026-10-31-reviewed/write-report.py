from pathlib import Path
import json,hashlib,shutil,statistics
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');D=W/'diagnostics/devex-saved-runtime/2026-10-31-reviewed';v=json.loads((D/'analysis.json').read_text())
for name in ('devex-saved-runtime-reviewed-numerical-admission.md','devex-saved-runtime-reviewed-numerical-admission.json'):
 shutil.copyfile(Path('/tmp')/name,D/name)
rows=[]
for x in v['cases']:
 rows.append(f"| {x['id']} | {x['old_KLU_failed_handler_median_ms']:.3f} | {x['current_UMFPACK_strict_handler_median_ms']:.3f} | {x['strict_constructor_median_ms']:.3f} | {x['devex_constructor_median_ms']:.3f} | {x['paired_ratio_median']:.3f} ({x['paired_ratio_range'][0]:.3f}–{x['paired_ratio_range'][1]:.3f}) |")
text='''# Production Devex recovery on the original saved runtime bases

**Accepted component verification: all six original runtime bases now complete private recovery and actual Devex publication; strict weight handling and strict recovery continue to refuse them. Ordinary Test654/654, exit0.** One new process completed in15.382276621seconds inclusive. No numerical retry, production edit or complete LP solve. Current master9940bdabe149e922afa60b5364227a7e7393bc75 contains the integrated Devex change d48f0865 and the later post-primal cleanup corrections. Those cleanup paths are not exercised by this component case.

## What is and is not the original case

The user identified diagnostics/klu-weight-btran/2026-10-29/REPORT.md. Its complete experiment remains **NOT ACCEPTED**,13816pass/217fail. Its six runtime bases came from the exact two existing exchange tapes; all six B0/B80/B160 matrix hashes match that stored run. Captured A and basis indices are unchanged, including negative-identity artificial columns. The original zero-cost, unbounded-unused-bound algebra holder is recreated exactly. This is not the original full LP, and does not contain its complete costs/bounds/point.

The prior parent capture stopped deliberately at ITERATION_LIMIT45000; the later failed KLU benchmark did not run any simplex iteration. Therefore the requested iteration comparison is **0 before /0 now**. No full-solve OPTIMAL result, iteration reduction or end-to-end runtime benefit follows. A complete LP comparison would be a different experiment.

The stored experiment used native KLU/full exported/local graph factors. This verification uses the **actual current production native PFI/UMFPACK factorization**, without new wrappers, factor dispatch changes or KLU promotion. The separate earlier weight-rejection diagnosis already established the same first-row reliability refusal for UMFPACK on runtime30000/B0; this new run establishes it on all six bases. Comparisons against stored KLU times are contextual only. It would be incorrect to describe the new accepted route as a repaired/accepted KLU steepest-edge benchmark.

## Actual result and preserved safeguards

Each current strict compatibility consumer returnsfalse. Both the strict private constructor (algorithm unspecified) and explicit-dual constructor build genuine independent production factors, recompute the same zero-RHS core and apply the unchanged finite/basis/primal/basic-price/weight residual checks. Strict construction returnsnothing; explicit dual construction returns a private fallback result, failed_weight_row1, reason finite_inconclusive, cause not_improved. No failed steepest-edge weight is accepted. The live basis/factor/primal remain unchanged until explicit publication. The last measured private trial is published once per case; its actual factor is adopted, weight mode isDevex, reference membership is exactly the basis and all reset weights are1. Exactly one commit-only pricing_weight_rejected and pricing_devex event and one repair event are present. Core quality passes before and after publication; input A/B hashes, basis/states and working costs/bounds remain unchanged. All iterations remain0.

Solve tolerance2^-44, max_refinements3, native legacy policy and original numerical checks remain. No zero snapping, dropped coefficients, precision increase, safeguard removal or production method overwrite. No custom Test recorder/manual stack. This verifies the real production constructor/classification/publication on these captured matrices; it does not execute the full dual retry loop or subsequent pivots on a real saved LP. Their prior permanent tests remain separate evidence.

## Time comparison

Two warm and five measured rounds per case, alternating arm order. Every measured whole-constructor compile/recompile value is0; all measured GC values are retained. Setup and explicit GC are outside timed windows. Per-column numbers are side medians; ratio is the median of same-round ratios, not the quotient of those side medians. Five short pairs in one process do not establish a universal cost ratio.

| Saved basis | Stored KLU failed handler ms | Current UMFPACK failed handler ms | Current strict constructor ms | Current Devex constructor ms | Paired Devex/strict median (range) |
|---|---:|---:|---:|---:|---:|
'''+ '\n'.join(rows)+'''

The first two columns time a weight handler ending after the first failed row; the last two include genuine factor construction, owned trial preparation, recompute/core checks and the weight attempt. They are different workloads. The old sampled128requested unit fields were not128successful weights and are not used as a denominator. New Devex construction pays additional mandatory core revalidation and reset, hence it is ordinarily more expensive than merely returning failure. Its paired medians are7.9–19.9% above the strict constructor, with three ranges crossing1. This is a capability/correctness result, not a speedup. Single post-window publication costs0.353–0.427ms here; it is not part of the repeated constructor times.

## Work, allocations and memory

Exactly84 constructor calls (42strict/42dual),12 initial workspace factor constructions and six separate publications were planned and executed through the bound driver. Per-arm refactorization-charge tests require7/case. These are source/call-site accounting, not complete instrumented native internal work counts. Each case also makes7strict compatibility handler calls and one classification probe. All fail on row1; no later weight row is attempted. No LP solve or pivot is called. The saved original failure likewise stopped on its first row, so avoided later DSE rows cannot be counted as measured speedup.

Strict constructor medians allocate38.86–42.93MB aggregate traffic/257–258events, Devex40.91–44.98MB/285–286events. The increase is2,045,720–2,051,976bytes and28events per call; the mandatory post-failed-weight core revalidation constructs RHS and SolveQualityScratch and gathers basis values/costs, plus reset bookkeeping. No new production implementation was added in this task. This required cold recovery work is not an unnecessary new per-iteration cost. These are allocation traffic counters, potentially including native callbacks, not live/peak native memory. There is no full native allocation/free ledger or retention proof.

Diagnostic setup owns two initial factors/workspaces, current B and checkpoints; at most the last accepted private trial remains rooted between pairs. Per-case verification/hash/quality scans, fixed scalar cost records and explicit48GC calls are outside constructor windows and do contribute to process time/memory. No per-iteration snapshots or growing solver ledger are introduced. Peak child RSS756024KiB includes runtime/JIT/diagnostics/factors; it is not a factor-only graph measure. Fifteen samples: minavailable21963500KiB, swap0. Full748historical/current groups AND sessions are absent after exit; no Julia remains. All111launch pins and master/user-state checks passed.

## Admission and preservation

Initial source-only admission caught a numeric-valued Dict into which the driver would insert String metadata. It was rejected before Julia; initial2026-10-31 driver,107pins/seal/review remain unchanged. Separately sealed reviewed driver differs by exactly one explicit Dict{String,Any} storage annotation; numerical calls/assertions/order are unchanged. GC accounting was clarified to48total. Accepted fresh admission binds111pins+seal+pins+report. No failed numerical attempt preceded the accepted run.

Canonical new auditor accepted all checks; separate postexit closure verifies the full groups/sessions and current refs. Raw run-1 is immutable. Initial preflight744groups omitted the previous launcher; the preserved correction adds its immutable identity and both fresh prelaunch checks cover745, with748after the new process. No old launcher/accepted check/auditor/benchmark was rerun or rewritten. Master, production/permanent tests/environment/CI/user files remain unchanged. CI remains disabled. Broader solver/full-suite/performance obligations remain open.

Independent result review is recorded separately; this report was written before that review. Any later publication record is separate, not a retroactive launch pin.
'''
(D/'REPORT.md').write_text(text)
shutil.copyfile(__file__,D/'write-report.py')
print('report written from stored raw and analysis; no Julia rerun')
