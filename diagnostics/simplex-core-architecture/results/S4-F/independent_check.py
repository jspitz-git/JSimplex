"""Separate one-time offline verification of actual S4-F artifacts."""
from pathlib import Path
import json,tomllib,hashlib,struct,subprocess
root=Path.cwd();out=root/'diagnostics/simplex-core-architecture/results/S4-F';base=root/'.superpowers/simplex-core-architecture/S4-F/boundary-1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
r=tomllib.loads((out/'boundary-1-report.toml').read_text());pin=json.loads((out/'boundary-1-pins.json').read_text());pre=json.loads((out/'preflight.json').read_text());audit=json.loads((out/'boundary-1-audit.json').read_text())
bits=lambda v:[struct.pack('>d',float(x)).hex() for x in v]
starts=[[4,1,1,3],[1,3,2,4],[4,1,0,3],[4,1,1,3],[4,1,1,3],[4,1,1,3]]
targets=[[5,1,1,4],[2**-20,3,2,4],[4,1,2,3],[4,3],[2,3,4],[1,2,2,4]]
inputchecks=[]
for x in r['records']:
 i=x['case']-1;b0=x['B0'];b1=x['B1'];n=3 if i==4 else 2
 cp=[1,3,5] if i not in (3,4) else list(range(1,n+2));rv=[1,2,1,2] if i not in (3,4) else list(range(1,n+1))
 inputchecks.append(b0['bits']==bits(starts[i]) and b0['colptr']==[1,3,5] and b0['rowval']==[1,2,1,2] and b1['bits']==bits(targets[i]) and b1['colptr']==cp and b1['rowval']==rv and b1['m']==b1['n']==n)
checks={'full649_pin_rehash':len(pin['inventory'])==649 and all(sha(p)==v['sha256'] and str(Path(p).resolve())==v['resolved'] for p,v in pin['inventory'].items()),'raw_portable5_equal':all(sha(base/name)==sha(out/('boundary-1-'+name)) for name in ['report.toml','run.log','process.json','resources.jsonl']) and sha(base.parent/'boundary-1-pins.json')==sha(out/'boundary-1-pins.json'),'all12_exact_input_representations':all(inputchecks) and len(inputchecks)==12,'same_default_controls':len({tuple(x['controls_bits']) for x in r['records']})==1,'native13_library_hashes':len(pre['native_libraries'])==13 and all(sha(p)==h for p,h in pre['native_libraries'].items()),'driver_frozen_runtime_identity':pre['driver_sha256']==sha(out/'driver.jl.txt')==sha(root/'diagnostics/simplex-core-architecture/reproduce/hh_symbolic_boundary.jl'),'user6_preserved':len(pre['user_hashes'])==6 and all(sha(p)==h for p,h in pre['user_hashes'].items()),'all24_audit_gates':len(audit['checks'])==24 and audit['all_passed'] and all(audit['checks'].values()),'no_runtime_source_change':not subprocess.check_output(['git','diff','master','--','src','test','.github'],text=True),'launch_group_absent':not Path('/proc/3788').exists()}
with (out/'independent.json').open('x') as f:json.dump({'checks':checks,'all_passed':all(checks.values()),'input_representations':len(inputchecks),'scope':'author independent offline supplement; no numerical or exclusive auditor rerun'},f,indent=2)
print(checks);assert all(checks.values())
