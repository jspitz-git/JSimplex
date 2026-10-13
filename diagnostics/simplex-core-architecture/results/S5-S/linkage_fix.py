"""Exclusive second admission amendment: audit durable invocation linkage."""
from common_reviewed import *
assert not absent()['matches'];assert (H/'prelaunch-final-review.md').is_file()
for source,target in [('common_reviewed.py','common_final.py'),('launcher-reviewed.py','launcher-final.py'),('audit-reviewed.py','audit-final.py')]:
 s=(H/source).read_text()
 for a,b in [('common_reviewed','common_final'),('launcher-reviewed.py','launcher-final.py'),('audit-reviewed.py','audit-final.py'),('required-reviewed-paths.json','required-final-paths.json'),('admission-reviewed-pins.json','admission-final-pins.json'),('prelaunch-final-review.md','prelaunch-accepted-review.md')]:s=s.replace(a,b)
 if source=='audit-reviewed.py':
  needle="   'guard_invocation':read(H/'guard-invocation.json')['returncode']==0 and 'error' not in read(H/'guard-invocation.json'),"
  assert needle in s
  s=s.replace(needle,"   'guard_invocation':invocation_valid(process,sha(out/'pins.json')),")
  s=s.replace('def audit(out):', '''def invocation_valid(process,pin_hash):
 invocation=read(H/'guard-invocation.json');reservation=read(H/'attempt-reserved.json')
 log=read(H/'guard-output.log')
 expected=[sys.executable,str(G),'run',str(H/'launch-pins.json'),str(O),'--seconds','120','--',*command()]
 return (type(invocation.get('returncode')) is int and invocation['returncode']==0 and 'error' not in invocation
  and invocation.get('command')==expected and reservation.get('command')==command()
  and reservation.get('pins_sha256')==pin_hash and log==process
  and type(reservation.get('time_ns')) is int and type(invocation.get('started_ns')) is int and type(invocation.get('ended_ns')) is int
  and reservation['time_ns']<=invocation['started_ns']<=invocation['ended_ns']
  and invocation['host']['boot_id']==process['runner']['boot_id'] and invocation['host']['matches']==[])

def audit(out):''')
  s=s.replace("raw_sha256={str(p.relative_to(out)):sha(p) for p in out.iterdir() if p.is_file()},time_ns=", "invocation_sha256={str(H/n):sha(H/n) for n in ('guard-invocation.json','guard-output.log','attempt-reserved.json')},raw_sha256={str(p.relative_to(out)):sha(p) for p in out.iterdir() if p.is_file()},time_ns=")
 with (H/target).open('x') as f:f.write(s)
checks={'RED_unbound_returncode':"read(H/'guard-invocation.json')['returncode']==0" in (H/'audit-reviewed.py').read_text(),'GREEN_typed_returncode':"type(invocation.get('returncode')) is int" in s,'GREEN_log_process_identity':'log==process' in s,'GREEN_reservation_pin_identity':"reservation.get('pins_sha256')==pin_hash" in s,'GREEN_exact_invocation':"invocation.get('command')==expected" in s,'GREEN_record_hashes':'invocation_sha256=' in s}
dump(H/'linkage-fix.json',dict(checks=checks,all_passed=all(checks.values()),sha256={str(H/n):sha(H/n) for n in ('common_final.py','launcher-final.py','audit-final.py','linkage_fix.py','prelaunch-final-review.md')},scope='Second offline amendment; no candidate change or Julia.'));assert all(checks.values())
