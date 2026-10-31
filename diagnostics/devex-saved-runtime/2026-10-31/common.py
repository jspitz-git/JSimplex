from pathlib import Path
import json,hashlib,os,sys,subprocess,time
D=Path(__file__).resolve().parent;M=Path('/home/jspitz/JSimplex.jl');W=D.parents[2];R=D/'run-1'
def require(v,m):
 if not v:raise ValueError(m)
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def fresh(p,v):
 with open(p,'x') as f:json.dump(v,f,indent=2);f.write('\n')
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],text=True).strip()
def identity(pid):
 p=Path('/proc')/str(pid);s=(p/'stat').read_text();f=s[s.rfind(')')+2:].split()
 return dict(pid=int(pid),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'))
def host(defer_self=False):
 base=read(D/'baseline-host.json');boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();groups=set(base['checked_groups']) if boot==base['boot_id'] else set();deferred=[]
 for path in (R/'attempt.json',R/'guard/process.json',R/'guard/current.json'):
  if not path.exists():continue
  v=read(path)
  for key in ('runner','child'):
   a=v.get(key,{})
   if a.get('boot_id')==boot:
    if defer_self and a==identity(os.getpid()):deferred.append(a)
    else:groups.update((a['pgid'],a['sid']))
 conflicts=[]
 for p in Path('/proc').glob('[0-9]*'):
  try:
   a=identity(p.name)
   if (p/'comm').read_text().strip().lower().startswith('julia') or a['pgid'] in groups or a['sid'] in groups:conflicts.append(a)
  except (FileNotFoundError,ProcessLookupError):pass
 require(not conflicts,'active Julia/group/session '+str(conflicts))
 mem={s.split(':')[0]:int(s.split()[1]) for s in Path('/proc/meminfo').read_text().splitlines()};memory=dict(available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree']);require(memory['available_kib']>=6*1024**2 and memory['swap_used_kib']<=1024**2,'memory pressure')
 c=read(D/'contract.json');refs=dict(master=git(M,'rev-parse','HEAD'),origin_master=git(W,'rev-parse','origin/master'),diagnostic=git(W,'rev-parse','HEAD'))
 require(refs==dict(master=c['master'],origin_master=c['master'],diagnostic=c['diagnostic']),'refs changed')
 require(git(M,'branch','--show-current')=='master' and not git(M,'diff','--cached','--name-only') and not git(M,'diff','--name-only','--','src','test','Project.toml','.github'),'master source/index changed')
 require(git(M,'status','--porcelain','-uall')==base['master_status'],'user status changed');require(all(sha(p)==h for p,h in base['user_hashes'].items()),'user file changed')
 return dict(at=time.time(),boot_id=boot,checked_groups=sorted(groups),conflicts=conflicts,deferred_active_launcher=deferred,memory=memory,refs=refs)
def pins_ok():
 p=read(D/'pins.json');require(set(p['files'])==set(p['inventory']) and p['trees']==[],'pin membership')
 for name,v in p['inventory'].items():require(sha(name)==v['sha256'] and str(Path(name).resolve(strict=True))==v['resolved'],'pin changed '+name)
 return True
