from pathlib import Path
import json,hashlib,subprocess
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');D=R/'diagnostics/simplex-core-architecture';E=D/'results/S4-N'
(D/'S4-NATIVE-ACCOUNTING-FEASIBILITY-REVIEW.md').write_text('''# S4-N independent contract and work review

Fresh gpt-6-astra/high, read-only review of the report, N contract, O next plan,
installed wrappers, actual ELF code and versioned upstream references.

Critical: none. Important: none. Minor: none.

The unsupported complete-accounting conclusion is justified. Actual installed
helper bodies reach callbacks, but this is distinct from transitive allocation
coverage or captured successful runtime initialization. Source-only S4-O is the
appropriate narrower next obligation; no numerical/hook experiment is qualified.

Reviewer independently inspected actual ELF bodies for umf_l_malloc/realloc/free,
SuiteSparse callback routes and setter, including count clamp/overflow/raw realloc.
An initial exact text comparison differed only in trailing full-disassembly padding;
semantic instructions matched. Installed LibSuiteSparse.jl lines35–103, umfpack.jl
171–187,283–295,1000–1014 inspected for initialization, finalization and shared owners.
Versioned upstream ABI/global slots/restore semantics checked. Eleven sampled hashes
independently recomputed and matched. Reviewer read the 572-entry supplement/five
checks but did NOT rehash all572; author full verification is separate. Production,
test and CI diff to master empty; HH reuse_symbolic=false remains at source line538.

No unnecessary production work or retained memory introduced. Prospective callback
work per event and O(C) ledger storage are explicitly accounted for, with no measured
instrumentation-cost claim. Numerical behavior unchanged; no new numerical tests or
benchmarks warranted for this scope. No Julia, dlopen/native calls, hook changes or
edits performed by reviewer. No fix pass or newly deferred Minor.
''')
p=D/'STATUS.md';t=p.read_text().replace('S4-N source-only accounting feasibility under independent review','S4-N source-only accounting feasibility accepted');t=t.replace('All old accepted drivers/evidence unchanged; production/test/master/CI unchanged.','Fresh gpt-6-astra review: no Critical/Important/Minor; no unnecessary production work\nor retained memory. Reviewer independently sampled11 hashes; author full572 separate.\nAll old accepted drivers/evidence unchanged; production/test/master/CI unchanged.',1);p.write_text(t)
p=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md';t=p.read_text();t=t.replace('Fresh review\npending. Next ONE source-only S4-O plan:','Fresh independent gpt-6-astra review found no Critical/Important/Minor and no\nunnecessary production work/memory. Reviewer11sample hashes; author full572 separate.\nNext ONE source-only S4-O plan:');p.write_text(t)
p=E/'ledger.md';t=p.read_text().replace('Fresh independent review pending. No production work or retained memory introduced.','Fresh independent gpt-6-astra/high review: no Critical/Important/Minor; no unnecessary\nproduction work/memory. Reviewer sampled11 hashes and actual source/instructions;\nauthor full572 separate. No correction pass or newly deferred Minor. Host final\nfull-group scan again empty, refs unchanged. No production work or memory introduced.');p.write_text(t)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
a=json.loads((E/'independent-full.json').read_text());old=json.loads((E/'host-before.json').read_text());host=json.loads((E/'host-final.json').read_text())
checks={'full572_unchanged':all(sha(p)==h for p,h in a['sha256'].items()),'six_user_hashes_unchanged':all(sha(p)==h for p,h in old['user_hashes'].items()),'source_test_ci_master_identical':subprocess.check_output(['git','diff','master','--','src','test','.github'],cwd=R)==b'','no_previous_process_groups_or_julia':host['matches']==[],'boot_same':host['boot_id']==old['boot_id'],'master_unchanged':subprocess.check_output(['git','rev-parse','master'],cwd=R,text=True).strip()=='0eb75c3190096946b0e91e5360230ccd7166f298','independent_review_no_findings':'Critical: none. Important: none. Minor: none.' in (D/'S4-NATIVE-ACCOUNTING-FEASIBILITY-REVIEW.md').read_text(),'one_source_only_continuation':'S4-O' in (D/'STATUS.md').read_text() and 'SOURCE/EVIDENCE ONLY' in (R/'docs/superpowers/plans/2026-10-12-hh-allocation-counter-attribution.md').read_text()}
files=list(E.iterdir())+[D/'S4-NATIVE-ACCOUNTING-FEASIBILITY.md',D/'S4-NATIVE-ACCOUNTING-FEASIBILITY-REVIEW.md',D/'STATUS.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md',R/'docs/superpowers/plans/2026-10-12-hh-allocation-counter-attribution.md']
res={'checks':checks,'all_passed':all(checks.values()),'sha256':{str(p):sha(p) for p in files if p.is_file()},'scope':'Final document/evidence hashes, not launch pins'}
with (E/'closure.json').open('x') as f:json.dump(res,f,indent=2);f.write('\n')
print(json.dumps(checks,indent=2));assert res['all_passed']
