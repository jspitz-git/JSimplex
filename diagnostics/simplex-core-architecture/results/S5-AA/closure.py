"""Exclusive final closure. Rehash evidence; never execute frozen auditors."""
from pathlib import Path
import hashlib,json,subprocess,tomllib,time
R=Path.cwd();M=Path('/home/jspitz/JSimplex.jl');H=Path(__file__).resolve().parent;D=H.parent.parent;S=D/'STATUS.md';P=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md';REL='test/simplex_start_state_tests.jl';cache={}
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 p=Path(p)
 if p not in cache:
  h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(1048576),b''):h.update(b)
  cache[p]=h.hexdigest()
 return cache[p]
def mapped(k,v):
 if k in [str(r/REL) for r in (R,M)] and v=='47b2cc12ea40055262bc3912beb17cfd00a0ffe3b92e7ca54970dc85eae511ad':return H/'original-test.jl'
 if k==str(S):return H/'STATUS.md.before-AA'
 if k==str(P):return H/'2026-10-11-simplex-core-architecture.md.before-AA'
 return k
c={};bindings={}
for name in ['admission-pins.json','green/pins.json','master/pins.json']:
 a=read(H/name)['inventory'];c[name]=all(sha(mapped(k,v['sha256']))==v['sha256'] and str(Path(k).resolve())==v['resolved'] for k,v in a.items())
 groups=set()
for stage in ['green','master']:
 h=H/stage;a=read(h/'audit.json');po=read(h/'postcheck.json');proc=read(h/'portable/process.json');raw=tomllib.loads((h/'portable/raw/case.toml').read_text());report=tomllib.loads((h/'portable/raw/report.toml').read_text())
 c[stage+'_audit33']=len(a['checks'])==33 and a['all_passed'] is True and all(v is True for v in a['checks'].values())
 c[stage+'_post10']=len(po['checks'])==10 and po['all_passed'] is True and all(v is True for v in po['checks'].values()) and all(sha(k)==v for k,v in po['sha256'].items())
 c[stage+'_review']=all(t in (h/'review.md').read_text() for t in ['Verdict: ACCEPTED','Unresolved findings: []'])
 c[stage+'_raw8']=len(a['raw_sha256'])==8 and all(sha(R/'.superpowers/simplex-core-architecture/S5-AA'/(stage+'-1')/k)==sha(h/'portable'/k)==v for k,v in a['raw_sha256'].items())
 c[stage+'_inv3']=len(a['invocation_sha256'])==3 and all(sha(k)==v for k,v in a['invocation_sha256'].items())
 c[stage+'_oracle']=report['passes']==52 and report['fails']==report['errors']==report['broken']==0 and report['entry_counts']==[1,1,1,1] and len(raw['checks'])==50 and all(v is True for v in raw['checks'].values())
 groups.update(proc[k]['pgid'] for k in ('runner','child'))
expected='ce256932a4bbda14bb9c55678525d6506a8e63732683442def57b22873b0415f'
c['exact_actual_tests']=sha(R/REL)==sha(M/REL)==expected
c['test_only_integrations']=all(subprocess.check_output(['git','-C',str(p),'diff-tree','--no-commit-id','--name-only','-r','HEAD'],text=True).splitlines()==[REL] for p in (R,M))
c['all_source_test_pairs']=all(sha(p)==sha(M/p.relative_to(R)) for folder in ['src','test'] for p in (R/folder).rglob('*') if p.is_file())
c['user6']=all(sha(k)==v for k,v in read(H/'host-before.json')['user_hashes'].items())
c['master_admission']=all(t in (H/'master/admission-review.md').read_text() for t in ['Verdict: ACCEPTED','Unresolved findings: []'])
from common import absent
host=absent(groups);c['full26_groups_absent']=len(host['groups'])==26 and not host['matches']
c['initial_failure_preserved']=read(H/'entry.json')['all_passed'] is False and sum(v is False for v in read(H/'entry.json')['checks'].values())==3 and read(H/'entry-2.json')['all_passed'] is True
c['no_other_tracked_edits']=set(subprocess.check_output(['git','diff','--name-only'],text=True).splitlines())=={str(S.relative_to(R)),str(P.relative_to(R))}
paths=[p for p in H.rglob('*') if p.is_file()]+[S,P,D/'S5-CRASH-FALLBACK-OBSERVER-TEST-INTEGRATION.md',D/'S5-CRASH-FALLBACK-OBSERVER-TEST-INTEGRATION-REVIEW.md',R/'docs/superpowers/plans/2026-10-13-handoff-coverage-reconciliation.md']
with (H/'closure.json').open('x') as f:json.dump(dict(checks=c,all_passed=all(c.values()),sha256={str(p):sha(p) for p in paths},host=host,fresh_hashes=len(cache),refs={str(p):subprocess.check_output(['git','-C',str(p),'rev-parse','HEAD'],text=True).strip() for p in (R,M)}),f,indent=2);f.write('\n')
print(json.dumps(c));assert all(c.values())
