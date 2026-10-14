from pathlib import Path
import hashlib,json,subprocess
r=Path(__file__).resolve().parents[4]
d=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
plan=r/'docs/superpowers/plans/2026-10-14-direct-lu-markowitz.md'
spec=r/'docs/superpowers/specs/2026-10-14-direct-lu-markowitz.md'
review=(d/'review-final.md').read_text()
initial=(d/'review-initial.md').read_text()
source=json.loads((d/'source-readtime.json').read_text())
continuation=json.loads((d/'continuation.json').read_text())
checks={
'review_accepts_plan_only':'**Verdict: ACCEPTED as a plan for subsequent offline candidate/test preparation. No unresolved actionable plan findings remain.**' in review,
'final_doc_bindings':all(sha(p) in review for p in (plan,spec)),
'initial_versions_preserved':all(sha(d/n) in initial for n in ('spec.before-review.md','plan.before-review.md')),
'intermediate_preserved':sha(d/'plan.after-first-review.md') in review,
'source_reads_unchanged':all(sha(r/p)==v for p,v in source['sha256'].items()),
'continuation_exact':len(continuation['mappings'])==4 and all(sha(r/x['preserved_path'])==x['sha256'] for x in continuation['mappings']),
'no_tracked_production_changes':not subprocess.check_output(['git','diff','--name-only','HEAD','--','src','test','Project.toml','.github'],cwd=r,text=True).strip(),
'master_unchanged':subprocess.check_output(['git','rev-parse','master'],cwd=r,text=True).strip()=='6f68e24e8ddac42b948da8fcc2d636c010751194',
'new_host_clear':not json.loads((d/'host.json').read_text())['matches'],
'schedule_counts':(24*2*10*2,24*2*10*2*8,24*2*10*2*8*2,24*2*10*2*2)==(960,7680,15360,1920),
'diffcheck':subprocess.run(['git','diff','--check'],cwd=r,capture_output=True).returncode==0,
}
files=[plan,spec,r/'diagnostics/simplex-core-architecture/STATUS.md',r/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md',r/'diagnostics/simplex-core-architecture/DIRECT-LU-MARKOWITZ-PLAN.md']+sorted(p for p in d.iterdir() if p.is_file())
result={'all_passed':all(checks.values()),'checks':checks,'scope':'Plan/document closure only; not numerical evidence','sha256':{str(p.relative_to(r)):sha(p) for p in files}}
with (d/'closure.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({'all_passed':result['all_passed'],'checks':checks,'bindings':len(files)}))
if not result['all_passed']:raise SystemExit(1)
