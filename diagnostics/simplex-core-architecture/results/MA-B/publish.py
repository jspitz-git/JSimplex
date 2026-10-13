"""One-use documentation closure and exact fail-fast publication. No numerics."""
from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-B';A=D.parent/'MA-A'
BASE='950903feddf80d4c4aa17544a710b787e050d474';MASTER='d02416c108f06fcd41d58e0a1980b70a51fef9ef'
NAMES=('STATUS.md.before-MA-B','roadmap.md.before-MA-B','host.json','continuation-map.json','review.md','review.json','publish.py')
CONT=('diagnostics/simplex-core-architecture/STATUS.md','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md')
def require(ok,msg):
 if not ok:raise ValueError(msg)
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git','-C',str(R),*a],text=True).strip()
def dump(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
require(git('rev-parse','HEAD')==BASE and git('rev-parse','master')==MASTER,'refs')
require(not git('diff','--cached','--name-only'),'index')
require(set(git('diff','--name-only').splitlines())==set(CONT),'tracked scope')
require({p.name for p in D.iterdir()}==set(NAMES),'exact new evidence names')
mapping=read(D/'continuation-map.json')['mapping']
for n in ('result-review.json','closure.json','publication.json'):
 for p,h in read(A/n)['sha256'].items():
  q=Path(p);rel=str(q.relative_to(R)) if q.is_absolute() and q.is_relative_to(R) else p
  target=R/mapping[rel]['saved_path'] if rel in mapping else R/p
  require(sha(target)==h,'preserved MA-A binding:'+p)
for rel,v in mapping.items():require(subprocess.check_output(['git','-C',str(R),'show',BASE+':'+rel])==(R/v['saved_path']).read_bytes(),'exact before text')
rev=read(D/'review.json');require(rev['all_passed'] is True and rev['unresolved_findings']==[] and all(v is True for v in rev['checks'].values()),'independent review')
require('MA-B PLAN ADDITION ACCEPTED' in (D/'review.md').read_text(),'review marker')
for p,h in rev['sha256'].items():require(sha(R/p)==h,'review hash:'+p)
host=read(D/'host.json');require(host['matches']==[] and len(host['groups'])==32 and host['head']==BASE and host['master']==MASTER,'fresh preflight')
files=sorted([*CONT,*[str((D/n).relative_to(R)) for n in NAMES]])
require(set(git('ls-files','--others','--exclude-standard').splitlines())==set(files)-set(CONT)|{'Manifest.toml','LocalPreferences.toml'},'untracked scope')
checks=dict.fromkeys(['refs_index_scope','exact_new_files','all_MA_A_final_bindings_preserved','exact_committed_before_texts','independent_plan_review','all_review_bindings','fresh32groups_ANDsessions_preflight','documentation_only','exact_untracked_completeness'],True)
dump(D/'closure.json',{'all_passed':True,'checks':checks,'sha256':{p:sha(R/p) for p in files},'previous_MA_A_mapping':mapping,'scope':'User-requested pending roadmap item only; no implementation or numerics.'})
files.append(str((D/'closure.json').relative_to(R)));pub=str((D/'publication.json').relative_to(R));names=sorted(files+[pub])
dump(D/'publication.json',{'all_passed':True,'expected_staged_names':names,'sha256':{p:sha(R/p) for p in files},'checks':{'separate_closure_passed':True,'fixed_complete_names':True},'self_exclusion':'Own recursive hash excluded; actual staged and committed bytes checked.'})
subprocess.run(['git','-C',str(R),'add','--',*names],check=True)
require(git('diff','--cached','--name-only').splitlines()==names,'staged names')
for p in names:require(subprocess.check_output(['git','-C',str(R),'show',':'+p])==(R/p).read_bytes(),'staged bytes')
subprocess.run(['git','-C',str(R),'diff','--cached','--check'],check=True)
require(set(git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture').splitlines())=={BASE+'\trefs/heads/codex/simplex-core-architecture',MASTER+'\trefs/heads/master'},'remote refs')
print({'closure_checks':len(checks),'exact_staged_blobs':len(names),'all_passed':True},flush=True)
subprocess.run(['git','-C',str(R),'commit','-m','docs: add selective MutableArithmetics roadmap workstream'],check=True)
commit=git('rev-parse','HEAD');require(git('diff-tree','--no-commit-id','--name-only','-r',commit).splitlines()==names,'committed names')
for p in names:require(subprocess.check_output(['git','-C',str(R),'show',commit+':'+p])==(R/p).read_bytes(),'committed bytes')
subprocess.run(['git','-C',str(R),'push','origin','HEAD:refs/heads/codex/simplex-core-architecture'],check=True)
require(set(git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture').splitlines())=={commit+'\trefs/heads/codex/simplex-core-architecture',MASTER+'\trefs/heads/master'},'remote verification')
print({'commit':commit,'master':MASTER,'exact_committed_blobs':len(names),'remote_verified':True},flush=True)
