from pathlib import Path
import ast,copy,hashlib,importlib.util,json,math,os,struct,subprocess,sys
sys.dont_write_bytecode=True
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');D=W/'diagnostics/dual-recovery-devex-cost-admission/2026-10-30'
P=W/'diagnostics/dual-recovery-devex-task4/2026-10-30';F=W/'diagnostics/dual-recovery-devex-green-fixture-preparation/2026-10-30';R=W/'diagnostics/dual-recovery-devex-green2-result/2026-10-30'
checks={};bindings={};facts={}
def sha(p):
 p=Path(p);h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 bindings[str(p)]=h.hexdigest();return h.hexdigest()
def read(p):sha(p);return json.loads(Path(p).read_text())
def ck(n,v):
 checks[n]=bool(v)
 if not v:raise AssertionError(n)
def git(*args):return subprocess.check_output(['git','-C',str(W),*args],text=True).strip()
pres=read(D/'preservation.json')
ck('526 immutable prior files',len(pres['frozen_publications'])==526)
for p,h in pres['frozen_publications'].items():ck('prior file '+p,sha(p)==h)
for p,a in pres['copies'].items():ck('exact helper copy '+p,sha(p)==sha(a['source'])==a['sha256'])
source=read(D/'source-check.json');ck('source check accepted19',source['accepted'] is True and len(source['checks'])==19 and all(x is True for x in source['checks'].values()))
for p,h in source['bindings'].items():ck('source recorded binding '+p,sha(p)==h)
for p in D.rglob('*'):
 if p.is_file():sha(p)
for p in D.rglob('*.py'):ck('AST only '+str(p),ast.parse(p.read_text()) is not None)
for folder,rel in [(W/'diagnostics/dual-recovery-devex-task4-red/2026-10-30','red'),(R,'green2')]:
 closure=read(folder/'closure.json');maps=closure['explicit_exact_copy_maps'];a=read(folder/rel/'audit.json')
 ck(rel+' canonical accepted',a['accepted'] is True)
 ck(rel+' summary',a['test_summary']==({'Pass':7,'Fail':1,'Total':8} if rel=='red' else {'Pass':5774,'Total':5774}))
 for p,h in a['bindings'].items():ck(rel+' portable audit '+p,sha(maps.get(p,p))==h)
 facts[rel+'_audit_bindings']=len(a['bindings']);facts[rel+'_copy_maps']=len(maps)
 if rel=='green2':
  review=read(folder/'review-final.json');ck('prior independent result scope',review['accepted'] is True and review['runtime_accepted'] is True and review['production_admission'] is False and review['cost_qualified'] is False)
  for p,h in review['bindings'].items():ck('prior independent mapped '+p,sha(maps.get(p,p))==h)
  facts['green2_independent_checks_read_only']=len(review['checks']);facts['green2_independent_bindings_verified']=len(review['bindings'])
bad=W/'diagnostics/dual-recovery-devex-task4-green/2026-10-30';bs=read(bad/'green/supervisor.json')
ck('failed original GREEN remains rejected',bs['accepted'] is False and bs['returncode']==1 and not (bad/'green/audit.json').exists())
durations=[]
for folder,phase,accepted in [(W/'diagnostics/dual-recovery-devex-task4-red/2026-10-30','red',True),(bad,'green',False),(R,'green2',True)]:
 c=read(folder/phase/'completion.json');ck('prior outcome '+phase,c['supervisor_accepted'] is accepted);durations.append(c['elapsed_inclusive_seconds'])
ck('exact consumed total',durations==[33.35953255696222,494.6009602919803,505.6401044019731] and sum(durations)==1033.6005972509156)
ck('remaining shared seconds',1800-sum(durations)==766.3994027490844)
for side in ('reference','candidate'):
 files={p.relative_to(P/'overlays'/side).as_posix():p for p in (P/'overlays'/side).rglob('*') if p.is_file()}
 ck(side+'74 file project',len(files)==74)
 if side=='reference':reference=files
 else:candidate=files
 for n,p in files.items():
  if side=='reference' and n.startswith('src/'):ck('reference source '+n,sha(p)==sha(W/n))
  if side=='candidate':ck('GREEN2 candidate '+n,sha(p)==sha(F/'prepared/overlays/candidate'/n))
ck('only three canonical source changes',sorted(n for n in reference if sha(reference[n])!=sha(candidate[n]))==['src/simplex_numerics.jl','src/simplex_pivot.jl','src/simplex_recovery.jl'])
contract=read(D/'contract.json');ck('driver unchanged',sha(P/'cost.jl')==contract['driver_sha256']);ck('reference unchanged',sha(P/'tests/reference.jl')==contract['reference_sha256'])
ck('entire original cost contract retained',contract['cost']==read(P/'contract.json')['cost'])
ck('no reservation or runtime',not (W/'.superpowers/dual-recovery-devex-task4/cost-1').exists())
ck('no source modifications',not git('diff','master','HEAD','--','src','test','Project.toml','.github'))
ck('clean tracked worktree',not git('diff','HEAD','--name-only') and not git('diff','--cached','--name-only'))
ck('HEAD and master exact',git('rev-parse','HEAD')=='6251dafd8be8f94ba4409f560692a893ced7d6a0' and git('rev-parse','master')==git('rev-parse','origin/master')=='c0fa748ffa61ccb7c1caaf248c40324f60bc737b')
# Definitions-only imports of selected NEW pure functions. No submitted main or guard import.
sys.path.insert(0,str(D));import common as C;import cost_checks as K;import audit as A
ck('pure imports no guard',not any(n in sys.modules for n in ('guard_reviewed','supervisor_reviewed','entry_gate','seal','launch','close','offline_tests','offline_tests_final')))
def bits(v,T):return struct.pack('>f' if T=='Float32' else '>d',v).hex()
def make(side):
 cases=[]
 for T in ('Float32','Float64'):
  for layout in ('sparse','dense'):
   matrix=[]
   for j in range(1,65):
    for i in range(1,65):
     v=64 if i==j else (-(1+(i+2*j)%5)/64 if (i+j)%2==0 else (1+(i+2*j)%5)/64) if layout=='dense' or abs(i-j)==1 else 0
     matrix.append(bits(v,T))
   ck('independent matrix '+T+layout,matrix==K.expected_matrix(T,layout))
   for bad in (False,True):
    profile=dict(seconds=.002,bytes=128,events=2,gc_seconds=0.,compile_seconds=0.,recompile_seconds=0.)
    samples=[dict(profile,index=i,finite=True,reliable=not bad,owners_preserved=True,point_bits=[bits(.5 if bad else 1,T)]+[bits(0,T)]*63,rhs_bits=matrix[::64],absolute_bits=bits(32 if bad else 0,T),relative_bits=bits(1/3 if bad else 0,T),solve_entries=int(bad),stop_entries=int(bad)) for i in range(1,8)]
    cases.append(dict(type=T,layout=layout,unreliable=bad,dimension=64,nnz=sum(x!=bits(0,T) for x in matrix),matrix_bits=matrix,policy_solve_tolerance_bits=bits(256*(2**(-23 if T=='Float32' else -52)),T),warm=[dict(profile) for _ in range(3)],samples=samples,preparation=dict(profile),post_warm_gc=dict(profile),retained_julia_bytes=4096,solve_entries_total=10*bad,stop_entries_total=10*bad))
 return dict(side=side,cases=cases)
ref=make('reference');can=make('candidate');ck('independent reference schema',K.check_cost(ref,'reference'));ck('independent candidate schema',K.check_cost(can,'candidate'))
ck('256eps primary source', 'default_solve = exact ? zero(T) : T(256)*eps(T)' in (W/'src/simplex_numerics.jl').read_text())
ck('explicit tolerance hex anchors',[bits(256*2**-23,'Float32'),bits(256*2**-52,'Float64')]==['38000000','3d30000000000000'])
ck('valid paired output',K.comparison_data(ref,can)['accepted'] is True)
for case in range(8):
 for field in ('bytes','events','retained_julia_bytes'):
  changed=copy.deepcopy(can)
  if field=='retained_julia_bytes':changed['cases'][case][field]+=1
  else:
   for s in changed['cases'][case]['samples']:s[field]+=1
  compared=K.comparison_data(ref,changed)
  ck('full failed pair case'+str(case)+field,compared['accepted'] is False and len(compared['cases'])==8 and not all(compared['cases'][case]['gates'].values()))
for field,val in [('finite',1),('reliable',1),('owners_preserved',1),('index',True),('bytes',True),('events',1.0),('seconds',float('inf')),('compile_seconds',.001),('recompile_seconds',.001),('point_bits',[]),('rhs_bits',[]),('absolute_bits','0'),('relative_bits','0'),('stop_entries',False),('solve_entries',False)]:
 changed=copy.deepcopy(ref);changed['cases'][0]['samples'][0][field]=val
 try:K.check_cost(changed,'reference')
 except (ValueError,KeyError):rejected=True
 else:rejected=False
 ck('reject malformed sample '+field,rejected)
for field,val in [('type','BigFloat'),('layout','other'),('dimension',True),('nnz',True),('unreliable',0),('policy_solve_tolerance_bits','0'),('matrix_bits',[]),('samples',[]),('warm',[]),('retained_julia_bytes',True),('solve_entries_total',False),('stop_entries_total',False)]:
 changed=copy.deepcopy(ref);changed['cases'][0][field]=val
 try:K.check_cost(changed,'reference')
 except (ValueError,KeyError):rejected=True
 else:rejected=False
 ck('reject malformed case '+field,rejected)
log='Test Summary: | Pass Total Time\nTASK4_COST | 272 272 1.0s\nTASK4_COST_COMPLETED reference\n'
ck('flat ordinary272 parser',A.ordinary(log,'reference-cost')=={'Pass':272,'Total':272})
for i,v in enumerate([log+log,log.replace('reference','candidate'),log.replace('272 272','271 271'),log+'ERROR: fixture\n',log.replace('TASK4_COST_COMPLETED reference','')]):
 try:A.ordinary(v,'reference-cost')
 except ValueError:rejected=True
 else:rejected=False
 ck('ordinary mutation'+str(i),rejected)
used=sum(durations);done=dict(elapsed_inclusive_seconds=100.,total_inclusive_seconds=used+100.,limit_seconds=1800,supervisor_accepted=True);sup=dict(accepted=True,returncode=0,elapsed_seconds=99.,soft_timeout=False,hard_timeout=False,child_kill=False,guard_term=False,guard_kill=False,abnormal_cleanup_attempted=False,child_cleanup_attempted=False);proc=dict(returncode=0,reason='exit0',pins_unchanged=True,command=C.command('reference-cost'))
A.process(done,sup,proc,'reference-cost',used);ck('valid clock process',True)
for field,val in [('elapsed_inclusive_seconds',True),('total_inclusive_seconds',100.),('total_inclusive_seconds',1801.),('limit_seconds',True),('supervisor_accepted',False)]:
 q=dict(done);q[field]=val
 try:A.process(q,sup,proc,'reference-cost',used)
 except ValueError:rejected=True
 else:rejected=False
 ck('clock rejects '+field+repr(val),rejected)
# Fresh read-only full process-group/session census, independently implemented.
h=read(D/'host.json')['host'];boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();ck('same boot',boot==h['boot_id']);groups=set(h['checked_groups']);ck('736 old groups',len(groups)==736)
conflicts=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text();a=s[s.rfind(')')+2:].split();comm=(p/'comm').read_text().strip()
  if comm.lower().startswith('julia') or int(a[2]) in groups or int(a[3]) in groups:conflicts.append(dict(pid=int(p.name),pgid=int(a[2]),sid=int(a[3]),comm=comm))
 except (FileNotFoundError,ProcessLookupError):pass
ck('fresh full groups sessions and no Julia',not conflicts)
m={s.split(':')[0]:int(s.split()[1]) for s in Path('/proc/meminfo').read_text().splitlines()};memory=dict(available_kib=m['MemAvailable'],swap_used_kib=m['SwapTotal']-m['SwapFree']);ck('fresh resource bounds',memory['available_kib']>=6*1024**2 and memory['swap_used_kib']<=1024**2)
facts.update(base_seconds=used,remaining_seconds=1800-used,groups=len(groups),boot_id=boot,memory=memory,prior_durations=durations,new_submitted_test_methods_read_only=[11,13],original_source_check_bindings_read=546,new_pure_synthetic_test_data_not_numerical=True)
sha(__file__)
result=dict(accepted=True,scope='offline_preparation',runtime_qualified=False,numerical_admission=False,checks=checks,bindings=bindings,facts=facts,findings=[])
with Path('/tmp/devex-cost-preparation-review-check-result.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(accepted=True,checks=len(checks),bindings=len(bindings),facts=facts)))
