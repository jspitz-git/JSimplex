"""New narrow supplement correcting reviewer comparison text; no original checker rerun."""
from pathlib import Path
import ast,hashlib,json
D=Path(__file__).resolve().parent
P=D.parent/'NATIVE-PIVOT-INTEGRATION-DRIVER-PREPARATION'
def rd(p):return json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
old=(D/'offline-tests.py').read_text();new=(D/'offline-tests-final.py').read_text()
needle="[5]=='52'";replacement="[6:8]==['--seconds','52']"
a=(D/'prepare.py').read_text();b=(D/'prepare-2.py').read_text()
needle2="DRIVER-PREPARATION'\nPREPARATION=DRIVER";replacement2="DRIVER-PREPARATION'\\nPREPARATION=DRIVER"
initial=rd(D/'independent-review-checks.json')
checks=dict(initial_197_other_checks_pass=len(initial['checks'])==198 and initial['findings']==['test_selector_only_correction'] and all(v for k,v in initial['checks'].items() if k!='test_selector_only_correction'),test_selector_exact_single_change=old.count(needle)==1 and old.replace(needle,replacement)==new,prepare_exact_single_escape_change=a.count(needle2)==1 and a.replace(needle2,replacement2)==b)
modules=['common.py','control.py','guard.py','supervisor.py','seal.py','launch.py','audit.py','oracle.py','prepare-2.py','offline-tests-final.py','finalize.py','publication.py','author-check.py','verify-publication.py']
for n in modules:ast.parse((D/n).read_text())
checks['python_source_parse_only']=True
m=rd(D/'preparation-pins.json')
checks['all_1561_pins_still_match']=len(m['sha256'])==1561 and all(sha(Path(n))==h for n,h in m['sha256'].items())
checks['baseline520_supplement_exact']=(D/'actual-baseline.json').read_bytes()==(P/'actual-baseline.json').read_bytes()
extra=set(m['sha256'])-set(rd(P/'preparation-pins.json')['sha256'])
record=dict(all_passed=all(checks.values()),checks=checks,resolution='Initial reviewer comparison assumed the wrong old selector string. Direct exact replacement of the actual preserved [5]==52 expression confirms the sole author test change. No author artifact changed; initial reviewer failure preserved.',new_inventory_files=len(extra),new_inventory_bytes=sum(Path(n).stat().st_size for n in extra),runtime='UNEXECUTED')
with (D/'independent-review-supplement.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print(record)
raise SystemExit(0 if record['all_passed'] else 1)
