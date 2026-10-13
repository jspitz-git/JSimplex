"""Separate offline invocation linkage rejection tests, zero Julia."""
import common as c
import copy
p={'runner':{'boot_id':'synthetic'},'reason':'exit0'}
inv=dict(returncode=0,command=c.guard_command(),started_ns=2,ended_ns=3,host=dict(boot_id='synthetic',matches=[]))
res=dict(command=c.command(),pins_sha256='pins',output=str(c.B),launch_binding_sha256='binding',time_ns=1)
saved=c.sha;c.sha=lambda path:'binding'
try:
 checks={'synthetic_control':c.invocation_ok(inv,res,p,p,'pins')}
 for name,where,key,value in [('wrong_command','inv','command',[]),('bad_exit','inv','returncode',1),('wrong_output','res','output','/tmp/wrong'),('wrong_pin','res','pins_sha256','wrong'),('wrong_reservation_command','res','command',[]),('wrong_launch_binding','res','launch_binding_sha256','wrong'),('late_reservation','res','time_ns',4),('wrong_log','log','reason','different')]:
  i=copy.deepcopy(inv);r=copy.deepcopy(res);log=copy.deepcopy(p);{'inv':i,'res':r,'log':log}[where][key]=value
  checks[name]=not c.invocation_ok(i,r,log,p,'pins')
finally:c.sha=saved
c.dump(c.H/'link-tests.json',dict(checks=checks,all_passed=all(checks.values()),scope='Synthetic path/time/hash/log linkage only, no runtime operation.'))
print(checks);assert all(checks.values())
