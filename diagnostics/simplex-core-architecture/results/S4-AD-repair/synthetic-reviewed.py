"""One-use new pure schema checks and corrected schedule arithmetic; no Julia."""
import sys,copy
from pathlib import Path
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D))
from common import dump,sha,require,read
from oracle import raw_ok
from freeze_stage_reviewed import WORKSPACE,MARKOWITZ,CACHE
checks={};path='/fixture/test.jl'
for stage,rows in [('red',[(WORKSPACE[-1][0],[20,4,0,0])]),('green',[(x,[v,0,0,0]) for x,v in MARKOWITZ]),('master',[(x,[v,0,0,0]) for x,v in WORKSPACE])]:
 c=dict(stage=stage,root='/fixture',files=[path],expected={path:[dict(name=x,counts=v) for x,v in rows]})
 children=[dict(name=x,counts=v,nonpasses=([dict(kind=2,expression='row.reads == vcat',file=path,line=39,display='expected failure') for _ in range(4)] if stage=='red' else []),children=[]) for x,v in rows]
 r=dict(stage=stage,source='/fixture/src/JSimplex.jl',Julia_version='1.13.0',before_precision=256,before_rounding='RoundingMode{:Nearest}()',after_precision=256,after_rounding='RoundingMode{:Nearest}()',ambient_ok=True,errors=[],all_passed=stage!='red',files=[dict(file=path,tree=dict(name=path,counts=[0,0,0,0],nonpasses=[],children=children),counts=[sum(v[i] for _,v in rows) for i in range(4)])])
 checks[stage+'_valid']=raw_ok(r,c);variants=[]
 q=copy.deepcopy(r);q['errors']=['unexpected'];variants.append(q)
 q=copy.deepcopy(r);q['all_passed']=not q['all_passed'];variants.append(q)
 q=copy.deepcopy(r);q['files'][0]['tree']['children'][0]['counts'][0]-=1;variants.append(q)
 q=copy.deepcopy(r);q['files'][0]['tree']['children']=[];variants.append(q)
 q=copy.deepcopy(r);q['after_precision']=128;variants.append(q)
 q=copy.deepcopy(r);q['files'][0]['counts'][-1]=False;variants.append(q)
 if stage=='red':
  for key,value in [('line',38),('kind',3),('expression','unrelated'),('file','/wrong')]:
   q=copy.deepcopy(r);q['files'][0]['tree']['children'][0]['nonpasses'][0][key]=value;variants.append(q)
 for i,q in enumerate(variants):checks[stage+'_reject_'+str(i)]=not raw_ok(q,c)
schedule=read(D/'schedule.json');checks['source_counts']=sum(v for _,v in WORKSPACE)==324 and sum(v for _,v in MARKOWITZ)==308 and sum(v for _,v in CACHE)==90
checks['corrected_schedule']=schedule['markowitz_file']['expected_GREEN_counts']==[308,0,0,0] and schedule['green']['expected_counts']==[722,0,0,0]
driver=(D/'driver.jl').read_text();original=(D.parent/'S4-AD/driver.jl').read_text()
checks['original_bad_api_preserved']='Test.push_testset(ts)' in original and 'Test.pop_testset()' in original
checks['scope_API_replaced']='Test.push_testset' not in driver and 'Test.pop_testset' not in driver and driver.count('Test.@with_testset ts begin')==1
checks['context_restoration']='Test.get_testset() === parent_testset && Test.get_testset_depth() == parent_depth' in driver
api=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/stdlib/v1.13/Test/src/Test.jl').read_text()
checks['installed_macro_exists']='macro with_testset(ts, expr)' in api and 'push_testset' not in api and 'pop_testset' not in api
checks['failed_attempt_preserved']=read(D.parent/'S4-AD/red/audit.json')['all_passed'] is False and not (D.parent/'S4-AD/red/raw/tests.toml').exists()
checks['new_groups']=len(read(D/'host.json')['groups'])==36 and read(D/'host.json')['matches']==[]
result=dict(all_passed=all(checks.values()),checks=checks,sha256={str(D/n):sha(D/n) for n in ('oracle.py','driver.jl','run_stage_reviewed.py','common.py','freeze_stage_reviewed.py','schedule.json','synthetic-reviewed.py','repair-plan.md','repair-evidence.json')},scope='New synthetic Test-result objects and corrected schedule arithmetic only; no Julia/launcher execution.')
dump(D/'synthetic.json',result);require(result['all_passed'],'synthetic schema failed');print('Synthetic gates',len(checks),'PASS')
