"""S4-Y one-use failfast closure/publication; only after independent acceptance."""
from pathlib import Path
import hashlib,json,subprocess
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/S4-Y'
BASE='a679cceb9a924a85154e49610b2c162092a25cc1'
MASTER='d02416c108f06fcd41d58e0a1980b70a51fef9ef'
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(x,m):
 if not x:raise RuntimeError(m)
def read(n):return json.loads((D/n).read_text())
def write(n,v):
 with (D/n).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
status='diagnostics/simplex-core-architecture/STATUS.md'
roadmap='docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
report='diagnostics/simplex-core-architecture/S4-MARKOWITZ-RETENTION-PREPARATION.md'
review='diagnostics/simplex-core-architecture/S4-MARKOWITZ-RETENTION-PREPARATION-REVIEW.md'
plan='docs/superpowers/plans/2026-10-13-markowitz-retention-admission.md'
expected_evidence={
 'STATUS.md.before-S4-Y','roadmap.md.before-S4-Y','host.json','entry.json',
 'driver.jl','verify.py','source.json','historical-retention.json',
 'review-initial.md','report.before-review','plan.before-review',
 'STATUS.md.before-review','roadmap.md.before-review','driver-reviewed.jl',
 'fix.py','fix.json','publish.py','review.json','pre-publication-host.json'}
need({p.name for p in D.iterdir()}==expected_evidence,'unexpected/missing evidence')
need(all((D/n).is_file() for n in expected_evidence),'non-file evidence')
need(git('rev-parse','HEAD')==BASE and git('rev-parse','master')==MASTER,'refs')
need(not git('diff','--cached','--name-only'),'index not empty')
need(set(git('diff','--name-only').splitlines())=={status,roadmap},'tracked changes')
need(not git('diff','master','--','src','test','.github'),'production/test/CI changed')
entry=read('entry.json');source=read('source.json');fix=read('fix.json');rev=read('review.json')
need(source['all_passed'] and all(source['checks'].values()),'initial source checks')
need(fix['all_passed'] and all(fix['checks'].values()),'fix checks')
for p,h in source['sha256'].items():
 target=D/fix['initial_source_mapping'][p] if p in fix['initial_source_mapping'] else R/p
 need(sha(target)==h,'initial source binding: '+p)
for manifest in [fix,read('historical-retention.json')]:
 for p,h in manifest['sha256'].items():need(sha(R/p)==h,'final binding: '+p)
for p,h in entry['user_sha256'].items():need(sha(Path(p))==h,'user changed: '+p)
for b in entry['previous_continuation_mapping'].values():need(sha(R/b['saved_path'])==b['sha256'],'G binding')
need(rev['all_passed'] and all(rev['checks'].values()) and rev['unresolved_findings']==[],'review gates')
need('S4-Y ACCEPTED' in (R/review).read_text(),'review not accepted')
for p,h in rev['sha256'].items():need(sha(R/p)==h,'review binding: '+p)
host=read('pre-publication-host.json')
need(host['head']==BASE and host['master']==MASTER and host['groups']==read('host.json')['groups'],'fresh host refs/groups')
need(not host['matching_groups_or_sessions'] and not host['julia'],'host processes')
files=sorted([status,roadmap,report,review,plan]+[str((D/n).relative_to(R)) for n in expected_evidence])
new_expected=set(files)-{status,roadmap}
need(set(git('ls-files','--others','--exclude-standard').splitlines())==new_expected|{'Manifest.toml','LocalPreferences.toml'},'untracked completeness')
checks={'source_and_fix_passed':True,'initial_and_final_bindings':True,'independent_review':True,'review_bindings':True,'six_G_bindings_preserved':True,'user_files_preserved':True,'production_test_ci_unchanged':True,'expected_refs':True,'fresh_full_groups_sessions_noJulia':True,'index_empty':True,'tracked_scope':True,'exact_evidence_and_untracked_scope':True}
write('closure.json',{'checks':checks,'all_passed':True,'sha256':{p:sha(R/p) for p in files},'previous_G_mapping':entry['previous_continuation_mapping'],'initial_Y_mapping':fix['initial_source_mapping']})
files.append(str((D/'closure.json').relative_to(R)));pub=str((D/'publication.json').relative_to(R));names=sorted(files+[pub])
write('publication.json',{'checks':{'closure_passed':True,'explicit_complete_names':True},'all_passed':True,'expected_staged_names':names,'sha256':{p:sha(R/p) for p in files},'self_exclusion':'Own recursive hash excluded; actual staged/committed bytes independently checked before/after commit.'})
subprocess.run(['git','add','--',*names],check=True)
need(git('diff','--cached','--name-only').splitlines()==names,'staged names')
for p in names:need(subprocess.check_output(['git','show',':'+p])==(R/p).read_bytes(),'staged blob: '+p)
authored=[p for p in names if not p.endswith(('.before-S4-Y','.before-review'))]
subprocess.run(['git','diff','--cached','--check','--',*authored],check=True)
expected_remote={MASTER+'\trefs/heads/master',BASE+'\trefs/heads/codex/simplex-core-architecture'}
need(set(git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture').splitlines())==expected_remote,'remote changed')
print(json.dumps({'closure_checks':len(checks),'exact_staged_names_blobs':len(names),'all_passed':True}),flush=True)
subprocess.run(['git','commit','-m','docs: prepare Markowitz shrink-history retention diagnostic'],check=True)
commit=git('rev-parse','HEAD')
need(git('diff-tree','--no-commit-id','--name-only','-r',commit).splitlines()==names,'committed names')
for p in names:need(subprocess.check_output(['git','show',commit+':'+p])==(R/p).read_bytes(),'committed blob: '+p)
subprocess.run(['git','push','origin','HEAD:refs/heads/codex/simplex-core-architecture'],check=True)
need(set(git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture').splitlines())=={MASTER+'\trefs/heads/master',commit+'\trefs/heads/codex/simplex-core-architecture'},'remote verification')
need(git('rev-parse','master')==MASTER,'master changed')
print(json.dumps({'commit':commit,'master':MASTER,'exact_committed_blobs':len(names),'remote_verified':True}),flush=True)
