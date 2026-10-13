"""Exclusive publication validation after separate PASS closure and staging."""
from pathlib import Path
import hashlib,json,subprocess,time
R=Path.cwd();H=Path(__file__).resolve().parent;D=H.parent.parent
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
c=read(H/'closure.json');staged=set(subprocess.check_output(['git','diff','--cached','--name-only'],text=True).splitlines());allowed={str(p.relative_to(R)) for p in H.rglob('*') if p.is_file()}|{str((D/x).relative_to(R)) for x in ('STATUS.md','S5-BASIS-INITIALIZATION-STOP-TEST-PREPARATION.md','S5-BASIS-INITIALIZATION-STOP-TEST-PREPARATION-REVIEW.md')}|{'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md','docs/superpowers/plans/2026-10-13-basis-initialization-stop-test-integration.md'}
diff=subprocess.run(['git','diff','--cached','--check'],capture_output=True,text=True)
checks={'closure14':len(c['checks'])==14 and c['all_passed'] is True and all(v is True for v in c['checks'].values()),'closure_bindings':all(sha(k)==v for k,v in c['sha256'].items()),'complete_staged_scope':staged==allowed,'user6':all(sha(k)==v for k,v in read(H/'host-before.json')['user_hashes'].items()),'branch':subprocess.check_output(['git','branch','--show-current'],text=True).strip()=='codex/simplex-core-architecture','diff_clean':diff.returncode==0}
o=dict(checks=checks,all_passed=all(checks.values()),closure_sha256=sha(H/'closure.json'),diff_check=dict(returncode=diff.returncode,stdout=diff.stdout,stderr=diff.stderr),time_ns=time.time_ns())
with (H/'publication-check.json').open('x') as f:json.dump(o,f,indent=2);f.write('\n')
print(json.dumps(o));raise SystemExit(0 if o['all_passed'] else 1)
