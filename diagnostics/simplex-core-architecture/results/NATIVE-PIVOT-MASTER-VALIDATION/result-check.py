"""Independent result reviewer. Read saved data/Git/proc only; never Julia or old scripts."""
from pathlib import Path
import json, hashlib, subprocess, os, sys, time, math, tomllib
E=Path(__file__).resolve().parent;D=E.parent/'NATIVE-PIVOT-MASTER-READINESS';R=D.parents[3];Q=D.parent/'NATIVE-PIVOT-PRODUCTION-INTEGRATION-PREPARATION';A=D/'runs/master300';O=A/'output'
BASE='6f68e24e8ddac42b948da8fcc2d636c010751194';MASTER='26e2291745999f485a74f643298ca997d65c7205';HEAD='362b1a9da0338f33cb3c55807f6fb0e49d9c875b';checks=[]
def ck(v,m):
 if not v: raise AssertionError(m)
 checks.append(m)
def rd(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def path(p):return Path(p) if Path(p).is_absolute() else R/p
def bind(j,field='sha256'):
 for n,h in j[field].items():ck(sha(path(n))==h,'binding '+n)
def git(*a,cwd=R):return subprocess.check_output(['git',*a],cwd=cwd,text=True).strip()
def write(p,j):
 with p.open('x') as f:json.dump(j,f,indent=2);f.write('\n')
def inventory(j):
 files=set(j['files']);ck(len(files)==len(j['files']),'unique files')
 for root in j['trees']:
  root=Path(root);ck(root.is_dir() and not root.is_symlink(),'tree root '+str(root))
  for p in root.rglob('*'):
   ck(not(p.is_symlink() and (p.is_dir() or not p.exists())),'no directory/dangling symlink '+str(p))
   if p.is_file():files.add(str(p))
 ck(files==set(j['inventory']),'exact enumerated inventory')
 for n,v in j['inventory'].items():
  ck(Path(n).is_absolute(),'absolute inventory '+n)
  ck(str(Path(n).resolve(strict=True))==v['resolved'],'resolved '+n)
  ck(sha(n)==v['sha256'],'inventory SHA '+n)
s=rd(A/'sealed.json');lp=rd(A/'launch-pins.json');adm=rd(A/'admission.json');cfg=rd(A/'config.json');prod=rd(D/'production-commit.json');tree=rd(D/'production-tree.json');W=Path(prod['worktree']);main=Path('/home/jspitz/JSimplex.jl')
ck(git('rev-parse','HEAD')==HEAD==s['head']==adm['diagnostic_head'],'diagnostic head')
ck(git('rev-parse','master')==MASTER==s['master']==adm['production_commit']==prod['commit']==tree['commit'],'actual master')
ck(git('rev-parse','HEAD',cwd=W)==git('rev-parse','HEAD',cwd=main)==MASTER,'both actual checkouts')
ck(git('rev-list','--parents','-n','1',MASTER).split()==[MASTER,BASE],'exact one parent')
ck(git('ls-remote','origin','refs/heads/master')==BASE+'\trefs/heads/master','remote still original base')
ck(git('rev-parse','HEAD^{tree}',cwd=W)==git('rev-parse','master^{tree}'),'exact actual master tree')
ck(not git('diff','--name-only',cwd=W) and not git('diff','--cached','--name-only',cwd=W),'isolated tracked clean')
ck(not git('diff','--name-only') and not git('diff','--cached','--name-only'),'diagnostic tracked clean')
ck(git('diff-tree','--no-commit-id','--name-only','-r',MASTER).splitlines()==prod['names'] and len(prod['names'])==10,'exact ten-file change')
blobs={line.split('\t',1)[1]:line.split('\t',1)[0].split()[2] for line in git('ls-tree','-r',MASTER).splitlines()}
ck(set(blobs)==set(tree['sha256'])==set(tree['git_blobs'])==set(git('ls-files',cwd=W).splitlines()),'full tracked membership')
for n,h in tree['sha256'].items():
 ck(sha(W/n)==h,'tracked SHA '+n);ck(blobs[n]==tree['git_blobs'][n],'tracked blob '+n)
integ=rd(E/'integration.json');before=rd(E/'integration-before.json')
ck(integ['all_passed'] and integ['master']==MASTER and integ['parent']==BASE and integ['names']==prod['names'],'integration identity')
bind(integ)
for item in rd(Q/'payload-manifest.json')['files']:
 n=item['destination'];ck(blobs[n]==prod['blobs'][n]==integ['git_blobs'][n],'changed blob '+n)
 for p in [W/n,main/n,path(item['payload']),path(item['source'])]:ck(sha(p)==item['sha256']==prod['sha256'][n],'payload source exact '+str(p))
 ck(hashlib.sha256(subprocess.check_output(['git','show',MASTER+':'+n],cwd=R)).hexdigest()==item['sha256'],'commit bytes '+n)
ck(integ['user_sha256']==before['user_sha256'],'user previous identity')
for n,h in integ['user_sha256'].items():ck(sha(main/n)==h,'user preserved '+n)
ck(git('status','--porcelain',cwd=main)==integ['main_status']==rd(E/'main-before.json')['status'],'main status preserved')
prep=rd(D/'preparation-pins.json');ready=rd(D/'review-final.json');bind(prep);bind(ready)
ck(set(prep['sha256'])==set(rd(D/'required-paths.json')['paths']),'canonical readiness membership')
ck(ready['accepted'] and ready['findings']==[] and ready['scope']=='production commit readiness' and ready['pins_sha256']==sha(D/'preparation-pins.json'),'readiness scope')
ck(set(ready['sha256'])==set(prep['sha256'])|{str(D/'preparation-pins.json')},'exact readiness review membership')
expected_files={str(path(n)) for n in prep['sha256']}|{str(D/'preparation-pins.json'),str(D/'review-final.json')}|set(rd(D/'runtime-inputs.json')['inventory'])|{str(W/n) for n in tree['sha256']}|set(rd(D/'environment-files.json'))|{str(A/'host.json'),str(A/'config.json')}
ck(set(s['files'])==expected_files and len(expected_files)==4926,'independently reconstructed exact seal files')
ck(s['trees']==[str(W/'src'),str(W/'test')] and s['inputs']==[],'exact sealed trees and no inputs')
inventory(s);inventory(lp)
ck(set(lp['files'])==set(s['files'])|{str(A/'sealed.json'),str(A/'admission.json'),str(A/'prehost.json')},'exact launch files')
ck(lp['trees']==s['trees'] and lp['inputs']==[],'exact launch trees')
ck(all(lp['inventory'][n]==v for n,v in s['inventory'].items()),'seal launch identical inventories')
ck(rd(O/'pins.json')==lp,'output launch pins identical')
for n,v in rd(D/'runtime-inputs.json')['inventory'].items():ck(s['inventory'][n]==v,'runtime identity '+n)
for n,v in rd(D/'environment-files.json').items():ck(not Path(n).is_symlink() and sha(n)==v['sha256']==sha(v['source']),'environment file '+n)
ck(set(git('ls-files','--others','--exclude-standard',cwd=W).splitlines())=={'Manifest.toml','LocalPreferences.toml'},'exact external environment files')
ck({k:os.environ.get(k) for k in rd(D/'environment.json')}==rd(D/'environment.json'),'loading environment')
ck(adm['accepted'] is True and adm['findings']==[] and adm['scope']=='actual-master exact-stage admission' and adm['phase']=='master300','fresh admission scope')
ck(adm['pins_sha256']==sha(A/'sealed.json') and set(adm['sha256'])==set(s['files'])|{str(A/'sealed.json')},'exact admission seal binding')
bind(adm);bind(adm,'evidence_sha256')
ck(cfg==s['config'] and cfg['phase']=='master300' and cfg['seconds']==300 and cfg['expected_exit']==0 and cfg['production_commit']==MASTER,'exact phase cap commit')
command=['/bin/bash','/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh','--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--history-file=no','--project='+str(W),str(D/'master-driver.jl'),str(O),str(W)]
ck(cfg['command']==command and cfg['output']==str(O) and cfg['stage']==str(W) and cfg['run']==str(A),'exact command/output')
ck({p.name for p in O.iterdir()}=={'pins.json','current.json','process.json','resources.jsonl','run.log','raw.toml'} and all(p.is_file() and not p.is_symlink() for p in O.iterdir()),'all six exact outputs')
ck({p.name for p in (D/'runs').iterdir()}=={'master300'},'one attempt no master600')
p=rd(O/'process.json');cur=rd(O/'current.json');inv=rd(A/'invocation.json');sup=inv['supervisor'];res=rd(A/'reservation.json')
ck(p['returncode']==0 and p['reason']=='exit0' and p['pins_unchanged'] is True and 'error' not in p,'success process')
ck(sup['returncode']==0 and sup['accepted'] is True and 'cleanup_error' not in sup and all(sup[k] is False for k in ['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill']),'success supervisor')
ck(p['command']==cur['command']==inv['command']==command and p['cwd']==cur['cwd']==str(R),'process command cwd')
ck(p['pins_sha256']==cur['pins_sha256']==inv['pins_sha256']==sha(A/'launch-pins.json'),'launch hash identity')
ck(res==dict(one_attempt=True,phase='master300',command=command,pins_sha256=sha(A/'launch-pins.json'),review_sha256=sha(A/'admission.json'),max_seconds=300),'one attempt reservation')
ck(inv['reservation_sha256']==sha(A/'reservation.json') and inv['review_sha256']==sha(A/'admission.json'),'invocation reservation admission link')
gcmd=[inv['python'],'-B',str(D/'guard.py'),'run',str(A/'launch-pins.json'),str(O),'--seconds','292','--deadline',str(inv['monotonic_start']+292),'--expected-exit','0','--',*command]
ck(inv['guard_command']==gcmd and Path(inv['python']).resolve()==Path(sys.executable).resolve(),'exact inner deadline command')
ck(cur['runner']==p['runner']==sup['guard_identity'] and cur['child']==p['child'],'exact guard child identity chain')
for role,cmd in [('runner',gcmd),('child',command)]:
 z=p[role];ck(z['pid']==z['pgid']==z['sid'] and z['start_ticks']>0 and z['boot_id']==s['boot_id'] and z['command']==' '.join(cmd)+' ','identity boot start command '+role)
ck(p['runner']['start_ticks']<=p['child']['start_ticks'],'identity temporal order')
for v in [inv['elapsed_seconds'],sup['elapsed_seconds'],p['elapsed_including_launch']]:ck(type(v) in (int,float) and math.isfinite(v) and 0<=v<=300,'inclusive cap')
ck(p['elapsed_including_launch']<=292 and inv['elapsed_seconds']>=sup['elapsed_seconds']>=p['elapsed_including_launch'],'inner and outer duration ordering')
ck(json.loads((A/'launcher.log').read_text())==p,'launcher process log equality')
log=(O/'run.log').read_text();ck(log=='BEGIN native_pivot_policy_tests.jl\nEND native_pivot_policy_tests.jl\nBEGIN native_pivot_integration_tests.jl\nEND native_pivot_integration_tests.jl\n','exact failure-free progress log')
raw=tomllib.loads((O/'raw.toml').read_text());expected=rd(D/'expected-tests.json')
ck(set(raw)=={'complete','fatal','threads','blas_threads','tests','loaded'} and raw['complete'] is True and raw['fatal']=='','raw exact complete schema')
ck(type(raw['threads']) is int and type(raw['blas_threads']) is int and raw['threads']==raw['blas_threads']==1 and raw['loaded']==rd(D/'loaded-paths.json'),'loaded paths and one thread')
ck(raw['loaded']['JSimplex']==str(W/'src/JSimplex.jl'),'actual master loaded')
def node(t):
 ck(set(t)=={'name','pass','fail','error','broken','failures','children'} and type(t['name']) is str,'node exact schema '+t['name'])
 ck(all(type(t[k]) is int and t[k]>=0 for k in ['pass','fail','error','broken']) and t['fail']==t['error']==t['broken']==0 and t['failures']==[],'node exact pass '+t['name'])
 ck(type(t['children']) is list,'children list '+t['name'])
 return t['pass']+sum(node(c) for c in t['children'])
ck(node(raw['tests'])==6956==expected['assertions'] and raw['tests']['name']=='root' and raw['tests']['pass']==0,'exact 6956 root')
ck([[t['name'],node(t)] for t in raw['tests']['children']]==expected['groups'],'exact six groups')
for t in raw['tests']['children']:
 if t['name']=='Native pivot policy public integration':ck(t['pass']==0 and [[c['name'],node(c)] for c in t['children']]==expected['public_children'] and all(c['children']==[] for c in t['children']),'eight exact public children')
 else:ck(t['children']==[],'flat permanent group '+t['name'])
samples=[json.loads(l) for l in (O/'resources.jsonl').read_text().splitlines()]
ck(len(samples)==124,'124 samples')
for z in samples+[p['terminal_memory']]:ck(z['available_kib']>=6*1024**2 and 0<=z['swap_used_kib']<=1024**2,'sample resource guard')
ck(all(math.isfinite(z['elapsed']) and 0<=z['elapsed']<=292 for z in samples) and all(x['elapsed']<y['elapsed'] for x,y in zip(samples,samples[1:])),'resource elapsed monotonic bounded')
ck(min(z['available_kib'] for z in samples)==20914480 and max(z['swap_used_kib'] for z in samples)==0 and p['terminal_memory']=={'available_kib':23119284,'swap_used_kib':0} and p['child_maxrss_kib']==1984176,'exact reported resources')
for z in samples:
 for line in z['child_memory']:
  if line.startswith(('VmPeak:','VmSize:')):ck(int(line.split()[1])<=8*1024**2,'sample VM cap')
audit=rd(A/'audit.json');ck(audit['all_passed'] is True and audit['pure_timeout'] is False and audit['error']=='' and audit['phase']=='master300','original audit pass')
ck(set(audit['sha256'])=={str(q) for q in A.rglob('*') if q.is_file() and q.name!='audit.json'},'audit complete original attempt membership');bind(audit)
post=rd(E/'master300-postcheck.json');ck(post['all_passed'] is True and len(post['checks'])==10 and all(v is True for v in post['checks'].values()),'ten postcheck gates');bind(post)
ck(audit['result']==post['result'] and post['result']['assertions']==6956 and post['result']['groups']==expected['groups'],'audit postcheck raw agreement')
ck(post['resource_summary']['inclusive_elapsed_seconds']==inv['elapsed_seconds']==125.31696266899235,'reported inclusive duration')
groups=set(s['groups']);ck(len(groups)==220,'220 prior groups sessions')
for role in ['runner','child']:groups.update(p[role][k] for k in ['pgid','sid'])
for n in ['host.json','prehost.json','posthost.json']:
 h=rd(A/n);ck(h['matches']==[] and all(h[k]==s[k] for k in ['head','master','boot_id']),'saved host identity '+n)
 ck(set(s['groups'])<=set(h['groups']),'saved prior groups '+n)
ck(groups<=set(rd(A/'posthost.json')['groups'])<=set(post['host']['groups']) and post['host']['matches']==[],'all new groups sessions closure')
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[];unreadable=[];processes=0
for pp in Path('/proc').glob('[0-9]*'):
 try:
  fields=(pp/'stat').read_text().rsplit(')',1)[1].split();comm=(pp/'comm').read_text().strip();exe='';processes+=1
  try:exe=str((pp/'exe').resolve(strict=True))
  except PermissionError:unreadable.append(int(pp.name))
  except FileNotFoundError:pass
  if int(fields[2]) in groups or int(fields[3]) in groups or comm.lower().startswith('julia') or Path(exe).name.lower().startswith('julia'):matches.append(dict(pid=int(pp.name),pgid=int(fields[2]),sid=int(fields[3]),start_ticks=int(fields[19]),boot_id=boot,command=(pp/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'),comm=comm,exe=exe))
 except (FileNotFoundError,ProcessLookupError):pass
mem={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines()};memory=dict(available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree'])
selfstat=Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()
host=dict(time=time.time(),boot_id=boot,groups=sorted(groups),matches=matches,processes_examined=processes,unreadable_exe_pids=unreadable,memory=memory,head=git('rev-parse','HEAD'),master=git('rev-parse','master'),reviewer=dict(pid=os.getpid(),pgid=int(selfstat[2]),sid=int(selfstat[3]),start_ticks=int(selfstat[19]),command=Path('/proc/self/cmdline').read_bytes().replace(b'\0',b' ').decode()),scope='All readable stat/comm/exe, both groups AND sessions; inaccessible system exe links retain visibility limitation')
write(E/'result-host.json',host)
ck(not matches and boot==s['boot_id'],'fresh no Julia all prior new groups sessions')
ck(memory['available_kib']>=6*1024**2 and memory['swap_used_kib']<=1024**2,'fresh memory')
for rec in [D/'closure.json',D/'publication.json']:
 for live,beforepath in [(R/'diagnostics/simplex-core-architecture/STATUS.md',E/'STATUS.md.before-master-validation'),(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md',E/'roadmap.md.before-master-validation')]:
  ck(sha(live)==sha(beforepath)==rd(rec)['sha256'][str(live.relative_to(R))],'four continuation bindings '+str(rec)+str(live))
summary=dict(all_passed=True,check_count=len(checks),checks=checks,phase='master300',master=MASTER,diagnostic_head=HEAD,seal_entries=len(s['inventory']),launch_entries=len(lp['inventory']),admission_entries=len(adm['sha256']),tracked_files=len(tree['sha256']),assertions=6956,resource_samples=len(samples),attempt_files=sorted(str(q.relative_to(A)) for q in A.rglob('*') if q.is_file()),execution_scope='Only new Python/Git/proc verification; no Julia or historical checker execution')
write(E/'result-checks.json',summary)
print('Independent result checks PASS',len(checks),'seal',len(s['inventory']),'launch',len(lp['inventory']),'tracked',len(tree['sha256']))
