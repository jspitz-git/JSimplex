"""Independent author postexit source/input/pin/guard check; exclusive output."""
from pathlib import Path
from fractions import Fraction as Q
import json,tomllib,hashlib,struct,subprocess,time
r=Path.cwd();d=r/'diagnostics/simplex-core-architecture';o=d/'results/S4-M';raw=r/'.superpowers/simplex-core-architecture/S4-M/cost-1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();pins=json.loads((o/'cost-1-pins.json').read_text());audit=json.loads((o/'cost-1-audit.json').read_text());a=tomllib.loads((o/'cost-1-report.toml').read_text());inputs=tomllib.loads((o/'inputs.toml').read_text());checks={}
checks['full554']=len(pins['inventory'])==554 and all(sha(p)==h['sha256'] for p,h in pins['inventory'].items());checks['raw4']=all(sha(raw/n)==sha(o/('cost-1-'+n)) for n in ['report.toml','process.json','run.log','resources.jsonl']);checks['audit_bound']=audit['report_sha256']==sha(raw/'report.toml') and audit['auditor_postexit_sha256']==sha(d/'reproduce/hh_symbolic_cost_audit.py') and audit['auditor_not_launch_pin'];checks['all24gates']=len(audit['checks'])==24 and all(audit['checks'].values());checks['no_production_change']=not subprocess.check_output(['git','diff','master','--','src','test','.github'])
floatq=lambda b:Q.from_float(struct.unpack('>d',bytes.fromhex(b))[0]);input_count=0
for key,v in inputs.items():
 kind=key[:-1];p=int(key[-1]);M=[[Q(8)+Q(i%7,64)+Q(p,8) if i==j else Q((-1)**(i+j)*(8+p),8192) if kind=='dense' or abs(i-j)<=2 else Q(0) for j in range(1,97)] for i in range(1,97)]
 vals=[];rows=[];ptr=[1]
 for j in range(96):
  for i in range(96):
   if M[i][j]:vals.append(M[i][j]);rows.append(i+1)
  ptr.append(len(vals)+1)
 assert vals==list(map(floatq,v['nzval_bits'])) and rows==v['rowval'] and ptr==v['colptr'];input_count+=len(vals)
 for name,z in [('rhs_forward_bits',[(-1)**i for i in range(1,97)]),('rhs_transpose_bits',[i%3-1 for i in range(1,97)])]:
  expected=[sum(c*x for c,x in zip(row,z)) for row in M];assert expected==list(map(floatq,v[name]));input_count+=96
checks['all_inputs_and_RHS_rebuilt']=input_count==20148
resources=[json.loads(s) for s in (raw/'resources.jsonl').read_text().splitlines()];checks['resource_guard']=all(v['available_kib']>=6*1024**2 and v['swap_used_kib']<=1024**2 for v in resources)
process=json.loads((raw/'process.json').read_text());groups={process['runner']['pgid'],process['child']['pgid']};matches=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  s=(p/'stat').read_text();v=s[s.rindex(')')+2:].split()
  if int(v[2]) in groups or (p/'exe').resolve().name=='julia':matches.append({'pid':int(p.name),'pgid':v[2],'start_ticks':v[19]})
 except (OSError,ValueError):pass
checks['groups_absent']=not matches;pre=json.loads((o/'preflight.json').read_text());checks['user6']=all(sha(p)==h for p,h in pre['user_hashes'].items());checks['actual_refs']=subprocess.check_output(['git','rev-parse','HEAD','master'],text=True).splitlines()==[pre['head'],pre['master']]
x={'checks':checks,'all_passed':all(checks.values()),'input_coefficients_and_RHS_checked':input_count,'resource_samples':len(resources),'minimum_available_kib':min(v['available_kib'] for v in resources),'maximum_swap_kib':max(v['swap_used_kib'] for v in resources),'matches':matches,'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'time_ns':time.time_ns(),'author_full_pin_check_not_reviewer_sample':True}
with (o/'independent.json').open('x') as f:json.dump(x,f,indent=2)
print(x);assert x['all_passed']
