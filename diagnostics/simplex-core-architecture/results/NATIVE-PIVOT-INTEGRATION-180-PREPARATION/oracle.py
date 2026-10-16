"""Saved integration-result oracle. No historical tool imports or numerical execution."""
from common import rd,require,Q
import re
MODES=('pfi','forrest_tomlin','suhl_suhl','bartels_golub')
IDS=[m+'/'+p for m in MODES for p in ('default','threshold_one')]+['recovery']
def count(x):return type(x) is int and x>=0
def group(g,name,passes,children):
 require(g['name']==name and type(g['pass']) is int and g['pass']==passes,'Test group/pass '+name)
 require(all(type(g[k]) is int and g[k]==0 for k in ['fail','error','broken']) and g['failures']==[],'Failed test '+name)
 require(len(g['children'])==children,'Test child count '+name)
def vector(v,n):require(type(v) is list and len(v)==n and all(count(x) for x in v),'Invalid count vector')
def test_results(raw,phase):
 require(phase=='integration' and raw['phase']==phase,'Phase')
 require(raw['complete'] is True and raw['fatal']=='' and raw['probe_failed'] is False,'Incomplete or failed execution')
 require(type(raw['started']) is int and raw['started']==9 and type(raw['active']) is int and raw['active']==0,'Case state')
 require(type(raw['threads']) is int and type(raw['blas_threads']) is int and raw['threads']==raw['blas_threads']==1,'Threads')
 root=raw['tests'];group(root,'root',0,2);public,recovery=root['children']
 group(public,'Native pivot policy public integration',0,8)
 for i,g in enumerate(public['children']):group(g,IDS[i].replace('/',' / '),6,0)
 group(recovery,'Native pivot policy private recovery',114,0)
 cases=raw['cases'];require(type(cases) is list and len(cases)==9,'Nine exact cases')
 base=rd(Q/'controls-baseline.json')['default'];require(len(base)==20 and all(re.fullmatch('[0-9a-f]{16}',t) for t in base),'Frozen controls')
 totals=[0]*4;scan_entries=0;refactor_coverage={};nonempty=[]
 for i,c in enumerate(cases):
  symbol='threshold_one' if i==8 or i%2 else 'default';caps=(2,0,2,6) if i==8 else (64,64,4096,4096)
  require(c['id']==IDS[i] and c['policy']==symbol and c['finished'] is True,'Case order/policy/finish')
  a=c['attempts'];s=c['successes'];e=c['empty'];vector(a,4);vector(s,2);vector(e,2)
  require(all(n<=cap for n,cap in zip(a,caps)),'Attempt cap')
  require(all(e[k]<=s[k]<=a[k] for k in range(2)),'Attempt/success/empty linkage')
  require(s[0]-e[0]>=1,'No nonempty construction observed')
  expected=base.copy()
  if symbol=='threshold_one':expected[3]='3ff0000000000000';expected[7]='0000000000000000'
  require(c['expected_controls']==expected and c['last_controls']==expected,'All20 control oracle')
  if i<8:
   require(c['status']=='OPTIMAL' and c['has_point'] is True and c['has_objective'] is True,'Public result presence')
   require(c['point']==['4000000000000000','4000000000000000'] and c['objective']=='c024000000000000','Literal optimum bits')
  else:
   require(a[0]==s[0]==2 and e==[0,0] and a[1]==s[1]==0 and a[2]==2 and 3<=a[3]<=6,'Recovery selected work')
   require(c['status']=='recovery' and c['has_point'] is False and c['has_objective'] is False and c['point']==[] and c['objective']=='','Recovery serialization shape')
  totals=[x+y for x,y in zip(totals,a)];scan_entries+=20*sum(s[k]-e[k] for k in range(2))
  refactor_coverage[c['id']]=dict(attempts=a[1],successful_nonempty=s[1]-e[1]);nonempty.append(s[0]-e[0])
 require(all(x<=y for x,y in zip(totals,[514,512,32770,32774])),'Aggregate caps')
 require(raw['selected_scope']=='managed Float64 UMFPACK backend attempts; extracted-factor and raw auxiliary LU work excluded','Scope')
 return dict(assertions=162,public_solves=8,recovery_trials=1,selected_attempts=totals,control_entries_checked=scan_entries,refactor_coverage=refactor_coverage,nonempty_constructions=nonempty,scope=raw['selected_scope'],limitation='Selected boundaries only, not complete manager/native work or a performance comparison')
