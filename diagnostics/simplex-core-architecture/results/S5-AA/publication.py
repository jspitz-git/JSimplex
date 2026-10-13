"""Exclusive exact staged closure before failfast publication; no numerical work."""
from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();H=Path(__file__).resolve().parent;D=H.parent.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a])
closure=json.loads((H/'closure.json').read_text());c={}
c['closure23_pass']=len(closure['checks'])==23 and closure['all_passed'] is True and all(v is True for v in closure['checks'].values())
c['all_closure_bindings']=all(sha(k)==v for k,v in closure['sha256'].items())
c['refs_unchanged']=all(subprocess.check_output(['git','-C',k,'rev-parse','HEAD'],text=True).strip()==v for k,v in closure['refs'].items())
c['no_numerical_processes']=closure['host']['matches']==[] and len(closure['host']['groups'])==26
c['authored_whitespace_clean']=subprocess.run(['git','diff','--cached','--check'],capture_output=True).returncode==0
c['no_user_staging']=not any(x in git('diff','--cached','--name-only').decode().splitlines() for x in ['Manifest.toml','LocalPreferences.toml','.vscode/settings.json'])
assert all(c.values())
with (H/'publication-check.json').open('x') as f:json.dump(dict(checks=c,all_passed=True,closure_sha256=sha(H/'closure.json'),closure_bindings=len(closure['sha256'])),f,indent=2);f.write('\n')
subprocess.run(['git','add','--',str(H.relative_to(R))],check=True)
expected={str(p.relative_to(R)) for p in H.rglob('*') if p.is_file()}|{str(p.relative_to(R)) for p in [D/'STATUS.md',D/'S5-CRASH-FALLBACK-OBSERVER-TEST-INTEGRATION.md',D/'S5-CRASH-FALLBACK-OBSERVER-TEST-INTEGRATION-REVIEW.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md',R/'docs/superpowers/plans/2026-10-13-handoff-coverage-reconciliation.md']}
staged=set(git('diff','--cached','--name-only').decode().splitlines());assert staged==expected,(staged^expected)
bindings={k:sha(R/k) for k in sorted(staged)}
assert all(hashlib.sha256(git('show',':'+k)).hexdigest()==v for k,v in bindings.items())
manifest=H/'staged-files.json'
with manifest.open('x') as f:json.dump(dict(sha256=bindings,scope='Exact complete staged names and index blobs, excluding only this self manifest; independently verified before commit.'),f,indent=2);f.write('\n')
subprocess.run(['git','add','--',str(manifest.relative_to(R))],check=True)
assert set(git('diff','--cached','--name-only').decode().splitlines())==expected|{str(manifest.relative_to(R))}
assert all(hashlib.sha256(git('show',':'+k)).hexdigest()==v for k,v in bindings.items()) and git('show',':'+str(manifest.relative_to(R)))==manifest.read_bytes()
subprocess.run(['git','diff','--cached','--check'],check=True)
print('Publication',len(c),'PASS; closure bindings',len(closure['sha256']),'; exact',len(expected)+1,'staged files/blobs verified BEFORE commit.')
