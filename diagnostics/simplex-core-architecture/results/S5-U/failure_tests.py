"""Exclusive new offline synthetic schema/refusal tests; no Julia or old script."""
from common import *
from audit import data_checks
import copy,subprocess,tomllib
F=H/'failure-cases';F.mkdir()
schema=read(H/'schema.json');expected=tomllib.loads((H/'expected.toml').read_text());raw=dict(checks={k:True for k in schema['checks']},observations=dict(schema['observation_values'],start_ns='123'),at_throw=schema['work'],after_unwind=schema['work']);report=dict(passes=42,fails=0,errors=0,broken=0,entry_counts=[1,1,1],julia_threads=1,blas_threads=1,**{k+'_sha256':expected[v] for k,v in [('test','candidate'),('prefix','prefix'),('suffix','suffix'),('executed','executed')]})
checks={'valid_synthetic_schema':all(data_checks(raw,report,schema,expected).values())};cases=[]
for name,change in [('literal_integer',lambda r,p:r['checks'].__setitem__(schema['checks'][0],1)),('missing_predicate',lambda r,p:r['checks'].pop(schema['checks'][0])),('extra_init',lambda r,p:p.__setitem__('entry_counts',[1,2,1])),('bool_count',lambda r,p:p.__setitem__('entry_counts',[True,1,1])),('extra_work',lambda r,p:r['after_unwind'].__setitem__('btran',3)),('failed_test',lambda r,p:p.__setitem__('fails',1))]:
 r=copy.deepcopy(raw);p=copy.deepcopy(report);change(r,p);result=data_checks(r,p,schema,expected);checks[name]=not all(result.values());cases.append(dict(name=name,checks=result))
for name,contents in [('missing',None),('malformed','{'),('incomplete','{}')]:
 d=F/name;d.mkdir()
 if contents is not None:(d/'process.json').write_text(contents)
 dest=F/(name+'-audit.json');cmd=[sys.executable,str(H/'audit.py'),'green',str(d),str(dest)];p=subprocess.run(cmd,capture_output=True,text=True)
 dump(F/(name+'-process.json'),dict(command=cmd,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr));x=read(dest);checks['durable_'+name]=p.returncode==1 and x['all_passed'] is False and x['checks']=={'readable_valid_complete_inputs':False}
dump(H/'failure-tests.json',dict(checks=checks,all_passed=all(checks.values()),synthetic_cases=cases,sha256={str(H/n):sha(H/n) for n in ('failure_tests.py','audit.py','common.py','schema.json','expected.toml')}));print(json.dumps(checks));assert all(checks.values())
