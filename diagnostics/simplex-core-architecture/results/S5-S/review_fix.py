"""Exclusive offline correction of two admission findings; originals preserved."""
from common import *
import subprocess,sys
assert not absent()['matches']
assert (H/'prelaunch-review.md').is_file()
original=G.read_text()
needle='''                child = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,'''
new=original.replace(needle,'''                started = time.monotonic()
'''+needle)
new=new.replace("                started = time.monotonic()\n                record['reason'] = 'running'","                record['reason'] = 'running'")
needle2="""                if record['reason'] == 'running' and child_exited(child):
                    members = active_group_members(child.pid)"""
replacement="""                record['elapsed_including_launch'] = time.monotonic() - started
                if record['reason'] == 'running' and record['elapsed_including_launch'] > args.seconds:
                    record['reason'] = 'wall_time'
                if record['reason'] == 'running' and child_exited(child):
                    members = active_group_members(child.pid)"""
assert needle2 in new;new=new.replace(needle2,replacement)
(H/'guard-reviewed.py').write_text(new)
common=(H/'common.py').read_text().replace("G=R/'diagnostics/simplex-core-architecture/reproduce/guarded_run.py'","G=H/'guard-reviewed.py'")
for a,b in [('common.py','common_reviewed.py'),('launcher.py','launcher-reviewed.py'),('audit.py','audit-reviewed.py'),('required-paths.json','required-reviewed-paths.json'),('prelaunch-review.md','prelaunch-final-review.md'),('admission-pins.json','admission-reviewed-pins.json')]:common=common.replace(a,b)
(H/'common_reviewed.py').write_text(common)
launcher=(H/'launcher.py').read_text().replace('from common import *','from common_reviewed import *')
for a,b in [('required-paths.json','required-reviewed-paths.json'),('prelaunch-review.md','prelaunch-final-review.md'),('admission-pins.json','admission-reviewed-pins.json'),('launcher.py','launcher-reviewed.py')]:launcher=launcher.replace(a,b)
needle3=" raise SystemExit(subprocess.call([sys.executable,str(G),'run',str(pins),str(O),'--seconds','120','--',*command()],cwd=R))"
replace3=""" invocation=dict(command=[sys.executable,str(G),'run',str(pins),str(O),'--seconds','120','--',*command()],started_ns=time.time_ns(),host=absent(),returncode=None)
 try:
  with (H/'guard-output.log').open('x') as log:
   result=subprocess.run(invocation['command'],cwd=R,stdout=log,stderr=subprocess.STDOUT)
   invocation['returncode']=result.returncode
 except BaseException as error:
  invocation['error']=repr(error)
 finally:
  invocation['ended_ns']=time.time_ns()
  dump(H/'guard-invocation.json',invocation)
 raise SystemExit(0 if invocation['returncode']==0 and 'error' not in invocation else 1)"""
assert needle3 in launcher;launcher=launcher.replace(needle3,replace3);(H/'launcher-reviewed.py').write_text(launcher)
audit=(H/'audit.py').read_text().replace('from common import *','from common_reviewed import *')
audit=audit.replace("'process_exit0':process['reason']=='exit0'", "'elapsed_guard':type(process.get('elapsed_including_launch')) in (int,float) and 0<=process['elapsed_including_launch']<=120,\n   'guard_invocation':read(H/'guard-invocation.json')['returncode']==0 and 'error' not in read(H/'guard-invocation.json'),\n   'process_exit0':process['reason']=='exit0'")
(H/'audit-reviewed.py').write_text(audit)
checks={'RED_timer_after_launch':original.index('started = time.monotonic()',original.index('def run('))>original.index('child = subprocess.Popen'),'GREEN_timer_before_launch':new.index('started = time.monotonic()',new.index('def run('))<new.index('child = subprocess.Popen'),'GREEN_final_deadline_before_exit':new.index("record['elapsed_including_launch'] > args.seconds")<new.index("record['reason'] = f'exit{child.returncode}'"),'RED_guard_failure_unrecorded':'guard-invocation.json' not in (H/'launcher.py').read_text(),'GREEN_guard_failure_preserved':'finally:' in replace3 and "dump(H/'guard-invocation.json'" in replace3,'original_guard_unchanged':G.read_text()==original}
dump(H/'review-fix.json',dict(checks=checks,all_passed=all(checks.values()),sha256={str(p):sha(p) for p in [G,H/'review_fix.py',H/'guard-reviewed.py',H/'common_reviewed.py',H/'launcher-reviewed.py',H/'audit-reviewed.py',H/'prelaunch-review.md']},scope='Offline source RED/GREEN only; no Julia or old script execution.'));assert all(checks.values())
