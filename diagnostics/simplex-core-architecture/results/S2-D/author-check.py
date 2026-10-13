from pathlib import Path
import json,hashlib
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/S2-D'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
o=json.loads((D/'admission-pins.json').read_text());req=json.loads((D/'required-paths.json').read_text())
checks={'full780':len(o['inventory'])==780 and all(sha(Path(p))==v['sha256'] for p,v in o['inventory'].items()),'required_exact_membership':set(o['inventory'])==set(req)|{str(D/'required-paths.json')},'source16':json.loads((D/'source-check.json').read_text())['all_passed'],'synthetic25':json.loads((D/'failure-tests.json').read_text())['all_passed'],'no_python_bytecache':not list(D.rglob('__pycache__')),'no_numerical_allowance':not (D/'allowance.json').exists() and not (D/'launch-pins.json').exists()}
files=[D/n for n in ['author-check.py','admission-pins.json','required-paths.json','source-check.py','source-check.json']]+[R/'diagnostics/simplex-core-architecture/S2-PRICE-AUDIT-ADMISSION-PREPARATION.md']
with (D/'author-check.json').open('x') as f:json.dump({'checks':checks,'all_passed':all(checks.values()),'sha256':{str(p):sha(p) for p in files}},f,indent=2);f.write('\n')
print(checks);assert all(checks.values())
