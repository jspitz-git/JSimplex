from pathlib import Path
D=Path(__file__).resolve().parent;S=D.with_name('MA-S-2');V=D.with_name('MA-V')
s=(S/'offline-tests.py').read_text();s=s[:s.index('# validate_admission only:')]
s=s.replace("import copy,json,math,importlib.util,tempfile", "import copy,json,math,importlib.util,tempfile,sys,ast\nsys.path.insert(0,str(Path(__file__).resolve().parent));sys.dont_write_bytecode=True")
s=s.replace('maximum_seconds_per_process\':120','maximum_seconds_per_process\':90').replace('seconds=120','seconds=90').replace('range(1,161)','range(1,171)').replace('total_cap_seconds=360','total_cap_seconds=270').replace('only159groups','only169groups').replace('range(1,160)','range(1,170)').replace("str(D.with_name('MA-S-LOAD')/'driver.jl')","str(D/'driver.jl')")
v=(V/'offline-tests.py').read_text();v=v[v.index("oldD=L.D"):v.index('# Durable journal correspondence')]
v=v.replace("'micro-batch.jl','tests-recorded.jl','guard-tests-recorded.jl',","'source-map.json',").replace('maximum_processes=2','maximum_processes=3')
s+="L=module('launcher')\n"+v
s+='''
# Independent strict one-process reducer checks against the old aggregate process rows.
for i,r in enumerate(rs,1):
 one=A.process_costs(r);agg=A.aggregate(rs)
 check('process_reducer_matches_'+str(i),all({k:v for k,v in p.items() if k!='id'}==row['processes'][i-1] for p,row in zip(one,agg)))
for ci in (50,51):
 for field in ('bytes','events'):
  r=copy.deepcopy(rs[0])
  for w in r['costs'][ci]['windows']:
   if w['phase']=='measured' and w['side']=='candidate':w[field]+=1
  check('rational_reject_'+str(ci)+'_'+field,not A.process_costs(r)[ci]['pass'])
# Paired-ratio target gate must differ from ratio of side medians on this fixture.
r=copy.deepcopy(rs[0]);rr=[1,2,3,4,5,6,7];cc=[.9,1.8,2.7,40,4.5,5.4,6.3]
for side,values in [('reference',rr),('candidate',cc)]:
 for w,v in zip([w for w in r['costs'][0]['windows'] if w['phase']=='measured' and w['side']==side],values):w['seconds']=v
check('paired_ratio_not_side_ratio',A.process_costs(r)[0]['ratio']==.9 and A.process_costs(r)[0]['pass'])
def journal(r):
 out=[]
 for c in r['costs']:
  for w in c['windows']:
   location='cost/'+c['id']+'/'+str(w['pair'])+'/'+str(1 if w['side']=='reference' else 2)
   out.extend([dict(kind='whole-metrics',location=location,window={k:v for k,v in w.items() if k not in ('output','preserved')}),dict(kind='whole-complete',location=location,window=w)])
 return out
for i,r in enumerate(rs,1):
 j=journal(r);check('journal_valid_'+str(i),A.journal_valid(j,r) and len(j)==2080)
 for label,mut in [('metrics_only',lambda x:x.pop()),('conversion_failure_prefix',lambda x:x.__delitem__(slice(1,None))),('assertion_failure_complete_prefix',lambda x:x.__delitem__(slice(2,None))),('changed',lambda x:x[0]['window'].update(bytes=999)),('reordered',lambda x:x.reverse())]:
  jj=copy.deepcopy(j);mut(jj)
  try:A.journal_valid(jj,r);refused=False
  except (ValueError,KeyError):refused=True
  check('journal_reject_'+str(i)+'_'+label,refused)
# No stage can pass absent output or a missing process/seal; read-only failure.
check('missing_real_outputs_fail_closed',all(A.stage(i)['all_passed'] is False for i in (1,2,3)))
for n in ['audit.py','launcher.py','supervisor.py','guard.py']:
 tree=ast.parse((D/n).read_text());check('no_assert_gate_'+n,not any(isinstance(x,ast.Assert) for x in ast.walk(tree)))
check('no_outputs',not any((D/n).exists() for n in ['launch-context.json','numerical-review.json','sequence-reservation.json','run-1','run-2','run-3']))
obj=dict(all_passed=all(results.values()),checks=results,scope='New synthetic Python records and fake admission files only; no real launcher main, no Julia, no old audit run',sha256={str(D/n):A.sha(D/n) for n in ['audit.py','launcher.py','guard.py','schedule.json','commands.json','offline-tests.py']})
with (D/'offline-tests.json').open('x') as f:json.dump(obj,f,indent=2);f.write('\\n')
print(len(results),'PASS')
'''
with (D/'offline-tests.py').open('x') as f:f.write(s)
