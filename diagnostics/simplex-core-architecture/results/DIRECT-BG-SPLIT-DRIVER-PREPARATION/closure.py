from pathlib import Path
import json,hashlib,subprocess
import control as c
D=Path(__file__).resolve().parent;R=c.R
def sha(p):return c.sha(p)
def need(v,m):c.require(v,m)
files=c.preparation()
c.validate_sources()
c.validate_environment()
host=c.full_host();host['remote_refs']=c.git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture')
need(not host['matches'] and len(host['groups'])==240,'Host groups/sessions/Julia')
need(host['head']+'\trefs/heads/codex/simplex-core-architecture' in host['remote_refs'],'Diagnostic remote differs')
need(c.MASTER+'\trefs/heads/master' in host['remote_refs'],'Master remote differs')
c.save(D/'host-closure.json',host)
checks=dict(preparation_review_exact=True,source_runtime_stage_membership=True,environment=True,host_clear=True,remote_refs=True,no_runs=not (D/'runs').exists(),actual_tracked_unchanged=subprocess.run(['git','diff','--quiet','HEAD'],cwd=R).returncode==0,index_empty=not c.git('diff','--cached','--name-only'))
for n,count in [('offline-tests.json',114),('negative-supplement.json',20),('warning-tests.json',13),('source-check.json',40)]:
 j=c.rd(D/n);checks[n]=j['all_passed'] and len(j['checks'])==count
checks['author_source_bindings']=c.bindings(c.rd(D/'source-check.json'))
checks['review_evidence']=c.bindings(c.rd(D/'review.json'),'evidence_sha256') if 'evidence_sha256' in c.rd(D/'review.json') else True
names=c.rd(D/'publication-names.json')['names'];scope=str(D.relative_to(R))+'/'
checks['publication_scope']=len(names)==len(set(names)) and all(n.startswith(scope) and '/' not in n[len(scope):] for n in names)
checks['publication_membership']={str(p.relative_to(R)) for p in D.iterdir() if p.is_file()}=={n for n in names if Path(n).name not in ['closure.json','publication.json']}
checks['no_nested_outputs']=all(p.is_file() for p in D.iterdir())
r=dict(all_passed=all(checks.values()),scope='Offline RED/GREEN driver preparation only. No Julia or numerical admission.',checks=checks,sha256={n:sha(R/n) for n in names if Path(n).name not in ['closure.json','publication.json']})
c.save(D/'closure.json',r)
print(json.dumps(dict(all_passed=r['all_passed'],checks=len(checks),bindings=len(r['sha256']),failed=[k for k,v in checks.items() if not v])))
need(r['all_passed'],'Closure failed')
