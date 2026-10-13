from common import *
import copy
boot=absent()['boot_id'];p=dict(runner=dict(pid=1,pgid=1,start_ticks=10,boot_id=boot,command=' '.join(guard_command('green'))+' '),child=dict(pid=2,pgid=2,start_ticks=11,boot_id=boot,command=' '.join(command('green'))+' '),terminal_memory=dict(available_kib=6*1024**2,swap_used_kib=0))
c={'identity_positive':identities_ok(p,'green'),'terminal_memory_positive':terminal_memory_ok(p),'source_RED_missing_identity_gate':'process_identity=identities_ok' not in (H/'audit.py.before-identity-fix').read_text(),'source_GREEN_identity_gate':'process_identity=identities_ok' in (H/'audit.py').read_text(),'source_RED_missing_terminal_snapshot':"record['terminal_memory'] = memory()" not in (H/'guard.py.before-identity-fix').read_text(),'source_GREEN_terminal_snapshot':"record['terminal_memory'] = memory()" in (H/'guard.py').read_text()}
for who in ('runner','child'):
 for field in ('pid','pgid','start_ticks','command','boot_id'):
  x=copy.deepcopy(p);del x[who][field];c[who+'_missing_'+field]=not identities_ok(x,'green')
 for field,val in [('start_ticks',True),('command','wrong'),('boot_id','wrong')]:
  x=copy.deepcopy(p);x[who][field]=val;c[who+'_wrong_'+field]=not identities_ok(x,'green')
for n,m in [('missing',{}),('lowram',{'available_kib':1,'swap_used_kib':0}),('swap',{'available_kib':10**8,'swap_used_kib':2*1024**2}),('bool',{'available_kib':True,'swap_used_kib':0})]:c['terminal_'+n]=not terminal_memory_ok({'terminal_memory':m})
x=copy.deepcopy(p);x['child']['command']=' '.join([RUNTIME,'--startup-file=no',*command('green')[2:]])+' ';c['runtime_exec_command']=identities_ok(x,'green')
dump(H/'fix-tests.json',dict(checks=c,all_passed=all(c.values())));assert all(c.values());print(len(c),'fix tests PASS')
