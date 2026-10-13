from pathlib import Path
import json,hashlib
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/S2-D'
def put(n,s):
 with (D/n).open('x') as f:f.write(s)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
original={str(p):sha(p) for p in D.rglob('*') if p.is_file()}
review=json.loads((D/'reviewer-check.json').read_text())
# Original rejected artifacts and original780 inventory are never changed.
put('driver-reviewed.jl',(D/'driver.jl').read_text().replace('755','655'))
common=(D/'common.py').read_text()
for a,b in [('driver.jl','driver-reviewed.jl'),('launcher.py','launcher-reviewed.py'),('audit.py','audit-reviewed.py'),('common.py','common_reviewed.py'),('admission.md','admission-reviewed.md'),('required-paths.json','required-paths-reviewed.json'),('admission-pins.json','admission-pins-reviewed.json'),('review.md','final-review.md'),('reviewer-check.json','final-review-check.json')]:common=common.replace(a,b)
put('common_reviewed.py',common)
audit=(D/'audit.py').read_text().replace('from common import *','from common_reviewed import *').replace('755','655').replace('required-paths.json','required-paths-reviewed.json')
put('audit-reviewed.py',audit)
launcher=(D/'launcher.py').read_text().replace('from common import *','from common_reviewed import *')
for a,b in [('launcher.py','launcher-reviewed.py'),('required-paths.json','required-paths-reviewed.json'),('admission-pins.json','admission-pins-reviewed.json'),("'review.md'","'final-review.md'"),('reviewer-check.json','final-review-check.json')]:launcher=launcher.replace(a,b)
# Every assertion is replaced by an unconditional runtime gate, including semicolon gates.
lines=[]
for line in launcher.splitlines():
 if 'assert ' in line:
  indent=line[:len(line)-len(line.lstrip())]
  for part in line.strip().split(';'):
   part=part.strip()
   if part.startswith('assert '):lines.append(indent+'require('+part[7:]+', "admission gate rejected")')
   elif part:lines.append(indent+part)
 else:lines.append(line)
launcher='\n'.join(lines)+'\n'
launcher=launcher.replace('def main():','def require(condition,message):\n if not condition:raise ValueError(message)\ndef main():')
put('launcher-reviewed.py',launcher)
admission=(D/'admission.md').read_text().replace('total755','total655')
admission+='\nCanonical corrected files are driver-reviewed.jl, common_reviewed.py,\nlauncher-reviewed.py, audit-reviewed.py, required-paths-reviewed.json and\nadmission-pins-reviewed.json. Initial review.md is REJECTED and retained;\nfinal-review.md/final-review-check.json must accept this offline correction.\nAll pre-launch gates use explicit if/raise, independent of Python optimization.\nThe original755 aggregate was wrong: the unchanged seven children sum to655.\nNo Julia, launcher or guard was executed for this correction.\n'
put('admission-reviewed.md',admission)
report=R/'diagnostics/simplex-core-architecture/S2-PRICE-AUDIT-ADMISSION-PREPARATION.md'
put('report.before-review',report.read_text())
report.write_text(report.read_text().replace('expected755','expected655')+'\nInitial admission review rejected two Important errors: aggregate755 versus actual\nsource sum655, and assert-based pre-launch gates removable by Python optimization.\nThe original bundle780, checks and rejected review are preserved. Separate reviewed\nvariants correct the total and use explicit runtime gates; original author report\nhash maps only to results/S2-D/report.before-review. See admission-reviewed.md.\nThe original source16 and synthetic25 PASS records did not cover these errors.\n')
checks={'red_total_inconsistent':sum([90,40,416,34,16,31,28])!=755,'red_assert_gates_removable':'assert allowance_valid' in (D/'launcher.py').read_text(),'green_total655':sum([90,40,416,34,16,31,28])==655 and '755' not in (D/'driver-reviewed.jl').read_text() and '755' not in audit,'green_no_assert_gates':'assert ' not in launcher and 'if not condition:raise ValueError' in launcher,'original_files_preserved':all(sha(Path(p))==h for p,h in original.items())}
put('review-fix.json',json.dumps({'checks':checks,'all_passed':all(checks.values()),'sha256':{str(D/n):sha(D/n) for n in ['review-fix.py','driver-reviewed.jl','common_reviewed.py','launcher-reviewed.py','audit-reviewed.py','admission-reviewed.md','report.before-review']}},indent=2)+'\n')
print(checks)
if not all(checks.values()):raise SystemExit(1)
