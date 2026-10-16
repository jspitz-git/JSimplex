"""Independent offline read-only review. Only creates exclusive reviewer evidence.
No Julia, author checker, historical auditor, stage, seal, guard or launch execution.
"""
from pathlib import Path
import ast,copy,hashlib,json,os,subprocess,sys,time
D=Path(__file__).resolve().parent;R=D.parents[3];P=D.parent/'NATIVE-PIVOT-INTEGRATION-PREPARATION'
sys.dont_write_bytecode=True;sys.path.insert(0,str(D))
checks={};details={}
def ck(name,value):checks[name]=bool(value)
def rd(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
def rejects(f):
 try:f()
 except (RuntimeError,ValueError,KeyError,TypeError,IndexError,FileNotFoundError):return True
 return False
pins=rd(D/'preparation-pins.json')['sha256'];req=rd(D/'required-paths.json')['paths']
ck('1503 absolute pins',len(pins)==1503 and all(Path(n).is_absolute() for n in pins))
ck('required exact unique membership',set(req)==set(pins) and len(req)==len(set(req)))
for n,h in pins.items():ck('pin '+n,sha(n)==h)
base=rd(D/'actual-baseline.json')['sha256'];ck('520 baseline files',len(base)==520)
for n,h in base.items():
 ck('baseline current '+n,sha(R/n)==h)
 b=subprocess.check_output(['git','show','HEAD:'+n],cwd=R)
 ck('baseline HEAD '+n,hashlib.sha256(b).hexdigest()==h)
ck('HEAD unchanged',git('rev-parse','HEAD')=='86e0397c882ff6628193cfa4c1d24a7c71ed7c3e')
ck('master unchanged',git('rev-parse','master')=='6f68e24e8ddac42b948da8fcc2d636c010751194')
ck('tracked and index unchanged',not git('diff','--name-only') and not git('diff','--cached','--name-only'))
for fname in ['source-check.json']:
 z=rd(D/fname);ck(fname+' accepted',z['all_passed'] is True)
 ck(fname+' 867 bindings',len(z['sha256'])==867)
 for n,h in z['sha256'].items():ck(fname+' '+n,sha(n)==h)
m=rd(D/'source-map.json')
for n,src in m['byte_identical'].items():ck('inherited exact '+n,Path(src).read_bytes()==(D/n).read_bytes())
x=Path(m['recorder_source']).read_text();ck('recorder inherited exact',x[x.index('module RecordedTests'):x.index('function main()')]==(D/'recorder.jl').read_text())
f=rd(P/'observer-seams.json');s=(D/'observed-factorization.jl').read_text()
for i in reversed(f['application_order']):
 e=f['edits'][i];ck('observer inverse anchor '+str(i),s.count(e['after'])==e['count']);s=s.replace(e['after'],e['before'])
ck('observer whole inverse',s==Path(m['observer_source']).read_text())
t=rd(D/'test-inverse.json');s=(D/'observed-tests.jl').read_text()
for i,e in reversed(list(enumerate(t['edits']))):
 ck('test inverse anchor '+str(i),s.count(e['after'])==1);s=s.replace(e['after'],e['before'])
ck('test whole inverse',s==Path(t['original']).read_text())
old=rd(P/'overlay-manifest.json')['candidate'];new=rd(D/'overlay-manifest.json')['candidate']
ck('76 exact unique destinations',len(old)==len(new)==len({e['destination'] for e in new})==76)
for a,b in zip(old,new):
 ck('overlay '+b['destination'],a==b if b['destination']!='src/factorization.jl' else b['source']==str(D/'observed-factorization.jl'))
 ck('overlay source '+b['destination'],sha(b['source'])==b['sha256'])
ck('public assertions six',s[s.index('function public_case'):s.index('function copied_options')].count('@test ')==6)
ck('recovery assertions 29',s[s.index('function recovery_case'):s.index('@testset "Native pivot policy public')].count('@test ')==29)
ck('five option comparisons',s.count('    copied_options(options,')==5)
ck('one solve one init one checkpoint one trial',all(s.count(v)==1 for v in ['result = solve(','J.initialize_workspace(','J.checkpoint_basis(','J._recovery_trial(']))
ck('one loop of four modes two policies','for mode in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub), symbol in (:default,:threshold_one)' in s)
for name in ['common.py','control.py','seal.py','launch.py','audit.py','oracle.py','guard.py','supervisor.py','finalize.py','publication.py','author-check.py']:
 ast.parse((D/name).read_text());ck('Python text parses '+name,True)
# Only the newly prepared definitions are imported. No command entry point runs.
import control,oracle
raw=rd(D/'synthetic-good.json');out=oracle.test_results(raw,'integration')
ck('synthetic positive only',out['assertions']==162 and out['public_solves']==8 and out['recovery_trials']==1)
ck('zero refactor reported',all(x['attempts']==0 for x in out['refactor_coverage'].values()))
def mutate(label,fn):
 z=copy.deepcopy(raw);fn(z);ck('oracle refuses '+label,rejects(lambda:oracle.test_results(z,'integration')))
for key,val in [('phase','cost'),('complete',False),('fatal','caught'),('probe_failed',True),('started',8),('active',1),('threads',2),('blas_threads',2),('selected_scope','complete work')]:mutate(key,lambda z,k=key,v=val:z.__setitem__(k,v))
for i in range(9):
 for field,values in [('attempts',range(4)),('successes',range(2)),('empty',range(2))]:
  for k in values:mutate(f'negative {i} {field} {k}',lambda z,i=i,f=field,k=k:z['cases'][i][f].__setitem__(k,-1))
 for field in ['expected_controls','last_controls']:
  for k in range(20):mutate(f'all20 {i} {field} {k}',lambda z,i=i,f=field,k=k:z['cases'][i][f].__setitem__(k,'ffffffffffffffff'))
 for k,cap in enumerate((2,0,2,6) if i==8 else (64,64,4096,4096)):
  mutate(f'cap {i} {k}',lambda z,i=i,k=k,cap=cap:z['cases'][i]['attempts'].__setitem__(k,cap+1))
 mutate(f'finished {i}',lambda z,i=i:z['cases'][i].__setitem__('finished',False))
 mutate(f'bool count {i}',lambda z,i=i:z['cases'][i]['attempts'].__setitem__(0,True))
mutate('missing case',lambda z:z['cases'].pop())
mutate('extra test group',lambda z:z['tests']['children'].append(copy.deepcopy(z['tests']['children'][0])))
for i in range(8):
 for key,val in [('pass',5),('fail',1),('error',1),('broken',1),('failures',['caught']),('name','wrong')]:
  mutate(f'test child {i} {key}',lambda z,i=i,k=key,v=val:z['tests']['children'][0]['children'][i].__setitem__(k,v))
for key,val in [('pass',113),('error',1),('broken',1)]:mutate('recovery test '+key,lambda z,k=key,v=val:z['tests']['children'][1].__setitem__(k,v))
ck('missing raw refused',rejects(lambda:oracle.test_results({},'integration')))
config=control.config('integration');ck('config preview exact',config==rd(D/'config-preview.json'))
ck('60 inclusive inner52',config['seconds']==60 and control.guard_command(config,D/'fake',100.)[-len(config['command']):]==config['command'] and '--deadline' in control.guard_command(config,D/'fake',100.) and '152.0' in control.guard_command(config,D/'fake',100.))
for phase in ['red','green2','cost','../integration']:ck('phase refused '+phase,rejects(lambda p=phase:control.config(p)))
r=dict(accepted=True,findings=[],scope='offline preparation',pins_sha256=sha(D/'preparation-pins.json'),sha256={str(D/'preparation-pins.json'):sha(D/'preparation-pins.json')})
control.verify_review(r,D/'preparation-pins.json',list(r['sha256']),'offline preparation');ck('review verifier positive',True)
for key,val in [('accepted',False),('findings',['x']),('scope','exact-stage admission'),('pins_sha256','bad'),('sha256',{})]:
 q=copy.deepcopy(r);q[key]=val;ck('review refuses '+key,rejects(lambda q=q:control.verify_review(q,D/'preparation-pins.json',list(r['sha256']),'offline preparation')))
ck('environment exact',{k:os.environ.get(k) for k in rd(D/'environment.json')}==rd(D/'environment.json'))
ck('no integration stage',not Path(config['stage']).exists());ck('no runs',not (D/'runs').exists())
h=rd(D/'host.json');groups=h['groups'];boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[];unreadable=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  z=(p/'stat').read_text().rsplit(')',1)[1].split();comm=(p/'comm').read_text().strip();exe=''
  try:exe=str((p/'exe').resolve(strict=True))
  except PermissionError:unreadable.append(int(p.name))
  except FileNotFoundError:pass
  if int(z[2]) in groups or int(z[3]) in groups or comm.lower().startswith('julia') or Path(exe).name.lower().startswith('julia'):
   matches.append(dict(pid=int(p.name),pgid=int(z[2]),sid=int(z[3]),start_ticks=int(z[19]),comm=comm,exe=exe,boot_id=boot))
 except (FileNotFoundError,ProcessLookupError):pass
ck('216 groups and sessions none',len(groups)==len(set(groups))==216 and not matches)
ck('same Linux boot observation',boot==h['boot_id'])
details['host']=dict(boot_id=boot,groups=groups,matches=matches,unreadable_exe_pids=unreadable,scope='Read-only proc scan; no Windows restart-cause inference')
details['counts']=dict(preparation_pins=len(pins),baseline=len(base),source_check_bindings=867,overlay=len(new),assertions=162,public=48,recovery=29,options=85)
details['runtime']='UNEXECUTED; no Julia parse/query/import/compile/numerics or stage/seal/guard invocation'
result=dict(all_passed=all(checks.values()),checks=checks,failed=[n for n,v in checks.items() if not v],details=details)
with (D/'independent-review-checks.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=result['all_passed'],checks=len(checks),failed=result['failed'],counts=details['counts'])))
if not result['all_passed']:sys.exit(1)
