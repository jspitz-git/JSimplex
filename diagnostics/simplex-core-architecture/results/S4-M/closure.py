"""Exclusive S4-M closure after fresh review; never rerun numerical evidence."""
from pathlib import Path
import json,hashlib,subprocess,time
r=Path.cwd();d=r/'diagnostics/simplex-core-architecture';o=d/'results/S4-M';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();pins=json.loads((o/'cost-1-pins.json').read_text());a=json.loads((o/'cost-1-audit.json').read_text());pre=json.loads((o/'preflight.json').read_text());raw=r/'.superpowers/simplex-core-architecture/S4-M/cost-1';process=json.loads((raw/'process.json').read_text());groups={process['runner']['pgid'],process['child']['pgid']};checks={}
checks['all554pins']=len(pins['inventory'])==554 and all(sha(p)==v['sha256'] for p,v in pins['inventory'].items())
checks['raw4']=all(sha(raw/n)==sha(o/('cost-1-'+n)) for n in ['report.toml','run.log','process.json','resources.jsonl'])
checks['audit_and_independent']=a['all_passed'] and json.loads((o/'independent.json').read_text())['all_passed']
checks['auditor_postexit_bound']=sha(d/'reproduce/hh_symbolic_cost_audit.py')==a['auditor_postexit_sha256'] and str(d/'reproduce/hh_symbolic_cost_audit.py') not in pins['inventory']
checks['user6']=all(sha(p)==h for p,h in pre['user_hashes'].items())
checks['src_test_ci_unchanged']=not subprocess.check_output(['git','diff','master','--','src','test','.github'])
checks['review_and_continuation']=(d/'S4-SYMBOLIC-COST-MEASUREMENT-REVIEW.md').is_file() and 'next S4-N' in (d/'STATUS.md').read_text()
matches=[]
for q in Path('/proc').iterdir():
 if not q.name.isdigit():continue
 try:
  s=(q/'stat').read_text();v=s[s.rindex(')')+2:].split()
  if int(v[2]) in groups or (q/'exe').resolve().name=='julia':matches.append({'pid':int(q.name),'pgid':v[2],'start_ticks':v[19]})
 except (OSError,ValueError):pass
checks['full_groups_absent']=not matches
files=[p for p in o.iterdir() if p.is_file()]+[d/'S4-SYMBOLIC-COST-MEASUREMENT.md',d/'S4-SYMBOLIC-COST-MEASUREMENT-REVIEW.md',d/'STATUS.md',r/'docs/superpowers/plans/2026-10-12-hh-native-accounting-feasibility.md',r/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md']
x={'checks':checks,'all_passed':all(checks.values()),'hashes':{str(p):sha(p) for p in files},'matches':matches,'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'time_ns':time.time_ns()}
with (o/'closure.json').open('x') as f:json.dump(x,f,indent=2)
print({'checks':len(checks),'passed':sum(checks.values()),'hashes':len(files)});assert x['all_passed']
