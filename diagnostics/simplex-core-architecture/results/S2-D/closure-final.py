from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/S2-D';C=D.parent/'S2-C'
def read(p):return json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
def bindings(o,mapping={}):return all(sha(mapping.get(p,Path(p)))==h for p,h in o['sha256'].items())
mapper={str(R/'diagnostics/simplex-core-architecture/STATUS.md'):D/'STATUS.md.before-S2-D',str(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'):D/'roadmap.md.before-S2-D'}
report=R/'diagnostics/simplex-core-architecture/S2-PRICE-AUDIT-ADMISSION-PREPARATION.md';oldreport={str(report):D/'report.before-review'}
pins=read(D/'admission-pins-reviewed.json')['inventory'];initial=read(D/'admission-pins.json')['inventory'];review=read(D/'final-review-check.json');host=read(D/'pre-continuation-host.json')
checks={
'initial780_unchanged':len(initial)==780 and all(sha(Path(p))==v['sha256'] for p,v in initial.items()),
'reviewed801_full':len(pins)==801 and all(sha(Path(p))==v['sha256'] and str(Path(p).resolve(strict=True))==v['resolved'] for p,v in pins.items()),
'Cclosure35_preserved':len(read(C/'closure-final.json')['sha256'])==35 and bindings(read(C/'closure-final.json'),mapper),
'initial_author6_preserved':read(D/'author-check.json')['all_passed'] and bindings(read(D/'author-check.json'),oldreport),
'initial_rejection_preserved':not read(D/'reviewer-check.json')['accepted'] and bindings(read(D/'reviewer-check.json'),oldreport),
'initial16_and25_preserved':read(D/'source-check.json')['all_passed'] and read(D/'failure-tests.json')['all_passed'],
'fix5_pass':read(D/'review-fix.json')['all_passed'] and bindings(read(D/'review-fix.json')),
'fix32_pass':read(D/'review-fix-tests.json')['all_passed'] and bindings(read(D/'review-fix-tests.json')),
'fix_author5':all(read(D/'review-fix-author.json')['checks'].values()) and bindings(read(D/'review-fix-author.json')),
'final_review_accepted':'ACCEPTED for S2-D offline admission preparation only.' in (D/'final-review.md').read_text() and review['accepted'] is True,
'final_review_checks':review['all_passed'] and all(review['checks'].values()),
'final_review_bindings':bindings(review),
'no_unresolved_findings':review['unresolved_findings']==[],
'fresh_host5':host['all_passed'] and len(host['groups'])==26 and not host['matches'],
'user6_current':all(sha(Path(p))==v['sha256'] for p,v in host['user'].items()),
'HEAD_unchanged':git('rev-parse','HEAD')=='fdd4f5c67fdf1b0cdba3de85f5dcaaa887fa2f15',
'master_unchanged':git('rev-parse','master')=='d02416c108f06fcd41d58e0a1980b70a51fef9ef',
'actual_source_test_env_ci_unchanged':not git('diff','--name-only','master','--','src','test','.github','Project.toml'),
'only_continuation_tracked_edits':set(git('diff','--name-only').splitlines())=={str(Path(p).relative_to(R)) for p in mapper},
'index_empty':not git('diff','--cached','--name-only'),
'no_allowance_or_launchpins':not (D/'allowance.json').exists() and not (D/'launch-pins.json').exists(),
'no_numerical_output':not (R/'.superpowers/simplex-core-architecture/S2-D/qualification-1').exists(),
'no_python_bytecache':not list(D.rglob('__pycache__')),
'next_requires_human_allowance':'until the human explicitly grants' in (R/'docs/superpowers/plans/2026-10-13-price-audit-values-qualification.md').read_text(),
}
paths=sorted(p for p in D.rglob('*') if p.is_file())+[report,R/'diagnostics/simplex-core-architecture/S2-PRICE-AUDIT-ADMISSION-PREPARATION-REVIEW.md',R/'diagnostics/simplex-core-architecture/STATUS.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md',R/'docs/superpowers/plans/2026-10-13-price-audit-values-qualification.md']
out={'checks':checks,'all_passed':all(checks.values()),'sha256':{str(p):sha(p) for p in paths},'C35_mapping':{p:str(v) for p,v in mapper.items()},'initial_author_reviewer_report_mapping':{p:str(v) for p,v in oldreport.items()},'scope':'OFFLINE ONLY; no numerical allowance, Julia or production changes'}
with (D/'closure.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps({'checks':checks,'bindings':len(out['sha256'])}))
if not out['all_passed']:raise SystemExit(1)
