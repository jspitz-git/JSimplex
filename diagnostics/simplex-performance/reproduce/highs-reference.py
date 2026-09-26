"""Independent serial LP simplex reference through the installed HiGHS C API."""
import ctypes as c
import hashlib
import json
from pathlib import Path
import resource
import time

resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3))
lib=c.CDLL('/home/jspitz/.julia/artifacts/664e3659d6b26b70e764cb87b2ba2e87a33e2053/lib/libhighs.so.1.15.0')
ptr=c.c_void_p; integer=c.c_int; number=c.c_double; string=c.c_char_p
signatures={
 'Highs_create':([],ptr),'Highs_destroy':([ptr],None),'Highs_version':([],string),
 'Highs_readModel':([ptr,string],integer),'Highs_run':([ptr],integer),
 'Highs_setBoolOptionValue':([ptr,string,integer],integer),
 'Highs_setIntOptionValue':([ptr,string,integer],integer),
 'Highs_setDoubleOptionValue':([ptr,string,number],integer),
 'Highs_setStringOptionValue':([ptr,string,string],integer),
 'Highs_getModelStatus':([ptr],integer),'Highs_getObjectiveValue':([ptr],number),
 'Highs_getIntInfoValue':([ptr,string,c.POINTER(integer)],integer),
 'Highs_getDoubleInfoValue':([ptr,string,c.POINTER(number)],integer),
 'Highs_getNumCol':([ptr],integer),'Highs_getNumRow':([ptr],integer),
 'Highs_getSolution':([ptr,*([c.POINTER(number)]*4)],integer),
}
for name,(args,result) in signatures.items():
 fn=getattr(lib,name);fn.argtypes=args;fn.restype=result
def check(code):
 assert code==0,code
def info(model,key,kind):
 value=kind()
 fn=lib.Highs_getIntInfoValue if kind is integer else lib.Highs_getDoubleInfoValue
 check(fn(model,key.encode(),c.byref(value)))
 return value.value

work=Path('.superpowers/performance')
def safe(value):
 if isinstance(value,dict):return {k:safe(v) for k,v in value.items()}
 if isinstance(value,list):return [safe(v) for v in value]
 if isinstance(value,float) and not __import__('math').isfinite(value):return str(value)
 return value
report={'version':lib.Highs_version().decode(),'threads':1,'solve_relaxation':True,
        'time_limit':360,'presolve':'on','solver':'simplex','cases':[]}
for name in ('fast0507','runtime','medium'):
 path=Path('/home/jspitz/mps')/(name+'.mps')
 digest=hashlib.sha256(path.read_bytes()).hexdigest()
 for algorithm,strategy in (('dual',1),('primal',4)):
  model=lib.Highs_create()
  try:
   check(lib.Highs_setBoolOptionValue(model,b'output_flag',0))
   check(lib.Highs_setBoolOptionValue(model,b'solve_relaxation',1))
   check(lib.Highs_setIntOptionValue(model,b'threads',1))
   check(lib.Highs_setIntOptionValue(model,b'simplex_strategy',strategy))
   check(lib.Highs_setStringOptionValue(model,b'solver',b'simplex'))
   check(lib.Highs_setStringOptionValue(model,b'presolve',b'on'))
   check(lib.Highs_setDoubleOptionValue(model,b'time_limit',360))
   check(lib.Highs_readModel(model,str(path).encode()))
   print('Started HiGHS',name,algorithm,flush=True)
   start=time.monotonic(); code=lib.Highs_run(model);elapsed=time.monotonic()-start
   row={'name':name,'algorithm':algorithm,'source_sha256':digest,'status':lib.Highs_getModelStatus(model),
        'return_code':code,'seconds':elapsed,'objective':lib.Highs_getObjectiveValue(model),
        'iterations':info(model,'simplex_iteration_count',integer),
        'max_primal_infeasibility':info(model,'max_primal_infeasibility',number),
        'max_dual_infeasibility':info(model,'max_dual_infeasibility',number)}
   report['cases'].append(row)
   (work/'highs-reference.json').write_text(json.dumps(safe(report),indent=2,allow_nan=False)+'\n')
   if row['status']==7:
    n,m=lib.Highs_getNumCol(model),lib.Highs_getNumRow(model)
    primal,dual,activity,row_dual=(number*n)(),(number*n)(),(number*m)(),(number*m)()
    check(lib.Highs_getSolution(model,primal,dual,activity,row_dual))
    (work/(name+'-highs-'+algorithm+'-primal.bin')).write_bytes(bytes(primal))
   print(row,flush=True)
  finally:lib.Highs_destroy(model)
