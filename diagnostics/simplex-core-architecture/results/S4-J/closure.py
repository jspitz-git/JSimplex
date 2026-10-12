"""Exclusive S4-J closure; no Julia or accepted script execution."""
from pathlib import Path
import json,hashlib,subprocess,time
r=Path.cwd();d=r/'diagnostics/simplex-core-architecture';o=d/'results/S4-J'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
a=json.loads((o/'source-eligibility.json').read_text());ind=json.loads((o/'independent.json').read_text());pre=json.loads((d/'results/S4-I/preflight.json').read_text());matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  st=(p/'stat').read_text();v=st[st.rindex(')')+2:].split();exe=(p/'exe').resolve().name
  if int(p.name) in [8770,8771] or int(v[2]) in [8766,8771] or exe=='julia':matches.append({'pid':int(p.name),'pgid':int(v[2]),'start_ticks':v[19],'command':(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')})
 except (FileNotFoundError,PermissionError,ProcessLookupError):pass
review=d/'S4-REUSE-ELIGIBILITY-CONTRACT-REVIEW.md';status=d/'STATUS.md';plan=r/'docs/superpowers/plans/2026-10-12-hh-nonfinite-reuse-boundary.md'
checks={'all530hashes':len(a['hashes'])==530 and all(sha(k)==v for k,v in a['hashes'].items()),'27source_gates':len(a['checks'])==27 and a['all_passed'] and all(a['checks'].values()),'nine_independent_checks':len(ind['checks'])==9 and ind['all_passed'] and all(ind['checks'].values()),'independent_bound_artifacts':all(sha(o/k)==v for k,v in ind['artifact_hashes'].items()),'full_old_groups_noJulia':not matches,'source_test_CI_master':not subprocess.check_output(['git','diff','master','--','src','test','.github'],text=True),'user6_preserved':len(pre['user_hashes'])==6 and all(sha(k)==v for k,v in pre['user_hashes'].items()),'review_continuation_and_minor':all(p.is_file() for p in [review,status,plan]) and 'Minor DEFERRED' in review.read_text() and 'Before K launch, freeze the exact scaled residual formula' in status.read_text() and 'STOP immediately' in plan.read_text()}
artifacts=list(o.glob('*'))+[review,status,plan,d/'S4-REUSE-ELIGIBILITY-CONTRACT.md',r/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md']
result={'checks':checks,'all_passed':all(checks.values()),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'time_ns':time.time_ns(),'process_matches':matches,'refs':subprocess.check_output(['git','rev-parse','HEAD','master'],text=True).splitlines(),'artifact_hashes':{str(p):sha(p) for p in artifacts if p.is_file()},'scope':'new offline closure only; no launch, source/test/master/CI unchanged'}
with (o/'closure.json').open('x') as f:json.dump(result,f,indent=2)
print(checks);assert all(checks.values())
