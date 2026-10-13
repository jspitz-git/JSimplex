"""Exclusive synthetic tests of exact final invocation validator. No numerical calls."""
from common_final import *
import copy,sys
s=(H/'audit-final.py').read_text();code=s[s.index('def invocation_valid('):s.index('\ndef audit(out):')]
root=H/'synthetic-linkage';root.mkdir();rows=[]
for name in ['valid','missing-log','missing-reservation','wrong-command','wrong-pin','false-returncode','log-mismatch']:
 dest=root/name;dest.mkdir();process={'runner':{'boot_id':'synthetic-only'},'reason':'exit0'}
 inv=dict(returncode=0,command=[sys.executable,str(G),'run',str(dest/'launch-pins.json'),str(O),'--seconds','120','--',*command()],started_ns=2,ended_ns=3,host={'boot_id':'synthetic-only','matches':[]})
 res=dict(command=command(),pins_sha256='synthetic-pin',time_ns=1);log=copy.deepcopy(process)
 if name=='wrong-command':inv['command']=[]
 if name=='wrong-pin':res['pins_sha256']='wrong'
 if name=='false-returncode':inv['returncode']=False
 if name=='log-mismatch':log['reason']='exit1'
 dump(dest/'guard-invocation.json',inv)
 if name!='missing-reservation':dump(dest/'attempt-reserved.json',res)
 if name!='missing-log':dump(dest/'guard-output.log',log)
 scope=dict(H=dest,G=G,O=O,sys=sys,read=read,command=command);exec(code,scope)
 try:actual=scope['invocation_valid'](process,'synthetic-pin');error=None
 except Exception as e:actual=False;error=repr(e)
 rows.append(dict(case=name,accepted=actual,error=error,passed=actual is (name=='valid')))
assert all(x['passed'] for x in rows)
dump(H/'linkage-cases.json',dict(rows=rows,all_passed=True,source_fragment=code,scope='Exact final validator with synthetic metadata; not runtime evidence.'))
