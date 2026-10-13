"""Single-use closure/publication for S3-G; run only after accepted review."""
from pathlib import Path
import hashlib,json,subprocess
R=Path.cwd(); D=R/'diagnostics/simplex-core-architecture/results/S3-G'
BASE='7ddea1bba37e2783871b5d947e261554de88a856'; MASTER='d02416c108f06fcd41d58e0a1980b70a51fef9ef'
def git(*args): return subprocess.check_output(['git',*args],text=True).strip()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def need(ok,msg):
 if not ok: raise RuntimeError(msg)
def write(name,data):
 with (D/name).open('x') as f: json.dump(data,f,indent=2); f.write('\n')
status=Path('diagnostics/simplex-core-architecture/STATUS.md'); roadmap=Path('docs/superpowers/plans/2026-10-11-simplex-core-architecture.md')
report=Path('diagnostics/simplex-core-architecture/S3-RATIONAL-PRIMAL-SUPPORT-ADMISSION.md'); review=Path('diagnostics/simplex-core-architecture/S3-RATIONAL-PRIMAL-SUPPORT-ADMISSION-REVIEW.md'); plan=Path('docs/superpowers/plans/2026-10-13-rational-primal-support-admission.md')
need(git('rev-parse','HEAD')==BASE,'HEAD changed'); need(git('rev-parse','master')==MASTER,'master changed')
need(not git('diff','--cached','--name-only'),'index not empty')
need('S3-G ACCEPTED' in review.read_text(),'review not accepted')
evidence=json.loads((D/'source.json').read_text())
need(evidence['all_passed'] and all(evidence['checks'].values()),'source gates failed')
for p,h in evidence['sha256'].items(): need(sha(R/p)==h,'source binding changed: '+p)
for old in evidence['previous_continuation_hashes'].values():
 for p,h in old.items():
  saved='STATUS.md.before-S3-G' if p==str(status) else 'roadmap.md.before-S3-G'
  need(sha(D/saved)==h,'old continuation binding lost')
need(not git('diff','master','--','src','test','.github'),'production change')
need(set(git('diff','--name-only').splitlines())=={str(status),str(roadmap)},'unexpected tracked modification')
need(not json.loads((D/'pre-continuation-host.json').read_text())['matches'],'host not clear')
# Reviewer may bind source and author files with checkout-relative or absolute paths.
r=json.loads((D/'review.json').read_text())
need(r['all_passed'] and all(r['checks'].values()),'review checks failed')
for p,h in r['sha256'].items(): need(sha(R/p)==h,'review binding changed: '+p)
expected_evidence_names = {
    'STATUS.md.before-S3-G', 'roadmap.md.before-S3-G',
    'host.json', 'pre-continuation-host.json',
    'collect.py', 'source.json', 'review.json', 'publish.py',
}
need({p.name for p in D.iterdir()} == expected_evidence_names,
     'new evidence directory differs from reviewed explicit whitelist')
need(all((D/name).is_file() for name in expected_evidence_names),'non-file evidence member')
files=sorted([status,roadmap,report,review]+[(D/name).relative_to(R) for name in expected_evidence_names])
checks={'source_checks':True,'source_hashes':True,'independent_review':True,'review_bindings':True,'old_continuation_preserved':True,'production_test_ci_unchanged':True,'expected_refs':True,'host_groups_sessions_absent':True,'index_initially_empty':True,'tracked_changes_scoped':True}
write('closure.json',{'checks':checks,'all_passed':True,'sha256':{str(p):sha(R/p) for p in files},'mapping':{str(status):str((D/'STATUS.md.before-S3-G').relative_to(R)),str(roadmap):str((D/'roadmap.md.before-S3-G').relative_to(R))}})
files.append((D/'closure.json').relative_to(R)); pub=(D/'publication.json').relative_to(R)
names=sorted(str(p) for p in files+[pub])
write('publication.json',{'checks':{'closure_passed':True,'files_exist':all((R/p).is_file() for p in files)},'all_passed':True,'expected_staged_names':names,'sha256':{str(p):sha(R/p) for p in files},'self_exclusion':'Own recursive hash excluded; all actual staged blobs checked below before commit.'})
subprocess.run(['git','add','--',*names],check=True)
need(git('diff','--cached','--name-only').splitlines()==names,'staging names mismatch')
for p in names:
 b=subprocess.check_output(['git','show',':'+p]); need(b==(R/p).read_bytes(),'staged blob mismatch: '+p)
# Raw previous continuation copies retain their exact bytes; all other files must be whitespace clean.
authored=[p for p in names if not p.endswith('.before-S3-G')]
subprocess.run(['git','diff','--cached','--check','--',*authored],check=True)
remote=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture')
need(set(remote.splitlines())=={MASTER+'\trefs/heads/master',BASE+'\trefs/heads/codex/simplex-core-architecture'},'remote changed')
print(json.dumps({'closure_checks':len(checks),'publication_names':len(names),'all_staged_blobs_verified':True}),flush=True)
subprocess.run(['git','commit','-m','docs: close rational primal support admission decision'],check=True)
commit=git('rev-parse','HEAD'); need(git('diff-tree','--no-commit-id','--name-only','-r',commit).splitlines()==names,'committed names mismatch')
for p in names: need(subprocess.check_output(['git','show',commit+':'+p])==(R/p).read_bytes(),'committed blob mismatch: '+p)
subprocess.run(['git','push','origin','HEAD:refs/heads/codex/simplex-core-architecture'],check=True)
remote=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture')
need(set(remote.splitlines())=={MASTER+'\trefs/heads/master',commit+'\trefs/heads/codex/simplex-core-architecture'},'remote verification failed')
need(git('rev-parse','master')==MASTER,'local master changed')
print(json.dumps({'commit':commit,'master':MASTER,'committed_blobs':len(names),'remote_verified':True}),flush=True)
