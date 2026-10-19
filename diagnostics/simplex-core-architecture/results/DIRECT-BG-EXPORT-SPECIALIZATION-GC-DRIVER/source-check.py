"""New read-only source/pin verification, no frozen checker rerun and no Julia."""
from pathlib import Path
import sys,json,ast
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import control as c
N=P.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-GC-PREPARATION');D=P.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-DRIVER');Q=P.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-RED');checks={}
def ck(n,v):
 checks[n]=bool(v)
 if not v:raise RuntimeError(n)
m=P/'preparation-pins.json';j=c.rd(m);ck('full_2286_manifest',len(j['sha256'])==2286 and c.bindings(j))
ck('required_membership',set(j['sha256'])==set(c.rd(P/'required-paths.json')['paths']))
nm=N/'preparation-pins-reviewed.json';nj=c.rd(nm);c.verify_review(c.rd(N/'review.json'),nm,list(nj['sha256'])+[str(nm)],'BG specialization fixed GC preparation');ck('accepted_gc_source_review',True)
for name,item in c.rd(P/'copied-files.json').items():ck('copy_'+name,c.sha(P/name)==c.sha(item['source'])==item['sha256'])
c.validate_environment();ck('environment',True);c.validate_sources();ck('source_stage_runtime',True)
ck('stage83',all(len(s['sha256'])==83 for s in c.rd(P/'stages.json').values()))
for name in ['offline-tests.json','full-audit-tests.json']:
 v=c.rd(P/name);ck(name,v['all_passed'] and all(v['checks'].values()))
for path in P.glob('*.py'):ast.parse(path.read_text(),filename=str(path))
ck('python_source_parse_only',True)
ck('old_publications_unchanged',all(c.bindings(c.rd(root/'publication.json')) for root in [D,N,Q]))
ck('old_failure_preserved',c.rd(D/'runs/red300/audit.json')['all_passed'] is False and c.rd(D/'runs/red300/audit.json')['pure_timeout'] is False)
ck('no_operational_artifacts',all(not (P/n).exists() for n in ['runs','outers','sealed.json','admission.json','release.json','reservation.json','output']))
c.save(P/'source-check.json',dict(all_passed=True,checks=checks,sha256={str(m):c.sha(m),str(P/'source-check.py'):c.sha(P/'source-check.py')},scope='New offline full read-time hashes and source identities only, no Julia or actual admission'))
print('Source check PASS',len(checks))
