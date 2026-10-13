"""Exclusive fail-fast publication gate, after separate closure."""
from pathlib import Path
import hashlib,json,subprocess,time
R=Path.cwd();O=R/'diagnostics/simplex-core-architecture/results/S5-R'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
c=json.loads((O/'closure.json').read_text());h=json.loads((O/'host-before.json').read_text())
allowed={'diagnostics/simplex-core-architecture/STATUS.md','diagnostics/simplex-core-architecture/S5-BASIS-INITIALIZATION-STOP-PREPARATION.md','diagnostics/simplex-core-architecture/S5-BASIS-INITIALIZATION-STOP-PREPARATION-REVIEW.md','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md','docs/superpowers/plans/2026-10-13-basis-initialization-stop-qualification.md'}
staged=subprocess.check_output(['git','diff','--cached','--name-only'],text=True).splitlines();diff=subprocess.run(['git','diff','--cached','--check'],capture_output=True,text=True)
checks={'closure14':len(c['checks'])==14 and c['all_passed'] is True and all(c['checks'].values()),'closure_bindings':all(sha(p)==v for p,v in c['sha256'].items()),'staged_scope':allowed.issubset(staged) and all(p in allowed or p.startswith('diagnostics/simplex-core-architecture/results/S5-R/') for p in staged),'user6':all(sha(p)==v for p,v in h['user_hashes'].items()),'branch':subprocess.check_output(['git','branch','--show-current'],text=True).strip()=='codex/simplex-core-architecture','diff_clean':diff.returncode==0}
out=dict(checks=checks,all_passed=all(checks.values()),closure_sha256=sha(O/'closure.json'),diff_check=dict(returncode=diff.returncode,stdout=diff.stdout,stderr=diff.stderr),time_ns=time.time_ns())
with (O/'publication-check.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps(checks));assert out['all_passed']
