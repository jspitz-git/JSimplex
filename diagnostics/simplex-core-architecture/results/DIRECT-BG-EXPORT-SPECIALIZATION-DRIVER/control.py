"""Definitions only. No seal/reservation/Julia execution on import."""
from pathlib import Path
import json,hashlib,subprocess,os,sys,time
import guard
D=Path(__file__).resolve().parent;R=D.parents[3];C=R/'diagnostics/direct-bg-export-specialized/reproduce'
MASTER='26e2291745999f485a74f643298ca997d65c7205';ENTRY='b504ea4fbf3bc40a9fa87cfc0b9a7dd69cc821cd'
WRAPPER='/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh'
W=Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl')
def require(v,m):
 if not v:raise RuntimeError(m)
def rd(p):return json.loads(Path(p).read_text())
def sha(p):return guard.digest(p)
def save(p,j):
 with Path(p).open('x') as f:json.dump(j,f,indent=2);f.write('\n')
def git(*a,cwd=R):return subprocess.check_output(['git',*a],cwd=cwd,text=True).strip()
def path(n):return Path(n) if Path(n).is_absolute() else R/n
def bindings(j,key='sha256'):return all(sha(path(n))==h for n,h in j[key].items())
def config(phase):
 require(phase in ('red300','green300','red600','green600'),'Unprepared phase')
 mode='red' if phase.startswith('red') else 'green';stage=rd(D/'stages.json')[mode]['path'];run=D/'runs'/phase;out=run/'output'
 command=['/bin/bash',WRAPPER,'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--history-file=no','--project='+stage,str(D/'driver.jl'),str(out),stage,phase]
 return dict(phase=phase,mode=mode,seconds=300 if phase.endswith('300') else 600,expected_exit=1 if mode=='red' else 0,stage=stage,run=str(run),output=str(out),command=command)
def verify_review(v,pins,required,scope,phase=None):
 require(v.get('accepted') is True and v.get('findings')==[] and v.get('scope')==scope,'Wrong review acceptance')
 require(phase is None or v.get('phase')==phase,'Wrong review phase')
 require(v.get('pins_sha256')==sha(pins) and set(v.get('sha256',{}))==set(required) and bindings(v),'Exact review bindings')
 if 'evidence_sha256' in v:require(bindings(v,'evidence_sha256'),'Supplementary review drift')
def validate_environment():
 e=rd(D/'environment.json');require({k:os.environ.get(k) for k in e}==e,'Loading environment drift')
def validate_sources():
 require(git('rev-parse','master')==MASTER and git('rev-parse','HEAD',cwd=W)==MASTER,'Master drift')
 require(MASTER+'\trefs/heads/master' in git('ls-remote','origin','refs/heads/master'),'Remote master drift')
 require(subprocess.run(['git','merge-base','--is-ancestor',ENTRY,'HEAD'],cwd=R,stdout=subprocess.DEVNULL).returncode==0,'Unrelated diagnostic history')
 for label,root in [('diagnostic',R),('production',W)]:
  b=rd(D/'baseline.json')[label]
  require(set(git('ls-files','src','test','.github','Project.toml',cwd=root).splitlines())==set(b),'Source membership')
  require(all(sha(root/n)==h for n,h in b.items()),'Baseline drift '+label)
 for mode,stage in rd(D/'stages.json').items():
  root=Path(stage['path']);actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}
  require(not root.is_symlink() and not any(p.is_symlink() for p in root.rglob('*')),'Stage symlink')
  require(actual==set(stage['sha256']) and all(sha(root/n)==h for n,h in stage['sha256'].items()),'Stage drift '+mode)
 require(guard.inventory(list(rd(D/'runtime-inputs-complete.json')['inventory']),[])==rd(D/'runtime-inputs-complete.json')['inventory'],'Runtime drift')
def full_host(extra=()):
 groups=sorted(set(rd(D/'host.json')['groups'])|set(extra));matches=[];unreadable=[];unreadable_identity=[]
 for p in Path('/proc').glob('[0-9]*'):
  try:
   a=(p/'stat').read_text().rsplit(')',1)[1].split();comm=(p/'comm').read_text().strip()
   argv0=(p/'cmdline').read_bytes().split(b'\0',1)[0].decode(errors='replace');exe=''
   try:exe=str((p/'exe').resolve(strict=True))
   except PermissionError:unreadable.append(int(p.name))
   except FileNotFoundError:pass
   if int(a[2]) in groups or int(a[3]) in groups or any(Path(v).name.lower().startswith('julia') for v in (comm,argv0,exe)):
    matches.append(dict(guard.process_identity(int(p.name)),comm=comm,argv0=argv0,exe=exe))
  except (FileNotFoundError,ProcessLookupError):pass
  except PermissionError:unreadable_identity.append(int(p.name))
 return dict(time=time.time(),groups=groups,matches=matches,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),head=git('rev-parse','HEAD'),master=git('rev-parse','master'),unreadable_exe_pids=unreadable,unreadable_identity_pids=unreadable_identity,scope='All groups AND sessions/stat/comm/argv0/readable exe; inaccessible exe links remain an explicit visibility limit, not a universal executable-identity proof')
def host_safe(h):return h.get('matches')==[] and h.get('unreadable_identity_pids')==[]
def preparation():
 m=D/'preparation-pins.json';j=rd(m);require(bindings(j),'Preparation drift')
 require(set(j['sha256'])==set(rd(D/'required-paths.json')['paths']),'Preparation membership')
 v=D/'review.json';require(rd(v).get('red_expectation_supported') is True,'Three RED expectations not independently supported');verify_review(rd(v),m,list(j['sha256'])+[str(m)],'BG specialization driver preparation')
 return sorted(set(j['sha256'])|{str(m),str(v)})
def result_review(phase,scope,filename):
 run=D/'runs'/phase;v=rd(run/filename);files=sorted(str(p) for p in run.rglob('*') if p.is_file() and p!=run/filename)
 require(v.get('accepted') is True and v.get('findings')==[] and v.get('scope')==scope and v.get('phase')==phase,'Result review absent/wrong')
 require(set(v.get('sha256',{}))==set(files) and bindings(v),'Result review membership/bindings')
 return files+[str(run/filename)],rd(run/'posthost.json')['groups']
def predecessor(phase):
 cfg=config(phase);files=[];groups=[]
 if cfg['mode']=='green':
  choices=[p for p in ['red300','red600'] if (D/'runs'/p/'result-review.json').is_file()]
  require(len(choices)==1,'Exactly one accepted RED result required')
  red=choices[0];f,g=result_review(red,'BG specialization RED result','result-review.json');a=rd(D/'runs'/red/'audit.json')
  require(a.get('all_passed') is True and a.get('pure_timeout') is False and a.get('phase')==red,'RED not accepted')
  require(guard.pins_match(rd(D/'runs'/red/'sealed.json')),'RED input drift');files+=f;groups+=g
 if phase.endswith('600'):
  prev=cfg['mode']+'300';f,g=result_review(prev,'pure timeout result','timeout-review.json');a=rd(D/'runs'/prev/'audit.json')
  require(a.get('all_passed') is False and a.get('pure_timeout') is True,'Not pure timeout')
  s=rd(D/'runs'/prev/'sealed.json');first=config(prev)
  require(s['config']==first and first['command'][:-3]==cfg['command'][:-3] and first['stage']==cfg['stage'],'Retry source/options drift')
  require(guard.pins_match(s),'Prior attempt input drift');files+=f;groups+=g
 return sorted(set(files)),sorted(set(groups))
def guard_command(cfg,pins,started):
 seconds=cfg['seconds']-8
 return [sys.executable,'-B',str(D/'guard.py'),'run',str(pins),cfg['output'],'--seconds',str(seconds),'--deadline',str(started+seconds),'--expected-exit',str(cfg['expected_exit']),'--',*cfg['command']]
def loaded_for(cfg):return dict(rd(D/'loaded-paths.json'),JSimplex=str(Path(cfg['stage'])/'src/JSimplex.jl'))
