"""Deterministic mocks only. No Popen/process/host signals or Julia."""
from pathlib import Path
import sys,json,subprocess
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D));sys.dont_write_bytecode=True
import supervisor as S
import audit as A
checks={}
def ck(n,b):
 checks[n]=b is True
 if not b:raise ValueError(n)
class Clock:
 def __init__(self):self.now=0.
 def monotonic(self):return self.now
clock=Clock();S.time=clock
class Proc:
 pid=100
 def __init__(self,script):self.script=list(script);self.calls=[]
 def wait(self,timeout):
  self.calls.append(timeout)
  x=self.script.pop(0)
  if x=='timeout':clock.now+=timeout;raise subprocess.TimeoutExpired('mock',timeout)
  clock.now+=.1;return x
identity=dict(pid=100,pgid=100,sid=100,start_ticks=1,boot_id='mock',command='mock')
S.guard.process_identity=lambda pid:dict(identity,pid=pid,pgid=pid,sid=pid)
signals=[];S.send_one=lambda who,sig,owner=None:signals.append((who['pid'],sig)) or True
S.kill_child=lambda out:True
for name,script,soft,hard,accepted in [('normal',[0],False,False,True),('nonzero',[1],False,False,False),('soft',['timeout',0],True,False,False),('hard',['timeout','timeout',-9],True,True,False),('unreaped',['timeout','timeout','timeout'],True,True,False)]:
 clock.now=0.;p=Proc(script);S.subprocess.Popen=lambda *args,**kwargs:p
 r=S.run(['mock'],None,Path('/tmp/nonexistent'),0.)
 ck(name,r['soft_timeout'] is soft and r['hard_timeout'] is hard and r['accepted'] is accepted and all(t<=90 for t in p.calls) and clock.now<=90.2)
# Re-import an isolated fresh module for per-member pidfd/owner identity checks.
import importlib.util
sp=importlib.util.spec_from_file_location('supervisor_fresh',D/'supervisor.py');M=importlib.util.module_from_spec(sp);sp.loader.exec_module(M)
class OS:
 def pidfd_open(self,pid,flags):return 500
 def close(self,fd):pass
class Sig:
 def __init__(self):self.sent=[]
 def pidfd_send_signal(self,fd,sig,x,y):self.sent.append((fd,sig))
M.os=OS();M.signal=Sig()
member=dict(identity,pid=101,pgid=100,sid=100,command='member')
for name,records,ok in [('valid',[member,member,identity],True),('member_reused',[dict(member,start_ticks=2)],False),('between_reads',[member,dict(member,command='changed')],False),('owner_reaped_reused',[member,member,dict(identity,start_ticks=9)],False),('member_left_session',[member,dict(member,pgid=999,sid=999)],False)]:
 seq=iter(records);M.guard.process_identity=lambda pid:next(seq);M.signal.sent=[]
 ck(name,M.send_one(member,9,owner=identity) is ok and bool(M.signal.sent) is ok)
obj=dict(all_passed=all(checks.values()),checks=checks,scope='pure mocks, no actual process operations',sha256={str(D/n):A.sha(D/n) for n in ['supervisor.py','supervisor-tests.py']})
with (D/'supervisor-tests-final.json').open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
print(len(checks),'PASS')
