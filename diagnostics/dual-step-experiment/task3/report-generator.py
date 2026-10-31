from pathlib import Path
import json,hashlib,shutil
W=Path('/home/jspitz/.codex/worktrees/dual-step-experiment/JSimplex.jl');D=W/'diagnostics/dual-step-experiment/task3'
def sha(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
q=json.loads((D/'postcheck.json').read_text());g=q['runs']['green'];total=g['assertions'];prior=sum(v for n,v in g['testsets'].items() if n.startswith(('Task1 ','Task2 ')))
readme=W/'diagnostics/dual-step-experiment/README.md';shutil.copyfile(readme,D/'README.md.before-completion')
(D/'completion-before-map.json').write_text(json.dumps({str(readme):{'sha256':sha(readme),'preserved':str(D/'README.md.before-completion'),'scope':'Task3 pending continuation before completion; Task2 original README binding remains incontinuation-map.json'}},indent=2)+'\n')
s=readme.read_text();start=s.index('- Status:');end=s.index('\n',start)
s=s[:start]+f'- Status: Task1/2 qualified; Task3 Harris/BFRT proposals and planned writes qualified{total}/{total} including{prior} unchanged Task1/2 regressions. [Task3 report](task3/REPORT.md), [work/ownership ledger](task3/WORK-MEMORY.md). No commit/controller or speedup claim yet; Tasks4–6 remain open.'+s[end:];readme.write_text(s)
rows='\n'.join(f'| {n} | {v} |' for n,v in g['testsets'].items())
runs='\n'.join(f"| {name} | {v['elapsed_seconds']:.9f} | {v['samples']} | {v['min_available_kib']} | {v['max_swap_kib']} | {v['child_maxrss_kib']} |" for name,v in q['runs'].items())
(D/'REPORT.md').write_text(f'''# Task3 qualified pending dual proposals

Task3 of the approved experimental dual-engine plan is implemented and component-qualified on codex/dual-step-experiment fromb2d74da078d5e8361fccaa4fc74e9f6abb750548. Master9940bdabe149e922afa60b5364227a7e7393bc75 and production src/test/environment/CI are unchanged. No public/default solver route, factor-update/numeric commit or recovery controller. Tasks4–6 remain open. PENDING.md and earlier admissions are historical checkpoints, superseded by this report and final evidence.

## Behavior

choose_leaving uses the exact maintained infeasible-basic set and robust current Devex scores with deterministic row-ID ties. Rejected rows expire on every committed generation change, including wrap/rebuild collisions. At most8 rejected rows route to recovery; an exhausted selection is not a certificate.

Harris/BFRT candidates use complete nonzero tableau support, unchanged user feasibility/zero tolerances and base pivot cutoff. Candidate validation inspects every potentially changed price and pending mandatory/optional flip, bounded by8 mathematical validations. Preexisting dual_bad membership blocks entry even outside future tableau support. Sign-eligible tiny pivots, nonfinite arithmetic, underflowed capacity and uncertain exhaustion remain conservative outcomes.

Entering FTRAN, original complete row residual, complete direction residual/absolute scales and _pivot_agrees are checked before planning. Flips remain pending; a nonempty set forms one aggregate RHS and at most one additional BFRT FTRAN with its independent residual check. Nonzero raw flip products that underflow to zero are rejected before BFRT. No coefficient cutoff or precision/tolerance relaxation is added.

The proposal plans changed primal values, reduced prices, entering cost shifts, Devex weights and entering/leaving/flip states into preallocated owned arrays with field masks and a unique affected union. Exactly unchanged values are omitted after validation. Complete Devex reference terms and direction-support weight updates retain positivity/finiteness. No committed numeric vector, basis/state map, invariant summary or mathematical factor base/update chain is published. Native solve work/cache necessarily changes and is counted; no whole-factor-graph immutability or rollback is claimed.

Proposal validity is generation/owner/factor/RHS/output/ticket-bound. Explicit rejection expires its stage; a completed-stage query additionally requires valid=true. A kernel call cannot revive an invalidated completed proposal through still-matching unrelated receipts. Failed validation/planning expires its stage; repeated queries do not repeat hidden solves or partial writes. Shared scalar deadline checks remain in place; no user callbacks execute inside E.

## Observed tests

Three independently admitted RED processes were executed once each: initial missing interfaces4fail/0errors/exit1; raw flip underflow1fail/0errors/exit1; lifetime regression3setupPass+4fail/0errors/exit1. Their exact source/pins/reviews/raw logs remain preserved through strict before maps. Earlier193/242/249GREEN reviews never launched. No frozen Task1/2 script or old numerical audit was rerun.

Final independently admitted GREEN: **{total}/{total} ordinary Test assertions**, exit0, including{prior} unchanged Task1/2 assertions and{total-prior} Task3 assertions. Counts are observed from ordinary summaries, not a custom recorder. The whole component suite covers genuine and degenerate pivots; ties; free/fixed/upper/boxed states; mandatory/optional/multirow flips; BFRT-only and canceled rows; absent/tiny/underflowed candidates; actual8candidate/rejected-row exhaustion; outside-support invalid prices; pending cost/weight/state changes; proposal invalidation, generation/stamp wrap, stopped calls, physical capacities and unchanged source/committed snapshots. Sparse/banded/dense n8/n64 cases compare full-row reference decisions and full simulated-application equations. A tiny general2x2 basis includes nonzero old multipliers reconstructed exactly;64row slack multipliers use closed form, not dense rational factorization. Four cold native probes validate the live factor against committed B independently of reference aliases.

| Ordinary testset | Pass |
|---|---:|
{rows}

New postexit auditor: {len(q['checks'])} checks accepted, including all actual290GREEN pins, exact prior-source mappings, original failure preservation, actual commands/admissions, resource bounds and current production-source equality. Postexit scripts/reviews are separately bound evidence, not retroactive launch pins. Independent source/numerical admission and result review are stored in GREEN-REVIEW.md/RESULT-REVIEW.md and their exact JSON bindings.

| Run | Inclusive seconds | Resource samples | Min available KiB | Max swap KiB | Child maxRSS KiB |
|---|---:|---:|---:|---:|---:|
{runs}

These inclusive times contain process startup, loading, compilation, fixture setup and cold oracles; they are not kernel benchmarks. Final fresh host closure checks every actual known process group ANDsession and noJulia; exact group count is recorded in postcheck-host.json/closure-host.json. No native peak/live/free accounting or observer-neutrality proof is claimed.

## Review corrections and work budget

Initial review caught raw flip-product underflow and incomplete general-basis/multirow/factor coverage. The separately observed underflow RED preceded its source fix. Final coverage also exercises unsuccessful coefficient visits, all8 candidate validations, generation-wrap exclusion expiry and the completed-stage lifetime defect; its separate observed RED preceded the scalar proof/stage correction. Review-service builder failures interrupted this work; after service recovery a fresh independent reviewer admitted the exact261pin lifetime RED, then reviewed the new290pin full GREEN. No prior accepted-but-superseded approval was reused.

Nominal newly retained payload versusTask2 is **50N+28m bytes** on64bit, plus headers/scalars/allocator slack:18N proposal metadata (current UInt8 state),32N newly materialized J scratch capacity,12m RHS support metadata and16m rejected-row sets. Existing32N planned value payload,8N candidate capacity and8m row_rhs payload are reused. Physical buffers are never shortened per proposal; no old/new numeric workspace/factor copy or growing trace is added. Setup overlap/cold resizing is explicit, not a hot-path claim.

Ordinary successful no-flip proposal:1BTRAN+1FTRAN; flips require1BTRAN+2FTRAN. Each native dense result still has a complete finite/support capture and each RHS is copied/checked. The original full row residual is retained. Direction/BFRT residuals check the complete visited-row union/scales. Leaving selection scans at mostm infeasible entries; ratio validation visits support s at most8times, with explicit in-place breakpoint/group/optional sorting. Planning enumerates direction/BFRT/flip/price support and writes each changed field once. No per-candidate fullN scan or repeated row index construction. The flip_rhs_terms counter includes entering-column and rejected BFRT coefficient attempts, not just successful flips. Extra factor probes/exact oracles are cold test work only. Task1's deferred redundant cold inverse-zeroing pass remains unchanged.

No speedup, lower-allocation, native-retention or end-to-end solver improvement is established here. The review checks numerical correctness and identifies the actual work/storage budget for later integrated measurement. Required receipts/captures/sorting/residual checks remain explicit costs; no unnecessary new scans, allocations or growing retained storage were found within the qualified private proposal path. Final result review records its precise evidence and limitations.

## Continuation

Old Task1/2 evidence remains frozen. Task2 source bindings resolve only through task2-before-map.json to its qualified copies; its original README closure binding maps through continuation-map.json/README.md.before-Task3. The pending Task3 README bytes are separately preserved in completion-before-map.json. All other old mappings remain unchanged. qualified-sources.json binds this exact component-qualified source/test set. Task3 closes by exact local commit only; no master merge/push or Task4 execution is included.
''')
Q=D/'qualified-source';Q.mkdir();mp={}
for p in sorted((W/'experimental/dual_engine').rglob('*.jl')):
 q=Q/p.relative_to(W/'experimental/dual_engine');q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q);mp[str(p)]={'sha256':sha(p),'preserved':str(q)}
(D/'qualified-sources.json').write_text(json.dumps(mp,indent=2)+'\n');print(json.dumps(dict(assertions=total,task3=total-prior,sources=len(mp))))
