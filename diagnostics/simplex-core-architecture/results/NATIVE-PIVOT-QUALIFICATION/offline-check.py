"""New offline verification. Never calls seal/launch/guard.run or Julia."""
from common import *
import ast,re,copy,importlib.util
checks={}
for p in Q.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
checks['python_syntax']=True
inv=rd(Q/'test-inverse.json')
for name,z in inv.items():
 text=(Q/name).read_text();require(sha(Q/name)==z['sha256'],'Instrumented hash')
 for a,b,count in reversed(z['edits']):require(text.count(b)==count,'Inverse count '+b);text=text.replace(b,a)
 require(text==Path(z['source']).read_text() and sha(z['source'])==z['source_sha256'],'Full original test inverse')
checks['whole_test_inverse']=True
for s in rd(Q/'neighbor-slices.json'):require((R/s['source']).read_text()[s['start']:s['end']]==s['text'],'Neighbor byte identity')
checks['five_whole_neighbors']=len([s for s in rd(Q/'neighbor-slices.json') if 'title' in s])==5
checks['candidate_fixed']=all(sha(e['source'])==e['sha256'] for a in ['reference','candidate'] for e in rd(PREV/'overlay-manifest.json')[a])
checks['runtime_hashes']=bindings(rd(Q/'runtime-pins.json'))
budget=rd(Q/'budget.json');checks['assertion_sum']=sum(budget['test_groups'].values())==budget['green_assertions']==6858
checks['window_budget']=len(rd(Q/'inputs.json')['schedule'])==88 and 88*48==4224 and 88*32==2816 and 88*16==1408
checks['exact_fixture_reuse']=rd(Q/'inputs.json')['fixtures']==rd(Q.parent/'NATIVE-ACCURACY-PREPARATION/inputs.json')['fixtures']
checks['stored_C_bound']=all(sha(e['path'])==e['sha256'] for vals in rd(Q/'saved-C.json').values() for e in vals)
checks['no_julia_or_stage']=not (Q/'runs').exists() and not (R/'.superpowers/native-pivot-qualification').exists()
checks['unchanged_actual']=not git('diff','--name-only','--','src','test','Project.toml','.github','diagnostics/direct-lu-markowitz/reproduce')
# Test pure validation refusal before using it in an admitted run.
from control import verify_review,config,guard_command
from oracle import test_results
from exact import residual,token,validate_controls,validate_timing
cases=[]
def refuses(name,f):
 try:f()
 except (ValueError,RuntimeError,KeyError,TypeError):cases.append(name);return
 raise RuntimeError('Failed to refuse '+name)
refuses('unknown phase',lambda:config('other'))
for value in [{},{'accepted':False,'findings':[],'scope':'offline preparation'},{'accepted':True,'findings':['x'],'scope':'offline preparation'}]:
 refuses('review acceptance',lambda value=value:verify_review(value,Q/'entry.json',[],'offline preparation'))
base=[token(0.)]*20;base[3]=token(.1);good=list(base);good[3]=token(1.)
validate_controls('P',good,base)
for index in [3,7,15,19]:
 bad=good.copy();bad[index]=token(7.)
 refuses('control '+str(index),lambda bad=bad:validate_controls('P',bad,base))
m=dict(n=1,colptr=[1,2],rowval=[1],nzval=[token(2.)]);require(residual(m,[token(1.)],[token(2.)])['passed'],'Exact positive');require(not residual(m,[token(2.)],[token(2.)])['passed'],'Exact negative')
red=dict(complete=True,fatal='',threads=1,blas_threads=1,counts={},events=[],equations=[],tests=dict(name='root',**{'pass':0,'fail':0,'error':0,'broken':0,'children':[dict(name='Missing native pivot policy contract',**{'pass':0,'fail':4,'error':0,'broken':0,'children':[],'failures':['native_pivot_policy','_NativePivotPolicy','pivot_policy','_native_lu']})]}))
require(test_results(red,'red')['expected_failure'],'RED exact positive')
for field,value in [('fatal','error'),('complete',False),('counts',{'raw_lu':1}),('events',[{}]),('equations',[{}])]:
 bad=copy.deepcopy(red);bad[field]=value;refuses('RED '+field,lambda bad=bad:test_results(bad,'red'))
for field,value in [('pass',1),('fail',3),('error',1),('broken',1),('failures',['wrong']*4)]:
 bad=copy.deepcopy(red);bad['tests']['children'][0][field]=value;refuses('RED '+field,lambda bad=bad:test_results(bad,'red'))
checks['synthetic_refusals']=len(cases)==18
checks['no_admission_or_reservation']=not list(Q.glob('*reservation*')) and not list(Q.glob('*admission.json'))
save(Q/'offline-check.json',dict(all_passed=all(checks.values()),checks=checks,refusals=cases,sha256={str(p):sha(p) for p in sorted(Q.iterdir()) if p.is_file() and p.name!='offline-check.json'}))
require(all(checks.values()),'Offline check failed; preserve output');print(dict(checks=len(checks),refusals=len(cases),all_passed=True))
