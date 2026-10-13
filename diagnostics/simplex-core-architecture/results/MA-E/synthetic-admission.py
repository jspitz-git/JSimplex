import sys
sys.dont_write_bytecode=True
from control import *
from guard import pressure,limits
from copy import deepcopy
checks={}
def check(n,v):checks[n]=bool(v)
p=str(D/'control.py');h='a'*64;inv=dict(files=[p],trees=[],inputs=[],inventory={p:dict(sha256=h,resolved=str(Path(p).resolve()))})
check('manifest_positive',inventory_ok(inv,{p:h},lambda _:h))
for n,mut in [('missing_required',lambda x:x['inventory'].clear()),('wrong_hash',lambda x:x['inventory'][p].update(sha256='b'*64)),('tree_escape',lambda x:x['trees'].append('/tmp')),('input',lambda x:x['inputs'].append('/tmp')),('resolved',lambda x:x['inventory'][p].update(resolved='/tmp/foreign')),('membership',lambda x:x['files'].clear())]:
 x=deepcopy(inv);mut(x);check('manifest_reject_'+n,not inventory_ok(x,{p:h},lambda _:h))
names=('admission-pins.json','required-paths.json','review.json','review.md','driver.jl','kernels.jl','auditor.py','control.py','guard.py','launcher.py','seal.py','admission.md')
a=dict(accepted=True,stage='MA-F-attempt-1',attempts=1,refs={'r':'head'},pin_sha256=h,commands=[command(s) for s in STAGES],output=str(OUT),sha256={str(D/n):h for n in names})
check('seal_positive',seal_ok(a,{'r':'head'},h,lambda _:h))
for n,mut in [('approval',lambda x:x.update(accepted=False)),('attempt',lambda x:x.update(attempts=2)),('stage',lambda x:x.update(stage='other')),('refs',lambda x:x.update(refs={})),('pin',lambda x:x.update(pin_sha256='bad')),('command',lambda x:x['commands'].pop()),('output',lambda x:x.update(output='/tmp/other')),('membership',lambda x:x['sha256'].pop(str(D/'guard.py'))),('inputhash',lambda x:x['sha256'].update({str(D/'guard.py'):'bad'}))]:
 x=deepcopy(a);mut(x);check('seal_reject_'+n,not seal_ok(x,{'r':'head'},h,lambda _:h))
check('resource_ok',not pressure(dict(available_kib=6*1024**2,swap_used_kib=1024**2)))
check('resource_RAM',pressure(dict(available_kib=6*1024**2-1,swap_used_kib=0)))
check('resource_swap',pressure(dict(available_kib=7*1024**2,swap_used_kib=1024**2+1)))
s=(D/'guard.py').read_text();check('session_cleanup_source',"int(fields[3]) == pgid" in s);check('prelaunch_deadline_source',"min(args.deadline, started + args.seconds)" in s)
check('guard_VM_source','resource.RLIMIT_AS, (8 * 1024**3, 8 * 1024**3)' in s)
check('fixed_thread_flags',all(k in command(STAGES[0]) for k in ('--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--compiled-modules=existing')))
save(D/'synthetic-admission.json',dict(all_passed=all(checks.values()),checks=checks,scope='new pure admission helper tests; resource/session/deadline code checks are not runtime kill/namespace proof'))
print(sum(checks.values()),'/',len(checks))
if not all(checks.values()):raise SystemExit(1)
