"""Fresh pure-data RED/GREEN and cwd independence; no launch/seal/supervisor."""
from control import *
import oracle,copy,ast
checks={}
def ck(n,v):checks[n]=bool(v);require(v,n)
old={};exec(compile((D/'oracle.py.before-review').read_text(),'preserved oracle definitions','exec'),old)
proc=dict(reason='wall_time',returncode=-15,pins_unchanged=True);sup=dict(returncode=1,hard_timeout=False);log='BEGIN native_pivot_policy_tests.jl'
loaded=rd(D/'loaded-paths.json');node=dict(name='root',**{'pass':0,'fail':0,'error':0,'broken':0,'failures':[],'children':[]})
valid=dict(complete=False,fatal='',loaded=loaded,threads=1,blas_threads=1,tests=node)
def accepted(raw):return oracle.timeout_only(proc,sup,raw,log,299,300,loaded)
for i,raw in enumerate([{},dict(complete=False,fatal=''),dict(complete='false',fatal='',tests={}),dict(complete=False,fatal='',tests={})]):
 ck('RED preserved malformed '+str(i),old['timeout_only'](proc,sup,raw,log,299,300) is True)
 ck('GREEN malformed '+str(i),accepted(raw) is False)
ck('missing raw remains permitted',accepted(None) is True);ck('valid empty partial',accepted(valid) is True)
partial=copy.deepcopy(valid);child=copy.deepcopy(node);child.update(name='options_and_copy_intent',**{'pass':7});partial['tests']['children']=[child];ck('valid incomplete counts',accepted(partial) is True)
for key in valid:
 bad=copy.deepcopy(valid);del bad[key];ck('missing '+key,accepted(bad) is False)
for key,value in [('complete','false'),('complete',0),('complete',True),('fatal','failure'),('threads',True),('threads',2),('blas_threads',1.0),('loaded',{}),('tests',[])]:
 bad=copy.deepcopy(valid);bad[key]=value;ck('invalid '+key+repr(value),accepted(bad) is False)
for key,value in [('name',''),('name','other'),('pass',1),('pass',-1),('pass',True),('fail',1),('error',1),('broken',1),('failures',['error']),('children',{})]:
 bad=copy.deepcopy(valid);bad['tests'][key]=value;ck('invalid root '+key+repr(value),accepted(bad) is False)
bad=copy.deepcopy(partial);bad['tests']['children'][0]['error']=1;ck('nested error',accepted(bad) is False)
bad=copy.deepcopy(partial);bad['tests']['children'][0]['pass']=-1;ck('negative child',accepted(bad) is False)
bad=copy.deepcopy(valid);bad['extra']='x';ck('unexpected raw field',accepted(bad) is False)
ck('failure log veto',oracle.timeout_only(proc,sup,valid,log+' TEST FAILURE:',299,300,loaded) is False)
# Extract only the modified return expression; production preparation itself requires final review.
f=next(n for n in ast.parse((D/'control.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='preparation')
expr=ast.Expression(f.body[-1].value);code=compile(expr,'runtime files expression','eval');m=D/'preparation-pins.json';j=rd(m)
original=Path.cwd();os.chdir('/tmp')
try:files=eval(code,dict(sorted=sorted,str=str,path=path,j=j,m=m,D=D))
finally:os.chdir(original)
ck('runtime all absolute',all(Path(n).is_absolute() for n in files));ck('runtime exact normalized membership',set(files)=={str(path(n)) for n in j['sha256']}|{str(m),str(D/'review-final.json')})
ck('relative input actually tested',any(not Path(n).is_absolute() for n in j['sha256']))
ck('no runs',not (D/'runs').exists())
files=[Path(__file__),D/'oracle.py',D/'oracle.py.before-review',D/'control.py',D/'control.py.before-review',D/'audit.py',D/'review-amendment.py']
save(D/'review-amendment-tests.json',dict(all_passed=all(checks.values()),checks=checks,sha256={str(p):sha(p) for p in files}))
print(len(checks),'fresh offline RED/GREEN checks PASS')
