from pathlib import Path
import json,hashlib,subprocess,time
R=Path.cwd();E=R/'diagnostics/simplex-core-architecture/results/S2-E';D=E.parent/'S2-D';C=E.parent/'S2-C'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def put(p,o):
 with Path(p).open('x') as f:json.dump(o,f,indent=2);f.write('\n')
def bindings(o,m={}):return all(sha(m.get(p,p))==h for p,h in o['sha256'].items())
def git(*args):return subprocess.check_output(['git',*args],text=True).strip()
host=read('/tmp/s2e-host-before.json')
with (E/'host-before.json').open('xb') as f:f.write(Path('/tmp/s2e-host-before.json').read_bytes())
for p,n in [(R/'diagnostics/simplex-core-architecture/STATUS.md','STATUS.md.before-S2-E'),(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md','roadmap.md.before-S2-E')]:
 with (E/n).open('xb') as f:f.write(p.read_bytes())
report=R/'diagnostics/simplex-core-architecture/S2-PRICE-AUDIT-ADMISSION-PREPARATION.md'
oldreport={str(report):D/'report.before-review'}
cmap={str(R/'diagnostics/simplex-core-architecture/STATUS.md'):D/'STATUS.md.before-S2-D',str(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'):D/'roadmap.md.before-S2-D'}
pins=read(D/'admission-pins-reviewed.json');old=read(D/'admission-pins.json');review=read(D/'final-review-check.json');closure=read(D/'closure.json');pub=read(D/'publication.json')
expected=pub['expected_staged_names'];actual=git('diff-tree','--no-commit-id','--name-only','-r','HEAD').splitlines()
checks={
 'host_refs_remote':host['refs']=={'HEAD':'36b718e9e30102807a22522efdef5a37b1f42a2c','master':'d02416c108f06fcd41d58e0a1980b70a51fef9ef'} and host['remote']=={'refs/heads/master':host['refs']['master'],'refs/heads/codex/simplex-core-architecture':host['refs']['HEAD']},
 'host26_groups_sessions_noJulia':len(host['groups'])==26 and not host['matches'],
 'user6':len(host['user_ok'])==6 and all(host['user_ok'].values()) and all(sha(p)==v['sha256'] for p,v in host['user'].items()),
 'reviewed801':len(pins['inventory'])==801 and all(sha(p)==v['sha256'] and str(Path(p).resolve(strict=True))==v['resolved'] for p,v in pins['inventory'].items()),
 'initial780':len(old['inventory'])==780 and all(sha(p)==v['sha256'] for p,v in old['inventory'].items()),
 'initial_author6_report_mapping':len(read(D/'author-check.json')['checks'])==6 and bindings(read(D/'author-check.json'),oldreport),
 'initial_rejected_review_preserved':read(D/'reviewer-check.json')['accepted'] is False and bindings(read(D/'reviewer-check.json'),oldreport),
 'final22_48':review['accepted'] is True and review['all_passed'] is True and review['unresolved_findings']==[] and len(review['checks'])==22 and all(review['checks'].values()) and len(review['sha256'])==48 and bindings(review),
 'closure24_127':closure['all_passed'] is True and len(closure['checks'])==24 and all(closure['checks'].values()) and len(closure['sha256'])==127 and bindings(closure),
 'publication6_128':pub['all_passed'] is True and len(pub['checks'])==6 and all(pub['checks'].values()) and len(pub['sha256'])==128 and bindings(pub),
 'exact129_committed_names_blobs':len(expected)==129 and set(expected)==set(actual) and all(subprocess.check_output(['git','show','HEAD:'+p])==(R/p).read_bytes() for p in expected),
 'Cclosure35':len(read(C/'closure-final.json')['sha256'])==35 and bindings(read(C/'closure-final.json'),cmap),
 'actual_source_test_env_CI_master_equal':not git('diff','--name-only','master','--','src','test','.github','Project.toml'),
 'tracked_index_clean':not git('diff','--name-only') and not git('diff','--cached','--name-only'),
 'separate_absent_numerical_paths':not any((D/n).exists() for n in ['allowance.json','launch-pins.json','numerical-review.md','attempt-reserved.json','invocation.json','launcher.log','audit.json']) and not (R/'.superpowers/simplex-core-architecture/S2-D/qualification-1').exists(),
 'existing_isolated_worktree':git('rev-parse','--git-dir')!=git('rev-parse','--git-common-dir') and not git('rev-parse','--show-superproject-working-tree') and git('branch','--show-current')=='codex/simplex-core-architecture',
}
paths=[E/'entry.py',E/'host-before.json',E/'STATUS.md.before-S2-E',E/'roadmap.md.before-S2-E',D/'admission-pins-reviewed.json',D/'final-review.md',D/'final-review-check.json',D/'closure.json',D/'publication.json',R/'docs/superpowers/plans/2026-10-13-price-audit-values-qualification.md']
put(E/'entry.json',{'checks':checks,'all_passed':all(checks.values()),'sha256':{str(p):sha(p) for p in paths},'historical_report_map':{p:str(v) for p,v in oldreport.items()},'C35_map':{p:str(v) for p,v in cmap.items()},'time_ns':time.time_ns()})
print(json.dumps({'checks':checks,'bindings':len(paths)}))
if not all(checks.values()):raise SystemExit(1)
