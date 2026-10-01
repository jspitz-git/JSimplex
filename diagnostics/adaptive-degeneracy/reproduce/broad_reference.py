"""Serial independent HiGHS LP-relaxation references for the expanded corpus."""
import ctypes as c,hashlib,json,resource,sys,time,tomllib
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(8*1024**3,8*1024**3))
lib=c.CDLL('/home/jspitz/.julia/artifacts/664e3659d6b26b70e764cb87b2ba2e87a33e2053/lib/libhighs.so.1.15.0')
p=c.c_void_p;i=c.c_int;f=c.c_double;s=c.c_char_p
signatures={'Highs_create':([],p),'Highs_destroy':([p],None),'Highs_version':([],s),
 'Highs_readModel':([p,s],i),'Highs_run':([p],i),'Highs_getModelStatus':([p],i),
 'Highs_getObjectiveValue':([p],f),'Highs_setBoolOptionValue':([p,s,i],i),
 'Highs_setIntOptionValue':([p,s,i],i),'Highs_setDoubleOptionValue':([p,s,f],i),
 'Highs_setStringOptionValue':([p,s,s],i),'Highs_getIntInfoValue':([p,s,c.POINTER(i)],i),
 'Highs_getDoubleInfoValue':([p,s,c.POINTER(f)],i),
 'Highs_getNumCol':([p],i),'Highs_getNumRow':([p],i),
 'Highs_getSolution':([p,*([c.POINTER(f)]*4)],i),'Highs_getColName':([p,i,s],i)}
for name,(args,result) in signatures.items():
 fn=getattr(lib,name);fn.argtypes=args;fn.restype=result
def save_report(report,output):
 output.write_text(json.dumps(report,indent=2)+'\n')
 def literal(v):
  if isinstance(v,float) and not __import__('math').isfinite(v):return str(v).lower()
  return json.dumps(v)
 lines=[k+' = '+literal(v) for k,v in report.items() if k!='cases']
 for row in report['cases']:
  lines.append('\n[[cases]]')
  lines.extend(k+' = '+literal(v) for k,v in row.items())
 output.with_suffix('.toml').write_text('\n'.join(lines)+'\n')
entries=tomllib.loads(Path(sys.argv[1]).read_text())['cases'];output=Path(sys.argv[2])
assert not output.exists()
report={'version':lib.Highs_version().decode(),'threads':1,'time_limit':60,'solve_relaxation':True,'cases':[]}
def check(code):
 assert code==0,code
def info(model,key,kind):
 value=kind();fn=lib.Highs_getIntInfoValue if kind is i else lib.Highs_getDoubleInfoValue
 check(fn(model,key.encode(),c.byref(value)));return value.value
for entry in entries:
 if len(sys.argv)>3 and entry['id'] not in sys.argv[3:]:continue
 path=Path(entry['path']);assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256']
 model=lib.Highs_create()
 try:
  check(lib.Highs_setBoolOptionValue(model,b'output_flag',0))
  check(lib.Highs_setBoolOptionValue(model,b'solve_relaxation',1))
  check(lib.Highs_setIntOptionValue(model,b'threads',1))
  check(lib.Highs_setStringOptionValue(model,b'solver',b'simplex'))
  check(lib.Highs_setDoubleOptionValue(model,b'time_limit',60))
  read_status=lib.Highs_readModel(model,str(path).encode());assert read_status in (0,1),read_status
  start=time.monotonic();run_status=lib.Highs_run(model)
  row={'id':entry['id'],'sha256':entry['sha256'],'status':lib.Highs_getModelStatus(model),
       'objective':lib.Highs_getObjectiveValue(model),'seconds':time.monotonic()-start,
       'read_return':read_status,'run_return':run_status,
       'iterations':info(model,'simplex_iteration_count',i),
       'max_primal_infeasibility':info(model,'max_primal_infeasibility',f),
       'max_dual_infeasibility':info(model,'max_dual_infeasibility',f)}
  if row['status']==7:
   n,m=lib.Highs_getNumCol(model),lib.Highs_getNumRow(model)
   primal,dual,activity,rowdual=(f*n)(),(f*n)(),(f*m)(),(f*m)()
   check(lib.Highs_getSolution(model,primal,dual,activity,rowdual))
   names=[]
   for column in range(n):
    buffer=c.create_string_buffer(512)
    check(lib.Highs_getColName(model,column,buffer));names.append(buffer.value.decode())
   primal_path=output.parent/(output.stem+'-'+entry['id'].replace('/','-')+'-primal.toml')
   primal_path.write_text('column_names = '+json.dumps(names)+'\nprimal = '+json.dumps(list(primal))+'\n')
   row['primal_path']=str(primal_path)
  report['cases'].append(row);save_report(report,output)
  print(row,flush=True)
 finally:lib.Highs_destroy(model)
