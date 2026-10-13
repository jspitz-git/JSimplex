"""Exclusive author verification, no Julia or accepted-script reuse."""
from pathlib import Path
import json,hashlib,subprocess,time
R=Path.cwd();O=R/'diagnostics/simplex-core-architecture/results/S5-R'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
e=json.loads((O/'evidence.json').read_text());fix=json.loads((O/'field-fix.json').read_text());host=json.loads((O/'host-before.json').read_text());s=(O/'candidate-reviewed.jl').read_text()
checks={'full199':len(e['sha256'])==199 and all(sha(p)==v for p,v in e['sha256'].items()),'source19':len(e['checks'])==19 and all(v is True for v in e['checks'].values()),'fix4':len(fix['checks'])==4 and all(fix['checks'].values()) and all(sha(p)==v for p,v in fix['sha256'].items()),'candidate_hash':sha(O/'candidate-reviewed.jl')==e['candidate_sha256'],'forty_predicates':len(e['predicate_names'])==40,'fixed_cost':len(e['probe_fields'])==15 and s.count('copy(')==2 and 4+40+12+14+14==84,'user6':len(host['user_hashes'])==6 and all(sha(p)==v for p,v in host['user_hashes'].items()),'source_test_CI_equal':not subprocess.check_output(['git','diff','master','--','src','test','.github'])}
paths=[O/'independent.py',O/'evidence.json',O/'candidate-reviewed.jl',O/'field-fix.json',R/'diagnostics/simplex-core-architecture/S5-BASIS-INITIALIZATION-STOP-PREPARATION.md',R/'docs/superpowers/plans/2026-10-13-basis-initialization-stop-qualification.md']
out=dict(checks=checks,all_passed=all(checks.values()),sha256={str(p):sha(p) for p in paths},time_ns=time.time_ns())
with (O/'independent.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps(checks));assert out['all_passed']
