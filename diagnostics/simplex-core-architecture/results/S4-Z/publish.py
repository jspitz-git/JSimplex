"""One-use S4-Z OFFLINE closure and failfast publication after fresh review."""
from common import *
BASE='23ac555994fc13d1f85fb8a2cff02e6958a0df22';MASTER='d02416c108f06fcd41d58e0a1980b70a51fef9ef'
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
status='diagnostics/simplex-core-architecture/STATUS.md';roadmap='docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
report='diagnostics/simplex-core-architecture/S4-MARKOWITZ-RETENTION-ADMISSION.md'
review='diagnostics/simplex-core-architecture/S4-MARKOWITZ-RETENTION-ADMISSION-REVIEW.md'
plan='docs/superpowers/plans/2026-10-13-markowitz-retention-qualification.md'
EXPECTED={'STATUS.md.before-S4-Z','roadmap.md.before-S4-Z','host.json','continuation-map.json','common.py','launcher.py','audit.py','guard.py','synthetic.py','synthetic.json','prepare.py','command.json','entry.json','admission.md','required-paths.json','admission-pins.json','final-review.md','review.json','publish.py','pre-publication-host.json'}
require({p.name for p in D.iterdir()}==EXPECTED,'exact evidence whitelist')
require(all((D/n).is_file() for n in EXPECTED),'evidence files')
require(git('rev-parse','HEAD')==BASE and git('rev-parse','master')==MASTER,'refs')
require(not git('diff','--cached','--name-only'),'index')
require(set(git('diff','--name-only').splitlines())=={status,roadmap},'tracked scope')
require(not git('diff','master','--','src','test','.github'),'source/test/CI')
pins=read(D/'admission-pins.json');required=read(D/'required-paths.json')
require(manifest_ok(pins,required),'all admission hashes')
require(sha(D/'required-paths.json')==pins['inventory'][str(D/'required-paths.json')]['sha256'],'required list binding')
for name in ('entry.json','synthetic.json'):
 x=read(D/name);require(x['all_passed'] is True and all(v is True for v in x['checks'].values()),name)
rev=read(D/'review.json');require(rev['all_passed'] is True and rev['unresolved_findings']==[] and all(v is True for v in rev['checks'].values()),'review')
require('S4-Z ACCEPTED' in (D/'final-review.md').read_text() and (R/review).read_bytes()==(D/'final-review.md').read_bytes(),'review text')
for p,h in rev['sha256'].items():require(sha(R/p)==h,'review binding:'+p)
host=read(D/'pre-publication-host.json');require(host['head']==BASE and host['master']==MASTER and set(host['groups'])==GROUPS and not host['matches'],'fresh host')
require(not OUT.exists() and not any((D/n).exists() for n in ('allowance.json','attempt-reserved.json','launch-pins.json','numerical-review.md','launcher.log','invocation.json','audit.json')),'no launch/allowance')
files=sorted([status,roadmap,report,review,plan]+[str((D/n).relative_to(R)) for n in EXPECTED])
require(set(git('ls-files','--others','--exclude-standard').splitlines())==set(files)-{status,roadmap}|{'Manifest.toml','LocalPreferences.toml'},'untracked completeness')
checks=dict.fromkeys(['exact_evidence_scope','refs_index_tracked_scope','unchanged_production_test_CI','full_admission_hashes','required_list_bound','entry_and_synthetics_passed','independent_review_accepted','review_hashes','fresh_full28groups_sessions_noJulia','no_allowance_reservation_output','exact_untracked_scope'],True)
dump(D/'closure.json',{'checks':checks,'all_passed':True,'sha256':{p:sha(R/p) for p in files},'previous_Y_mapping':read(D/'continuation-map.json')})
files.append(str((D/'closure.json').relative_to(R)));pub=str((D/'publication.json').relative_to(R));names=sorted(files+[pub])
dump(D/'publication.json',{'checks':{'closure_passed':True,'fixed_complete_names':True},'all_passed':True,'expected_staged_names':names,'sha256':{p:sha(R/p) for p in files},'self_exclusion':'Own recursive hash excluded; actual staged/committed bytes checked separately.'})
subprocess.run(['git','add','--',*names],check=True)
require(git('diff','--cached','--name-only').splitlines()==names,'staged names')
for p in names:require(subprocess.check_output(['git','show',':'+p])==(R/p).read_bytes(),'staged blob:'+p)
subprocess.run(['git','diff','--cached','--check','--',*[p for p in names if not p.endswith('.before-S4-Z')]],check=True)
require(set(git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture').splitlines())=={MASTER+'\trefs/heads/master',BASE+'\trefs/heads/codex/simplex-core-architecture'},'remote refs')
print(json.dumps({'closure':len(checks),'staged_names_blobs':len(names),'all_passed':True}),flush=True)
subprocess.run(['git','commit','-m','docs: prepare guarded Markowitz retention admission'],check=True)
commit=git('rev-parse','HEAD');require(git('diff-tree','--no-commit-id','--name-only','-r',commit).splitlines()==names,'committed names')
for p in names:require(subprocess.check_output(['git','show',commit+':'+p])==(R/p).read_bytes(),'committed blob:'+p)
subprocess.run(['git','push','origin','HEAD:refs/heads/codex/simplex-core-architecture'],check=True)
require(set(git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture').splitlines())=={MASTER+'\trefs/heads/master',commit+'\trefs/heads/codex/simplex-core-architecture'},'remote verification')
require(git('rev-parse','master')==MASTER,'master changed')
print(json.dumps({'commit':commit,'master':MASTER,'exact_committed_blobs':len(names),'remote_verified':True}),flush=True)
