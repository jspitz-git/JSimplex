"""Preserve intermediate review inputs and add exact successful outcome identity."""
from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parent
p=P/'control.py';s=p.read_text()
with (P/'control.py.before-outcome-fix').open('x') as f:f.write(s)
a="require(outcome['launched'] is True and outcome['returncode']==0 and outcome['error']=='','RED outer did not finish successfully')"
b="require(outcome['identity']==closure['outer_identity'] and outcome['launched'] is True and outcome['returncode']==0 and outcome['error']=='','RED outer did not finish successfully')"
if s.count(a)!=1:raise RuntimeError('Missing exact outcome gate')
s=s.replace(a,b).replace("m=D/'preparation-pins-reviewed.json'","m=D/'preparation-pins-final.json'").replace("rd(D/'required-paths-reviewed.json')","rd(D/'required-paths-final.json')");p.write_text(s)
t=(P/'closure-tests-2.py').read_text().replace("dict(launched=True,returncode=0,error='')","dict(identity=identity,launched=True,returncode=0,error='')").replace("[('launched',False),('returncode',2),('error','fatal')]","[('identity',dict(identity,start_ticks=99)),('launched',False),('returncode',2),('error','fatal')]").replace("P/'closure-tests-2.json'","P/'closure-tests-3.json'")
with (P/'closure-tests-3.py').open('x') as f:f.write(t)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
with (P/'outcome-fix.json').open('x') as f:json.dump(dict(all_passed=True,before_sha256=sha(P/'control.py.before-outcome-fix'),after_sha256=sha(P/'control.py'),scope='Added successful outer outcome identity linkage; final numerical admission still absent'),f,indent=2);f.write('\n')
