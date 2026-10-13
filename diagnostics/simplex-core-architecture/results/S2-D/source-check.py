from pathlib import Path
import json,hashlib,subprocess,tomllib,struct
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/S2-D';C=D.parent/'S2-C'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
pins=json.loads((D/'admission-pins.json').read_text());mapping=json.loads((D/'overlay-map.json').read_text());spec=tomllib.loads((D/'fixtures.toml').read_text())
source=(C/'original-primal-updates.jl').read_text();ref=(D/'reference-audit.jl').read_text();inverse=ref.replace('s2d_reference_price_audit','_primal_price_prediction_reliable').replace('JSimplex.','')
fixture_checks=[]
for f in spec['fixtures']:
 m,n=f['m'],f['n'];fmt='f' if f['scalar']=='Float32' else 'd';rows=[];ptr=[1];vals=[]
 for j in range(1,n+1):
  for i in range(1,m+1):
   if f['density']=='sparse' and not (i==(j-1)%m+1 or i==j%m+1 or (i+3*j)%17==0):continue
   v=((3*i+5*j)%17-8)/16
   if v:rows.append(i);vals.append(v)
  ptr.append(len(rows)+1)
 fixture_checks.append(rows==f['rowval'] and ptr==f['colptr'] and [struct.pack('>'+fmt,v).hex() for v in vals]==f['nzval_bits'] and [struct.pack('>'+fmt,1+(j%7)/8).hex() for j in range(1,n+1)]==f['cost_bits'] and hashlib.sha256(b''.join(struct.pack('<'+fmt,v) for v in vals)).hexdigest()==f['nzval_sha256'])
checks={'full780pins':len(pins['inventory'])==780 and all(sha(Path(p))==v['sha256'] and str(Path(p).resolve(strict=True))==v['resolved'] for p,v in pins['inventory'].items()),'overlay73exact':len(mapping)==73 and all(sha(D/'overlay'/p)==v['sha256']==sha(Path(v['origin'])) for p,v in mapping.items()),'source_one_change':sum((D/'overlay'/p).read_bytes()!=(R/p).read_bytes() for p in mapping)==1,'candidate_C_exact':sha(D/'overlay/src/primal_updates.jl')==sha(C/'candidate-primal-updates.jl'),'reference_inverse':source.endswith(inverse),'eight_exact_fixtures':len(fixture_checks)==8 and all(fixture_checks),'call_schedule':spec['warm_pairs']==4 and spec['measured_pairs']==8 and spec['calls_per_window']==16 and 8*12*2*16==3072,'no_allowance_or_output':not (D/'allowance.json').exists() and not (D/'launch-pins.json').exists() and not (R/'.superpowers/simplex-core-architecture/S2-D/qualification-1').exists(),'frozen_tests_direct_include':'include(joinpath(C,"candidate-tests.jl"))' in (D/'driver.jl').read_text(),'loaded_source_assertions':'realpath(pathof(JSimplex))' in (D/'driver.jl').read_text(),'new_guard_exact_AA':sha(D/'guard.py')==sha(D.parent/'S5-AA/guard.py'),'synthetic25':json.loads((D/'failure-tests.json').read_text())['all_passed'],'ordinary_manifest_dot':'path = "."' in (D/'overlay/Manifest.toml').read_text(),'actual_src_test_ci_unchanged':not subprocess.check_output(['git','diff','--name-only','master','--','src','test','.github','Project.toml'],text=True).strip(),'no_tracked_edit_yet':not subprocess.check_output(['git','diff','--name-only'],text=True).strip(),'Cclosure35_current':all(sha(Path(p))==h for p,h in json.loads((C/'closure-final.json').read_text())['sha256'].items())}
with (D/'source-check.json').open('x') as f:json.dump({'checks':checks,'all_passed':all(checks.values()),'scope':'offline text, bit inputs and hash verification; not Julia parse/runtime acceptance','sha256':{str(p):sha(p) for p in [D/'source-check.py',D/'admission-pins.json',D/'required-paths.json']}},f,indent=2);f.write('\n')
print(checks);assert all(checks.values())
