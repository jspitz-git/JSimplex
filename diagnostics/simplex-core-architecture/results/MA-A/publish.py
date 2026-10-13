"""One-use MA-A closure and exact fail-fast publication; no numerical execution."""
from common import *
BASE='af3cafba218a15271a43cb6d06f08b5efc07e6df';MASTER='d02416c108f06fcd41d58e0a1980b70a51fef9ef'
def git(*a):return subprocess.check_output(['git','-C',str(R),*a],text=True).strip()
status='diagnostics/simplex-core-architecture/STATUS.md';roadmap='docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
report='diagnostics/simplex-core-architecture/MA-PRIVATE-SCALAR-KERNEL.md'
NAMES=('STATUS.md.before-MA-A', 'allowance.json', 'attempt-reserved.json', 'audit.json', 'audit.py', 'authorization.json', 'common.py', 'continuation-map.json', 'driver.jl', 'env/Manifest.toml', 'env/Project.toml', 'guard.py', 'host.json', 'invocation.json', 'invocation.json.before-seal', 'launch-pins.json', 'launcher.log', 'launcher.log.before-seal', 'launcher.py', 'numerical-review.md', 'oracle.py', 'plan.md', 'postcheck.json', 'postcheck.py', 'pre-publication-host.json', 'prelaunch-host-final.json', 'prelaunch-host.json', 'preparation.json', 'prepare.py', 'preseal-failure.md', 'publish.py', 'qualification-1/current.json', 'qualification-1/measurement.toml', 'qualification-1/pins.json', 'qualification-1/process.json', 'qualification-1/resources.jsonl', 'qualification-1/run.log', 'required-paths.json', 'result-review.json', 'result-review.md', 'review.json', 'roadmap.md.before-MA-A', 'seal-supplement.json', 'seal-supplement.md')

require({str(p.relative_to(D)) for p in D.rglob('*') if p.is_file()}==set(NAMES),'exact MA-A whitelist')
require(git('rev-parse','HEAD')==BASE and git('rev-parse','master')==MASTER,'refs')
require(not git('diff','--cached','--name-only'),'index not empty')
require(set(git('diff','--name-only').splitlines())=={status,roadmap},'tracked scope')
require(not git('diff','master','--','src','test','.github','Project.toml'),'production/test/project/CI')
pins=read(D/'launch-pins.json');require(len(pins['inventory'])==622 and manifest_ok(pins,read(D/'required-paths.json')),'all622launchpins')
for n in ('audit.json','postcheck.json'):
 x=read(D/n);require(x['all_passed'] is True and all(v is True for v in x['checks'].values()),n)
 for p,h in x['sha256'].items():require(sha(p)==h,'result binding:'+p)
for q in (D/'qualification-1').iterdir():require(sha(q)==sha(OUT/q.name),'portable:'+q.name)
require(read(D/'invocation.json.before-seal')['returncode'] is None and (D/'launcher.log.before-seal').stat().st_size==0,'preserved preseal failure')
require(sha(D/'driver.jl')=='ef060c79736c9df4142bd1603fb6132a57c51b0c4fa0069d47e38e4047a64854','exact accepted driver')
mapping=read(D/'continuation-map.json')['mapping'];AA=D.parent/'S4-AA'
for n in ('review.json','closure.json','publication.json'):
 for p,h in read(AA/n)['sha256'].items():
  rel=str(Path(p).relative_to(R)) if Path(p).is_absolute() and Path(p).is_relative_to(R) else p
  q=R/mapping[rel]['saved_path'] if rel in mapping else R/p
  require(sha(q)==h,'AA preserved binding:'+p)
for p in read(AA/'publication.json')['expected_staged_names']:
 q=R/mapping[p]['saved_path'] if p in mapping else R/p
 require(subprocess.check_output(['git','-C',str(R),'show',BASE+':'+p])==q.read_bytes(),'actual AA committed blob:'+p)
rv=read(D/'result-review.json');require(rv['all_passed'] is True and rv['unresolved_findings']==[] and all(v is True for v in rv['checks'].values()),'result review')
require('MA-A RESULTS ACCEPTED' in (D/'result-review.md').read_text(),'result marker')
for p,h in rv['sha256'].items():require(sha(R/p)==h,'review hash:'+p)
p=read(OUT/'process.json');host=absent([p[k]['pgid'] for k in ('runner','child')]);require(not host['matches'] and len(host['groups'])==32,'fresh full32groups ANDsessions/noJulia')
files=sorted([status,roadmap,report]+[str((D/n).relative_to(R)) for n in NAMES])
require(set(git('ls-files','--others','--exclude-standard').splitlines())==(set(files)-{status,roadmap})|{'Manifest.toml','LocalPreferences.toml'},'exact untracked completeness')
checks=dict.fromkeys(['exact_new_evidence_names','refs_index_scope','production_test_project_CI_unchanged','full622launchhashes','admitted_audit_and_postcheck_passed','all_result_bindings','portable_raw_identical','preseal_failure_preserved_no_numerical_retry','exact_accepted_driver','AA_final_continuation_maps','actual_AA_committed_blobs','independent_result_review_and_bindings','fresh32groups_ANDsessions_noJulia','exact_untracked_scope'],True)
dump(D/'closure.json',{'checks':checks,'all_passed':True,'sha256':{p:sha(R/p) for p in files},'host':host,'previous_AA_mapping':mapping,'scope':'One completed isolated numerical experiment. No production integration. All numerical artifacts frozen.'})
files.append(str((D/'closure.json').relative_to(R)));pub=str((D/'publication.json').relative_to(R));names=sorted(files+[pub])
dump(D/'publication.json',{'all_passed':True,'checks':{'separate_closure_passed':True,'fixed_complete_names':True},'expected_staged_names':names,'sha256':{p:sha(R/p) for p in files},'self_exclusion':'Own recursive hash excluded; every staged and committed blob verified separately.'})
subprocess.run(['git','-C',str(R),'add','--',*names],check=True)
require(git('diff','--cached','--name-only').splitlines()==names,'staged names')
for p in names:require(subprocess.check_output(['git','-C',str(R),'show',':'+p])==(R/p).read_bytes(),'staged blob:'+p)
subprocess.run(['git','-C',str(R),'diff','--cached','--check','--',*[p for p in names if not p.endswith('.before-MA-A')]],check=True)
require(set(git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture').splitlines())=={BASE+'\trefs/heads/codex/simplex-core-architecture',MASTER+'\trefs/heads/master'},'remote refs')
print({'closure_checks':len(checks),'exact_staged_names_blobs':len(names),'all_passed':True},flush=True)
subprocess.run(['git','-C',str(R),'commit','-m','docs: measure private MutableArithmetics scalar kernels'],check=True)
commit=git('rev-parse','HEAD');require(git('diff-tree','--no-commit-id','--name-only','-r',commit).splitlines()==names,'committed names')
for p in names:require(subprocess.check_output(['git','-C',str(R),'show',commit+':'+p])==(R/p).read_bytes(),'committed blob:'+p)
subprocess.run(['git','-C',str(R),'push','origin','HEAD:refs/heads/codex/simplex-core-architecture'],check=True)
require(set(git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture').splitlines())=={commit+'\trefs/heads/codex/simplex-core-architecture',MASTER+'\trefs/heads/master'},'remote verification')
require(git('rev-parse','master')==MASTER,'master changed')
print({'commit':commit,'master':MASTER,'exact_committed_blobs':len(names),'remote_verified':True},flush=True)
