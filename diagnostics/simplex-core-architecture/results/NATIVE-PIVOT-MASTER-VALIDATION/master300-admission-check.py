"""Independent actual-master admission: Python/Git reads only; never launch Julia.
Writes only new review evidence and, after every gate, the exact admission.
"""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time,ast,fcntl
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
D=R/'diagnostics/simplex-core-architecture/results/NATIVE-PIVOT-MASTER-READINESS'
E=D.parent/'NATIVE-PIVOT-MASTER-VALIDATION'
Q=D.parent/'NATIVE-PIVOT-PRODUCTION-INTEGRATION-PREPARATION'
W=Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl')
M=Path('/home/jspitz/JSimplex.jl')
BASE='6f68e24e8ddac42b948da8fcc2d636c010751194'
COMMIT='26e2291745999f485a74f643298ca997d65c7205'
HEAD='362b1a9da0338f33cb3c55807f6fb0e49d9c875b'
RUN=D/'runs/master300';SP=RUN/'sealed.json'
checks=[]
def need(v,label):
 checks.append({'name':label,'passed':bool(v)})
 if not v: raise ValueError(label)
def rd(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def path(n):return Path(n) if Path(n).is_absolute() else R/n
def git(*args,cwd=R):return subprocess.check_output(['git',*args],cwd=cwd,text=True).strip()
def save(p,v):
 with Path(p).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
def host(groups):
 boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 matches=[];unreadable=[];processes=[]
 for p in Path('/proc').glob('[0-9]*'):
  try:
   fields=(p/'stat').read_text().rsplit(')',1)[1].split();comm=(p/'comm').read_text().strip()
   try:exe=str((p/'exe').resolve(strict=True))
   except PermissionError:exe=None;unreadable.append(int(p.name))
   except FileNotFoundError:exe=None
   try:command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
   except PermissionError:command=None
   v=dict(pid=int(p.name),pgid=int(fields[2]),sid=int(fields[3]),start_ticks=int(fields[19]),boot_id=boot,command=command,comm=comm,exe=exe,state=fields[0])
   processes.append(v)
   if v['pgid'] in groups or v['sid'] in groups or comm.lower().startswith('julia') or (exe and Path(exe).name.lower().startswith('julia')):matches.append(v)
  except (FileNotFoundError,ProcessLookupError):pass
 mem={s.split(':')[0]:int(s.split()[1]) for s in Path('/proc/meminfo').read_text().splitlines()}
 return dict(time=time.time(),boot_id=boot,head=git('rev-parse','HEAD'),master=git('rev-parse','master'),groups=groups,matches=matches,processes=processes,reviewer=next(v for v in processes if v['pid']==os.getpid()),unreadable_exe_pids=unreadable,memory=dict(available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree']),scope='All visible stat/comm and readable exe; inaccessible system exe links are a visibility limit')
def main():
 s=rd(SP);sp_hash=sha(SP);cfg=rd(RUN/'config.json');prep=rd(D/'preparation-pins.json');review=rd(D/'review-final.json');prod=rd(D/'production-commit.json');tree=rd(D/'production-tree.json');integration=rd(E/'integration.json')
 need(s['phase']=='master300' and s['master']==COMMIT and s['head']==HEAD,'Exact phase/master/diagnostic HEAD')
 need(set(p.name for p in RUN.iterdir())=={'sealed.json','config.json','host.json'},'No attempt/reservation/output/admission yet')
 need(s['files']==sorted(set(s['files'])) and all(Path(p).is_absolute() for p in s['files']),'Unique sorted absolute runtime paths')
 need(s['inputs']==[] and s['trees']==[str(W/'src'),str(W/'test')],'Exact source/test tree coverage')
 need(len(prep['sha256'])==4966 and set(prep['sha256'])==set(rd(D/'required-paths.json')['paths']),'Exact 4966 canonical readiness membership')
 need(review['accepted'] is True and review['findings']==[] and review['scope']=='production commit readiness' and review['production_commit']==COMMIT,'Readiness scope accepted only as predecessor')
 need(review['pins_sha256']==sha(D/'preparation-pins.json'),'Readiness manifest hash')
 need(set(review['sha256'])==set(prep['sha256'])|{str(D/'preparation-pins.json')},'Exact canonical review keys plus manifest')
 for n,h in prep['sha256'].items():need(sha(path(n))==h==review['sha256'][n],'Readiness hash '+n)
 need(review['sha256'][str(D/'preparation-pins.json')]==sha(D/'preparation-pins.json'),'Readiness manifest self binding')
 for n,h in review['evidence_sha256'].items():need(sha(path(n))==h,'Readiness evidence '+n)
 runtime=rd(D/'runtime-inputs.json')['inventory']
 envfiles=rd(D/'environment-files.json')
 expected_files={str(path(n)) for n in prep['sha256']}|{str(D/'preparation-pins.json'),str(D/'review-final.json')}|set(runtime)|{str(W/n) for n in tree['sha256']}|set(envfiles)|{str(RUN/'host.json'),str(RUN/'config.json')}
 need(set(s['files'])==expected_files,'Independent exact final seal membership')
 actual_paths=set(s['files'])
 for rootname in s['trees']:
  root=Path(rootname);need(root.is_dir() and not root.is_symlink(),'Real tree '+rootname)
  for p in root.rglob('*'):
   need(not(p.is_symlink() and (p.is_dir() or not p.exists())),'No directory/dangling tree symlink '+str(p))
   if p.is_file():actual_paths.add(str(p))
 need(actual_paths==set(s['inventory'])==set(s['files']),'Complete inventory including all tree members')
 actual={}
 for n in sorted(actual_paths):
  actual[n]={'resolved':str(Path(n).resolve(strict=True)),'sha256':sha(n)}
  need(actual[n]==s['inventory'][n],'Sealed resolved path and hash '+n)
 need(len(runtime)==606,'606 external runtime bindings')
 for n,v in runtime.items():need(actual[n]==v,'External runtime '+n)
 need(git('rev-parse','HEAD')==HEAD and git('rev-parse','master')==COMMIT,'Fresh diagnostic/master refs')
 need(git('rev-parse','HEAD',cwd=W)==git('rev-parse','HEAD',cwd=M)==COMMIT,'Isolated and actual master checkout HEAD')
 need(git('symbolic-ref','--short','HEAD',cwd=M)=='master','Main checkout on master')
 need(git('rev-parse',COMMIT+'^')==BASE,'Fast-forward exact parent')
 need(git('ls-remote','origin','refs/heads/master')==BASE+'\trefs/heads/master','Remote master remains base')
 need(git('diff-tree','--no-commit-id','--name-only','-r',COMMIT).splitlines()==prod['names']==integration['names'],'Exactly ten changed paths')
 need(len(prod['names'])==10 and sum(n.startswith('src/') for n in prod['names'])==7,'Seven source and three test destinations')
 need(integration['all_passed'] is True and integration['parent']==BASE and integration['master']==COMMIT,'Integration record')
 rows=git('ls-tree','-r',COMMIT).splitlines();blobs={row.split('\t',1)[1]:row.split()[2] for row in rows}
 need(blobs==tree['git_blobs'] and set(blobs)==set(tree['sha256']),'Complete 3533 tracked Git blob tree')
 need(len(blobs)==3533 and git('ls-files',cwd=W).splitlines()==sorted(blobs),'Complete tracked membership')
 for n,h in tree['sha256'].items():
  data=(W/n).read_bytes();blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
  need(hashlib.sha256(data).hexdigest()==h and blob==blobs[n],'Production tracked hash/blob '+n)
 payload=rd(Q/'payload-manifest.json')['files']
 need({v['destination'] for v in payload}==set(prod['names']),'Qualified payload membership')
 for v in payload:
  n=v['destination'];need(sha(W/n)==sha(M/n)==sha(path(v['source']))==sha(path(v['payload']))==v['sha256']==prod['sha256'][n],'Qualified/current-master payload '+n)
  need(blobs[n]==prod['blobs'][n]==integration['git_blobs'][n],'Integration Git blob '+n)
 for n,h in integration['user_sha256'].items():need(sha(M/n)==h,'Preserved user file '+n)
 need(git('status','--porcelain',cwd=M)==integration['main_status'],'Preserved user checkout status')
 need(not git('diff','--name-only') and not git('diff','--cached','--name-only'),'Clean diagnostic tracked tree')
 need(not git('diff','--name-only',cwd=W) and not git('diff','--cached','--name-only',cwd=W),'Clean tested tracked tree')
 need(set(git('ls-files','--others','--exclude-standard',cwd=W).splitlines())=={'Manifest.toml','LocalPreferences.toml'},'Only prescribed untracked tested environment')
 for n,v in envfiles.items():need(not Path(n).is_symlink() and sha(n)==sha(v['source'])==v['sha256'],'Copied external environment '+n)
 env=rd(D/'environment.json');need({k:os.environ.get(k) for k in env}==env,'Exact loading environment')
 wrapper='/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh'
 command=['/bin/bash',wrapper,'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--history-file=no','--project='+str(W),str(D/'master-driver.jl'),str(RUN/'output'),str(W)]
 expected_cfg=dict(phase='master300',seconds=300,expected_exit=0,stage=str(W),run=str(RUN),output=str(RUN/'output'),command=command,production_commit=COMMIT)
 need(s['config']==cfg==expected_cfg,'Exact command/cap/runtime/project/output contract')
 need(not (RUN/'output').exists(),'Unused output path')
 expected=rd(D/'expected-tests.json')
 names=['options_and_copy_intent','backend_owned_policy','private_spare_copy_and_failure','precision_and_factory_dispatch','Native pivot policy public integration','Native pivot policy private recovery'];counts=[4946,35,1568,245,48,114]
 need(expected['groups']==list(map(list,zip(names,counts))) and expected['assertions']==sum(counts)==6956,'Six exact groups and 6956 assertions')
 need(expected['public_children']==[[mode+' / '+policy,6] for mode in ['pfi','forrest_tomlin','suhl_suhl','bartels_golub'] for policy in ['default','threshold_one']],'Exact eight public children of six')
 driver=(D/'master-driver.jl').read_text();test=(W/'test/native_pivot_integration_tests.jl').read_text()
 for name,count in zip(names,counts):need('"'+name+'"=>'+str(count) in driver,'Driver exact count '+name)
 need('(\"native_pivot_policy_tests.jl\",\"native_pivot_integration_tests.jl\")' in driver,'Fixed test inclusion order')
 need('time_limit=5.0, iteration_limit=100' in test and 'result.status == OPTIMAL' in test,'Unchanged fixed five-second numerical solver deadline')
 for n in ['control.py','guard.py','supervisor.py','launch.py','audit.py','oracle.py']:
  ast.parse((D/n).read_text());need(str(D/n) in actual,'Bound parsable controller '+n)
 # These are static guards; no controller, checker or oracle is executed here.
 fragments={
 'control.py':["seconds=cfg['seconds']-8","set(v.get('sha256',{}))==set(required)","'actual'"],
 'guard.py':['resource.RLIMIT_AS, (8 * 1024**3, 8 * 1024**3)',"sample['available_kib'] < 6 * 1024**2", "sample['swap_used_kib'] > 1024**2","JULIA_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1'","JULIA_PKG_PRECOMPILE_AUTO='0'",'start_new_session=True, preexec_fn=limits',"('pid','start_ticks','boot_id','command')",'int(fields[2]) == pgid or int(fields[3]) == pgid','os.pidfd_open(pid,0)','signal.pidfd_send_signal(fd,sig,None,0)',"pins_match(pins) and pins_path.is_file() and digest(pins_path) == pins_digest",'resource.RUSAGE_CHILDREN','fcntl.LOCK_EX | fcntl.LOCK_NB'],
 'supervisor.py':['started+limit-6','started+limit-2','started+limit-time.monotonic()',"record['elapsed_seconds']<=limit",'guard.same_identity(before,after)','owner=a'],
 'launch.py':["'actual-master exact-stage admission',phase","guard.pins_match(sealed)","not h['matches']","for k in ('head','master','boot_id')","one_attempt=True",'supervisor.run(cmd,log,cfg[\'output\'],started,cfg[\'seconds\'])'],
 'audit.py':["resources+[p['terminal_memory']]","for key in ['pgid','sid']","'Boot/start/command'","'Inclusive limit/cleanup'","test_results(raw,rd(D/'expected-tests.json'),rd(D/'loaded-paths.json'))","rd(D/'loaded-paths.json'))","'Failed test log'"],
 'oracle.py':["set(raw)=={'complete','fatal','loaded','threads','blas_threads','tests'}","raw['complete'] is False","type(raw['threads']) is int","type(raw['blas_threads']) is int","raw['loaded']==loaded and valid_node(raw['tests'])","raw['tests']['name']=='root'","raw['tests']['pass']==0","'BEGIN native_pivot_policy_tests.jl' in log","'Exact groups'","'Public tree'","'Public depth'","'Unexpected nested group'"]}
 # The control contract uses exact review checks; no broad guessed fragments.
 fragments['control.py'].remove("'actual'")
 for n,items in fragments.items():
  text=(D/n).read_text()
  for fragment in items:need(fragment in text,'Static safeguard '+n+': '+fragment)
 wrapper_text=Path(wrapper).read_text()
 need('--startup-file=no' in wrapper_text and 'ulimit -v 8388608' in wrapper_text and 'JULIA_PKG_OFFLINE=true' in wrapper_text,'Bound startup/VM/offline wrapper')
 loaded=rd(D/'loaded-paths.json');need(loaded['JSimplex']==str(W/'src/JSimplex.jl') and all(str(Path(n).resolve())==n and n in actual for n in loaded.values()),'Pinned exact loaded source paths')
 oldhost=rd(D/'host.json');sealedhost=rd(RUN/'host.json')
 need(s['groups']==sealedhost['groups']==oldhost['groups'] and len(s['groups'])==220,'All 220 historical groups AND sessions')
 fresh=host(s['groups'])
 need(fresh['matches']==[],'Fresh no Julia and no prior group/session member')
 need(all(fresh[k]==s[k]==sealedhost[k] for k in ['boot_id','head','master']),'Fresh matching boot/refs')
 need(fresh['reviewer']['start_ticks']>0 and bool(fresh['reviewer']['command']),'Fresh reviewer boot/start/command')
 need(fresh['memory']['available_kib']>=6*1024**2 and fresh['memory']['swap_used_kib']<=1024**2,'Fresh RAM>=6GiB and swap<=1GiB')
 lock=Path('/tmp')/('jsimplex-numerical-'+str(os.getuid())+'.lock')
 if lock.exists():
  with lock.open('r') as f:fcntl.flock(f,fcntl.LOCK_SH|fcntl.LOCK_NB);fcntl.flock(f,fcntl.LOCK_UN)
 need(True,'No currently held exclusive numerical lock (read-only probe)')
 need(sha(SP)==sp_hash,'Final seal byte identity')
 save(E/'master300-admission-host.json',fresh)
 result=dict(all_passed=True,scope='actual-master exact-stage admission',phase='master300',check_count=len(checks),checks=checks,sealed_files=len(actual),canonical_readiness_keys=len(prep['sha256']),production_tracked_files=len(blobs),runtime_files=len(runtime),pins_sha256=sp_hash,numerical_execution=False)
 save(E/'master300-admission-checks.json',result)
 print(json.dumps({k:v for k,v in result.items() if k!='checks'}))
if __name__=='__main__':
 try:main()
 except Exception as exc:
  save(E/'master300-admission-check-failure.json',dict(all_passed=False,error=repr(exc),checks=checks))
  raise
