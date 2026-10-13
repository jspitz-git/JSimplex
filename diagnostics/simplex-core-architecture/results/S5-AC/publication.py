"""Exclusive complete-stage gate after the separate S5-AC closure."""
from pathlib import Path
import hashlib,json,subprocess
R=Path.cwd();H=Path(__file__).resolve().parent;D=H.parent.parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],text=True).strip()
x=json.loads((H/'closure.json').read_text());c={}
c['separate_closure_pass']=x['all_passed'] is True and all(x['checks'].values())
c['closure_bindings']=all(sha(Path(p).read_bytes())==v for p,v in x['sha256'].items())
c['refs_preserved']=all(git('-C',p,'rev-parse','HEAD')==v for p,v in x['refs'].items())
c['diff_check']=subprocess.run(['git','diff','--cached','--check'],capture_output=True).returncode==0
base=[D/'STATUS.md',D/'S5-CLEANUP-ENTRY-REUSE-DECISION.md',D/'S5-CLEANUP-ENTRY-REUSE-DECISION-REVIEW.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md',R/'docs/superpowers/plans/2026-10-13-test-mps-failure-provenance.md']
expected={str(p.relative_to(R)) for p in base+list(H.rglob('*')) if p.is_file()};staged=set(git('diff','--cached','--name-only').splitlines());c['exact_complete_names']=staged==expected
c['diagnostic_only']=all(p.startswith('diagnostics/simplex-core-architecture/') or p in [str(x.relative_to(R)) for x in base] for p in staged)
assert all(c.values()),c
with (H/'publication-check.json').open('x') as f:json.dump(dict(checks=c,all_passed=True,closure_sha256=sha((H/'closure.json').read_bytes())),f,indent=2);f.write('\n')
subprocess.run(['git','add','--',str((H/'publication-check.json').relative_to(R))],check=True)
rows={};blobs={}
for p in git('diff','--cached','--name-only').splitlines():
 b=subprocess.check_output(['git','show',':'+p]);assert b==(R/p).read_bytes(),p;rows[p]=sha(b);blobs[p]=git('rev-parse',':'+p)
with (H/'staged-files.json').open('x') as f:json.dump(dict(sha256=rows,git_blobs=blobs),f,indent=2);f.write('\n')
p=str((H/'staged-files.json').relative_to(R));subprocess.run(['git','add','--',p],check=True)
assert set(git('diff','--cached','--name-only').splitlines())==set(rows)|{p}
assert subprocess.check_output(['git','show',':'+p])==(H/'staged-files.json').read_bytes()
subprocess.run(['git','diff','--cached','--check'],check=True)
print(json.dumps(dict(checks=c,exact_complete_staged=len(rows)+1,listed_blobs=len(rows))))
