"""Separate offline linkage and inventory refusal tests; no numerical command."""
import common as c
from pathlib import Path
import tempfile,copy
checks={}
def test(n,x):checks[n]=bool(x);assert checks[n],n
stage='green';h=c.stage_files(stage);command=c.guard_command(stage);p={'runner':{'boot_id':'boot'},'test':'terminal'}
res=dict(time_ns=1,command=c.command(stage),pins_sha256='pin',output=str(c.out(stage)),launch_binding_sha256='digest')
inv=dict(command=command,started_ns=2,ended_ns=3,returncode=0,host={'boot_id':'boot','matches':[]})
origread=c.read;origsha=c.sha
def valid(ii=inv,rr=res,ll=p):
 c.read=lambda path:{'guard-invocation.json':ii,'attempt-reserved.json':rr,'guard-output.log':ll}[Path(path).name];c.sha=lambda path:'digest'
 try:return c.invocation_valid(stage,p,'pin')
 finally:c.read=origread;c.sha=origsha
try:
 test('invocation_positive',valid())
 for n,patch in [('wrong_cmd',{'command':[]}),('nonzero',{'returncode':1}),('bool_exit',{'returncode':False}),('exception',{'error':'x'}),('badtime',{'started_ns':0}),('host_matches',{'host':{'boot_id':'boot','matches':[1]}}),('wrongboot',{'host':{'boot_id':'other','matches':[]}})]:test(n,not valid(ii={**inv,**patch}))
 for n,patch in [('reservation_cmd',{'command':[]}),('pin',{'pins_sha256':'other'}),('output',{'output':'other'}),('binding',{'launch_binding_sha256':'other'}),('time',{'time_ns':9})]:test(n,not valid(rr={**res,**patch}))
 test('wrong_log',not valid(ll={'different':True}))
 # Missing mandatory actual pin is rejected even if all supplied values hash.
 reqorig=c.required
 with tempfile.TemporaryDirectory(prefix='s5aa-membership-') as tmp:
  f=Path(tmp)/'x';f.write_text('x');c.required=lambda stage:{str(f):c.sha(f)}
  test('empty_manifest_rejected',not c.inventory_ok({'inventory':{},'trees':[]},None))
 c.required=reqorig
finally:c.read=origread;c.sha=origsha
c.dump(c.H/'link-tests.json',dict(checks=checks,all_passed=all(checks.values())));print(len(checks),'linkage tests PASS')
