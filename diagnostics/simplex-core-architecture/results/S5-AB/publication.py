"""Exclusive exact staged publication gate, after a separate successful closure."""
from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();H=Path(__file__).resolve().parent;D=H.parent.parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
d=json.loads((H/'closure.json').read_text());c={}
c['closure_pass']=d['all_passed'] is True and all(x is True for x in d['checks'].values())
c['closure_bindings']=all(sha(Path(p).read_bytes())==v for p,v in d['sha256'].items())
c['refs_unchanged']=all(git('-C',p,'rev-parse','HEAD')==v for p,v in d['refs'].items())
c['authored_diff_clean']=subprocess.run(['git','diff','--cached','--check'],capture_output=True).returncode==0
base=[D/'S5-HANDOFF-COVERAGE-RECONCILIATION.md',D/'S5-HANDOFF-COVERAGE-RECONCILIATION-REVIEW.md',D/'STATUS.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md',R/'docs/superpowers/plans/2026-10-13-cleanup-entry-reuse-design-decision.md']
expected={str(p.relative_to(R)) for p in base+list(H.rglob('*')) if p.is_file()};staged=set(git('diff','--cached','--name-only').splitlines());c['complete_expected_staging']=staged==expected
c['only_diagnostic_paths']=all(p.startswith('diagnostics/simplex-core-architecture/') or p in [str(x.relative_to(R)) for x in base] for p in staged)
assert all(c.values()),c
with (H/'publication-check.json').open('x') as f:json.dump(dict(checks=c,all_passed=True,closure_sha256=sha((H/'closure.json').read_bytes())),f,indent=2);f.write('\n')
subprocess.run(['git','add','--',str((H/'publication-check.json').relative_to(R))],check=True)
rows={};blobs={}
for p in git('diff','--cached','--name-only').splitlines():
 blob=subprocess.check_output(['git','show',':'+p]);assert blob==(R/p).read_bytes(),p;rows[p]=sha(blob);blobs[p]=git('rev-parse',':'+p)
with (H/'staged-files.json').open('x') as f:json.dump(dict(sha256=rows,git_blobs=blobs),f,indent=2);f.write('\n')
rel=str((H/'staged-files.json').relative_to(R));subprocess.run(['git','add','--',rel],check=True)
actual=set(git('diff','--cached','--name-only').splitlines());assert actual==set(rows)|{rel};assert subprocess.check_output(['git','show',':'+rel])==(H/'staged-files.json').read_bytes()
subprocess.run(['git','diff','--cached','--check'],check=True)
print(json.dumps(dict(checks=c,exact_staged_files=len(actual),listed_blobs=len(rows))))
