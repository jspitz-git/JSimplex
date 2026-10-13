"""Exclusive author cross-check of offline Q artifacts."""
from pathlib import Path
import json,hashlib,subprocess,time
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture';Q=D/'results/S5-Q'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
e=json.loads((Q/'evidence.json').read_text());o=json.loads((Q/'oracle.json').read_text());host=json.loads((Q/'host-before.json').read_text());setup=(Q/'existing-setup.txt').read_text()
checks={'full178':len(e['sha256'])==178 and all(sha(p)==h for p,h in e['sha256'].items()),'checks18':len(e['checks'])==18 and all(v is True for v in e['checks'].values()),'exact_existing_setup':setup.rstrip('\n') in (R/'test/simplex_precision_tests.jl').read_text(),'one_selection':o['selection']['T']=='Float64' and o['selection']['update']=='pfi' and o['selection']['backend']=='native','nine_reference_roles':len(o['observation_cost']['roles'])==o['observation_cost']['reference_roles']==9,'copy_arithmetic':2*(2+4*4)==36 and 2+4==6,'user6':len(host['user_hashes'])==6 and all(sha(p)==h for p,h in host['user_hashes'].items()),'source_test_CI_equal':not subprocess.check_output(['git','diff','master','--','src','test','.github'])}
paths=[Path(__file__).resolve(),Q/'evidence.json',Q/'oracle.json',D/'S5-BASIS-INITIALIZATION-STOP-ORACLE.md',R/'docs/superpowers/plans/2026-10-13-basis-initialization-stop-preparation.md']
out=dict(all_passed=all(checks.values()),checks=checks,sha256={str(p):sha(p) for p in paths},time_ns=time.time_ns())
with (Q/'independent.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps(out));assert out['all_passed']
