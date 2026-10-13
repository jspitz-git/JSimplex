"""One-use S4-AA result closure/publication; never executes numerical tools."""
from pathlib import Path
import sys,subprocess
R=Path.cwd();A=R/'diagnostics/simplex-core-architecture/results/S4-AA';Z=A.parent/'S4-Z';sys.path.insert(0,str(Z))
from common import read,dump,sha,require,manifest_ok,OUT,GROUPS
BASE='52cd959a07ce4240a8d18d71f3da742d1708d662';MASTER='d02416c108f06fcd41d58e0a1980b70a51fef9ef'
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
status='diagnostics/simplex-core-architecture/STATUS.md';roadmap='docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
report='diagnostics/simplex-core-architecture/S4-MARKOWITZ-RETENTION-QUALIFICATION.md';review='diagnostics/simplex-core-architecture/S4-MARKOWITZ-RETENTION-QUALIFICATION-REVIEW.md'
AA={'STATUS.md.before-S4-AA','roadmap.md.before-S4-AA','authorization.json','continuation-map.json','host.json','numerical-review.json','postcheck.json','postcheck.py','prelaunch-host.json','qualification-1/current.json','qualification-1/pins.json','qualification-1/process.json','qualification-1/resources.jsonl','qualification-1/retention.toml','qualification-1/run.log','review.json','publish.py','pre-publication-host.json'}
ZN={'launch-pins.json','numerical-review.md','allowance.json','attempt-reserved.json','launcher.log','invocation.json','audit.json'}
require({str(p.relative_to(A)) for p in A.rglob('*') if p.is_file()}==AA,'AA whitelist')
require(git('rev-parse','HEAD')==BASE and git('rev-parse','master')==MASTER,'refs')
require(not git('diff','--cached','--name-only'),'index')
require(set(git('diff','--name-only').splitlines())=={status,roadmap},'tracked scope')
require(not git('diff','master','--','src','test','.github'),'production/test/CI')
pins=read(Z/'launch-pins.json');require(manifest_ok(pins,read(Z/'required-paths.json')),'711 launch pins')
require(len(pins['inventory'])==711,'launch membership')
for n in ('audit.json',):
 x=read(Z/n);require(x['all_passed'] is True and all(v is True for v in x['checks'].values()),n)
post=read(A/'postcheck.json');require(post['all_passed'] is True and all(v is True for v in post['checks'].values()),'postcheck')
for p,h in post['sha256'].items():require(sha(p)==h,'post binding:'+p)
for q in (A/'qualification-1').iterdir():require(sha(q)==sha(OUT/q.name),'portable:'+q.name)
mapping=read(A/'continuation-map.json')['mapping']
for n in ('review.json','closure.json','publication.json'):
 for p,h in read(Z/n)['sha256'].items():
  rel=str(Path(p).relative_to(R)) if Path(p).is_absolute() and Path(p).is_relative_to(R) else p
  q=R/mapping[rel]['saved_path'] if rel in mapping else R/p
  require(sha(q)==h,'Z preserved binding:'+p)
for p in read(Z/'publication.json')['expected_staged_names']:
 q=R/mapping[p]['saved_path'] if p in mapping else R/p
 require(subprocess.check_output(['git','show',BASE+':'+p])==q.read_bytes(),'actual Z committed blob:'+p)
rev=read(A/'review.json');require(rev['all_passed'] is True and rev['unresolved_findings']==[] and all(v is True for v in rev['checks'].values()),'result review')
require('S4-AA ACCEPTED' in (R/review).read_text(),'result review marker')
for p,h in rev['sha256'].items():require(sha(R/p)==h,'result review hash:'+p)
host=read(A/'pre-publication-host.json');p=read(OUT/'process.json');groups=GROUPS|{p['runner']['pgid'],p['child']['pgid']}
require(set(host['groups'])==groups and not host['matches'] and host['head']==BASE and host['master']==MASTER,'fresh full30groups ANDsessions')
files=sorted([status,roadmap,report,review]+[str((A/n).relative_to(R)) for n in AA]+[str((Z/n).relative_to(R)) for n in ZN])
require(set(git('ls-files','--others','--exclude-standard').splitlines())==set(files)-{status,roadmap}|{'Manifest.toml','LocalPreferences.toml'},'untracked completeness')
checks=dict.fromkeys(['exact_new_evidence_names','refs_index_tracked_scope','production_test_CI_unchanged','full711_launch_hashes','admitted_audit_passed','postcheck_passed_hashes','portable_raw_identical','Z_final_continuation_maps','actual_Z_committed_blobs','independent_result_review','result_review_hashes','fresh_full30groups_ANDsessions_noJulia','exact_untracked_scope'],True)
dump(A/'closure.json',{'checks':checks,'all_passed':True,'sha256':{p:sha(R/p) for p in files},'previous_Z_mapping':mapping,'scope':'One completed numerical attempt; all numerical evidence and old scripts frozen.'})
files.append(str((A/'closure.json').relative_to(R)));pub=str((A/'publication.json').relative_to(R));names=sorted(files+[pub])
dump(A/'publication.json',{'checks':{'separate_closure_passed':True,'fixed_complete_names':True},'all_passed':True,'expected_staged_names':names,'sha256':{p:sha(R/p) for p in files},'self_exclusion':'Own recursive hash excluded; every staged and committed byte checked separately.'})
subprocess.run(['git','add','--',*names],check=True)
require(git('diff','--cached','--name-only').splitlines()==names,'staged names')
for p in names:require(subprocess.check_output(['git','show',':'+p])==(R/p).read_bytes(),'staged blob:'+p)
subprocess.run(['git','diff','--cached','--check','--',*[p for p in names if not p.endswith('.before-S4-AA')]],check=True)
require(set(git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture').splitlines())=={BASE+'\trefs/heads/codex/simplex-core-architecture',MASTER+'\trefs/heads/master'},'remote refs')
print({'closure_checks':len(checks),'exact_staged_names_blobs':len(names),'all_passed':True},flush=True)
subprocess.run(['git','commit','-m','docs: qualify Markowitz shrink-history retention'],check=True)
commit=git('rev-parse','HEAD');require(git('diff-tree','--no-commit-id','--name-only','-r',commit).splitlines()==names,'committed names')
for p in names:require(subprocess.check_output(['git','show',commit+':'+p])==(R/p).read_bytes(),'committed blob:'+p)
subprocess.run(['git','push','origin','HEAD:refs/heads/codex/simplex-core-architecture'],check=True)
require(set(git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture').splitlines())=={commit+'\trefs/heads/codex/simplex-core-architecture',MASTER+'\trefs/heads/master'},'remote verification')
require(git('rev-parse','master')==MASTER,'master changed')
print({'commit':commit,'master':MASTER,'exact_committed_blobs':len(names),'remote_verified':True},flush=True)
