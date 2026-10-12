from pathlib import Path
import hashlib,json,subprocess
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');D=R/'diagnostics/simplex-core-architecture';E=D/'results/S4-O'
(D/'S4-ALLOCATION-COUNTER-ATTRIBUTION-REVIEW.md').write_text('''# S4-O independent attribution and work review

Fresh gpt-6-astra/high read-only review.
Critical: none. Important: none. Minor: none.

Counter semantics supported: successful result/current-task gating, usable bytes,
nonnegative realloc growth, free_acc rather than freecall; registered-thread gc_num
aggregation. Installed timing.jl corroborates distinct elapsed/compile/allocation
brackets. Historical uncertainty is properly bounded: reviewer independently confirmed
that timing.jl and both libjulia libraries are absent from M's launch inventory.
No historical callback/event capture or retroactive pin claim is made.

Next P is an appropriate source-only continuation, requiring NEW nonsymmetric inputs,
exact history/oracles, complete work counts, nonduplicated timing windows and no held
diagnostic owners before a separate numerical plan. No launch or hooks now; native
balance remains open.

No unnecessary production work, allocations or retained memory introduced. Source,
test and CI diff to master empty; numerical behavior unchanged. No new performance
improvement or numerical execution independently tested or claimed.

Reviewer read O report/current plan/P plan/script, JSON26checks/592inventory, M554
inventory and raw field schema; installed timing source, upstream accounting ranges,
14 saved targeted assembly bodies/stubs. Independently recomputed15 sampled hashes
and regenerated4 matching disassemblies: counted malloc/realloc/free and thread
aggregation. Did NOT rehash all554/592; author full592 check separately recorded.
Verified HEAD1cce03c/master0eb75c3. No old reruns, edits, Julia/nativecalls, compilation
or library loading. No correction pass and no new deferred Minor.
''')
p=D/'STATUS.md';t=p.read_text().replace('S4-O allocation-counter attribution under independent review','S4-O allocation-counter attribution accepted');t=t.replace('Report S4-ALLOCATION-COUNTER-ATTRIBUTION.md/REVIEW and results/S4-O. All rejections,','Freshgpt6astra no Critical/Important/Minor, no unnecessary production work/memory.\nReviewer15 sampled hashes/4 regenerated disassemblies; authorfull592 separate.\nReport S4-ALLOCATION-COUNTER-ATTRIBUTION.md/REVIEW and results/S4-O. All rejections,',1);p.write_text(t)
p=E/'ledger.md';t=p.read_text().replace('Fresh independent review pending. Numerical behavior and production cost\nunchanged; no docs benchmark warranted.','Fresh gpt-6-astra/high review no Critical/Important/Minor, no unnecessary production\nwork/memory. Reviewer15sample hashes/4regenerated disassemblies, author full592 separate.\nNo fix pass or newly deferred Minor. Final host groups absent, refs unchanged.\nNumerical behavior/production cost unchanged; no docs benchmark warranted.');p.write_text(t)
p=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md';t=p.read_text().replace('independent full592/5checks, all554M pins unchanged. Independent review pending.','independent full592/5checks, all554M pins unchanged. Freshgpt6astra nofindings/no\nunnecessary production work/memory; reviewer15sample hashes/4disassemblies, authorfull592\nseparate.');p.write_text(t)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();a=json.loads((E/'source-attribution.json').read_text());h=json.loads((E/'host-before.json').read_text());f=json.loads((E/'host-final.json').read_text())
checks={'full592_still_match':all(sha(p)==s for p,s in a['sha256'].items()),'user6_unchanged':all(sha(p)==s for p,s in h['user_hashes'].items()),'host_groups_absent':not f['matches'],'same_boot':h['boot_id']==f['boot_id'],'master_source_test_ci_equal':subprocess.check_output(['git','diff','master','--','src','test','.github'],cwd=R)==b'','master_unchanged':subprocess.check_output(['git','rev-parse','master'],cwd=R,text=True).strip()=='0eb75c3190096946b0e91e5360230ccd7166f298','review_no_findings':'Critical: none. Important: none. Minor: none.' in (D/'S4-ALLOCATION-COUNTER-ATTRIBUTION-REVIEW.md').read_text(),'source_only_next':'SOURCE/EVIDENCE ONLY' in (R/'docs/superpowers/plans/2026-10-12-hh-history-lifecycle-cost-contract.md').read_text()}
files=list(E.iterdir())+[D/'S4-ALLOCATION-COUNTER-ATTRIBUTION.md',D/'S4-ALLOCATION-COUNTER-ATTRIBUTION-REVIEW.md',D/'STATUS.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md',R/'docs/superpowers/plans/2026-10-12-hh-history-lifecycle-cost-contract.md']
res=dict(checks=checks,all_passed=all(checks.values()),sha256={str(p):sha(p) for p in files if p.is_file()},scope='Closure document hashes, no launch pins')
with (E/'closure.json').open('x') as out:json.dump(res,out,indent=2);out.write('\n')
print(checks);assert res['all_passed']
