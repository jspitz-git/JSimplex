"""Exclusive S4-K final closure; no Julia/accepted script execution."""
from pathlib import Path
import json,hashlib,subprocess,time
r=Path.cwd();d=r/'diagnostics/simplex-core-architecture';o=d/'results/S4-K';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();pins=json.loads((o/'nonfinite-1-pins.json').read_text());a=json.loads((o/'nonfinite-1-audit.json').read_text());ind=json.loads((o/'independent.json').read_text());pre=json.loads((o/'preflight.json').read_text());p=json.loads((o/'nonfinite-1-process.json').read_text());groups=[p['runner']['pgid'],p['child']['pgid']];matches=[]
for f in Path('/proc').glob('[0-9]*'):
 try:
  s=(f/'stat').read_text();v=s[s.rindex(')')+2:].split()
  if int(v[2]) in groups or int(f.name) in [p['runner']['pid'],p['child']['pid']] or (f/'exe').resolve().name=='julia':matches.append({'pid':int(f.name),'pgid':int(v[2]),'start_ticks':v[19],'command':(f/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')})
 except OSError:pass
review=d/'S4-NONFINITE-REUSE-BOUNDARY-REVIEW.md';report=d/'S4-NONFINITE-REUSE-BOUNDARY.md';status=d/'STATUS.md';plan=r/'docs/superpowers/plans/2026-10-12-hh-symbolic-cost-contract.md'
checks={'full551pins':len(pins['inventory'])==551 and all(sha(k)==v['sha256'] and str(Path(k).resolve())==v['resolved'] for k,v in pins['inventory'].items()),'audit26':a['all_passed'] and len(a['checks'])==26 and all(a['checks'].values()),'independent9':ind['all_passed'] and len(ind['checks'])==9 and all(ind['checks'].values()),'postexit_auditor_hash':sha(d/'reproduce/hh_nonfinite_reuse_audit.py')==a['auditor_sha256'],'full_groups_noJulia':not matches,'source_test_CI_master':not subprocess.check_output(['git','diff','master','--','src','test','.github'],text=True),'user6':all(sha(k)==v for k,v in pre['user_hashes'].items()),'review_next_scope':review.is_file() and plan.is_file() and 'Current continuation: S4-K accepted' in status.read_text() and 'SOURCE/EVIDENCE ONLY' in plan.read_text()}
paths=[x for x in o.glob('*') if x.is_file()]+[review,report,status,plan,r/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md',d/'reproduce/hh_nonfinite_reuse_audit.py']
result={'checks':checks,'all_passed':all(checks.values()),'time_ns':time.time_ns(),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'process_matches':matches,'refs':subprocess.check_output(['git','rev-parse','HEAD','master'],text=True).splitlines(),'artifact_hashes':{str(x):sha(x) for x in paths if x.is_file()},'scope':'new author offline closure; original numerical/source/audit immutable'}
with (o/'closure.json').open('x') as f:json.dump(result,f,indent=2)
print(checks);assert all(checks.values())
