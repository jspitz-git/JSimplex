from pathlib import Path
import json,hashlib,subprocess
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');D=R/'diagnostics/simplex-core-architecture/results/S2-B'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=R).decode().strip()
report=R/'diagnostics/simplex-core-architecture/S2-PRICE-AUDIT-STORAGE.md';plan=R/'docs/superpowers/plans/2026-10-13-price-audit-values-preparation.md';status=R/'diagnostics/simplex-core-architecture/STATUS.md';roadmap=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
source=json.loads((D/'source-check.json').read_text());oldmap={str(p):D/(p.name+'.before-review') for p in (report,plan)}
ap=json.loads((R/'diagnostics/simplex-core-architecture/results/S6-AP/closure.json').read_text());apmap={str(status):D/'STATUS.md.before-S2-B',str(roadmap):D/'roadmap.md.before-S2-B'}
final=json.loads((D/'review-fix-final.json').read_text());review=json.loads((D/'final-review-check.json').read_text())
groups=set(json.loads((D/'pre-continuation-host.json').read_text())['groups_checked']);hits=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  a=(p/'stat').read_text().rsplit(')',1)[1].split();comm=(p/'comm').read_text().strip()
  if int(a[2]) in groups or int(a[3]) in groups or comm.startswith('julia'):hits.append({'pid':p.name,'pgid':a[2],'sid':a[3],'start_ticks':a[19],'command':(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')})
 except (OSError,ValueError):pass
checks={
 'source13_pass':len(source['checks'])==13 and source['all_passed'] is True,
 'all531_initial_pins_reconciled':len(source['sha256'])==531 and all(sha(oldmap.get(p,p))==h for p,h in source['sha256'].items()),
 'all40_AP_closure_bindings_reconciled':len(ap['sha256'])==40 and all(sha(apmap.get(p,p))==h for p,h in ap['sha256'].items()),
 'author6_and4':all(json.loads((D/f).read_text())['all_passed'] for f in ['author-check.json','author-fix-check.json']),
 'fix5_and7bindings':len(final['checks'])==5 and final['all_passed'] is True and all(sha(p)==h for p,h in final['sha256'].items()),
 'review_accepted_exact_document':sha(D/'final-review.md')=='7d9dfbc6680680956e864e152400f185beaea2da97e3099ae0738050d4e6a6b1',
 'review_bounded_bindings':review['final_binding_count']==7 and all(review['final_bindings'].values()) and all(x['matches'] for x in review['intermediate_bindings']) and all(review['original_report_plan_bindings'].values()),
 'approved_report_plan':sha(report)=='903391ed6c6ce1fed91a3dd503032ba3bde2874e868565f0b8f44fdab8752e83' and sha(plan)=='a2f76357e74c341bd97cb68ffb47c641bd3e7d895e3906ff2b016c0c91943d08',
 'all26groups_sessions_absent':len(groups)==26 and not hits,
 'refs_unchanged':git('rev-parse','HEAD')=='c44472e7a43533fb9ec337eba86189aabbe6ac61' and git('rev-parse','master')=='d02416c108f06fcd41d58e0a1980b70a51fef9ef',
 'only_continuation_tracked_changes':set(git('diff','--name-only').splitlines())=={str(status.relative_to(R)),str(roadmap.relative_to(R))},
 'index_initially_empty':git('diff','--cached','--name-only')=='',
 'next_step_offline': 'Next S2-C:' in status.read_text() and 'NO Julia execution' in plan.read_text(),
}
paths=[p for p in D.iterdir() if p.is_file()]+[report,plan,status,roadmap,R/'diagnostics/simplex-core-architecture/S2-PRICE-AUDIT-STORAGE-REVIEW.md']
out={'checks':checks,'all_passed':all(checks.values()),'sha256':{str(p):sha(p) for p in sorted(paths)},'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'groups':sorted(groups),'live':hits,'AP_continuation_maps':{k:str(v) for k,v in apmap.items()},'initial_report_maps':{k:str(v) for k,v in oldmap.items()}}
with (D/'closure.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps({'checks':checks,'bindings':len(out['sha256']),'all_passed':out['all_passed']}));assert out['all_passed']
