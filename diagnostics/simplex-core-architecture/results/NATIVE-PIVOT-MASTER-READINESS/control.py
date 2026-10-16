"""Definitions only. Future sealing/launching requires actual-master acceptance."""
from pathlib import Path
import json,hashlib,subprocess,os,sys,time
import guard
D=Path(__file__).resolve().parent;R=D.parents[3];P=D.parent/'NATIVE-PIVOT-PRODUCTION-INTEGRATION-PREPARATION'
BASE='6f68e24e8ddac42b948da8fcc2d636c010751194';ENTRY='4c2198feb82d273fa71056f9c3cedc678549a7e0'
WRAPPER='/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh'
def require(v,m):
 if not v:raise RuntimeError(m)
def rd(p):return json.loads(Path(p).read_text())
def sha(p):return guard.digest(p)
def save(p,j):
 with Path(p).open('x') as f:json.dump(j,f,indent=2);f.write('\n')
def git(*a,cwd=R):return subprocess.check_output(['git',*a],cwd=cwd,text=True).strip()
def path(n):return Path(n) if Path(n).is_absolute() else R/n
def bindings(j):return all(sha(path(n))==h for n,h in j['sha256'].items())
def config(phase):
 require(phase in ('master300','master600'),'Unprepared phase')
 c=rd(D/'production-commit.json');w=Path(c['worktree']);run=D/'runs'/phase;out=run/'output'
 command=['/bin/bash',WRAPPER,'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--history-file=no','--project='+str(w),str(D/'master-driver.jl'),str(out),str(w)]
 return dict(phase=phase,seconds=300 if phase=='master300' else 600,expected_exit=0,stage=str(w),run=str(run),output=str(out),command=command,production_commit=c['commit'])
def verify_review(v,pins,required,scope,phase=None):
 require(v.get('accepted') is True and v.get('findings')==[] and v.get('scope')==scope,'Wrong review acceptance')
 require(phase is None or v.get('phase')==phase,'Wrong phase')
 require(v.get('pins_sha256')==sha(pins) and set(v.get('sha256',{}))==set(required) and bindings(v),'Exact review bindings')
def validate_environment():
 e=rd(D/'environment.json');require({k:os.environ.get(k) for k in e}==e,'Loading environment drift')
def validate_production(actual_master=True):
 c=rd(D/'production-commit.json');w=Path(c['worktree']);tree=rd(D/'production-tree.json');require(git('rev-parse','HEAD',cwd=w)==c['commit']==tree['commit'],'Production HEAD')
 require(git('rev-parse','HEAD^',cwd=w)==BASE,'Production parent')
 require(git('diff-tree','--no-commit-id','--name-only','-r',c['commit'],cwd=w).splitlines()==c['names'],'Production diff names')
 require(git('ls-files',cwd=w).splitlines()==sorted(tree['sha256']),'Tracked membership')
 require(all(sha(w/n)==h for n,h in tree['sha256'].items()),'Production file drift')
 require(not git('diff','--name-only',cwd=w) and not git('diff','--cached','--name-only',cwd=w),'Production dirty')
 for p,v in rd(D/'environment-files.json').items():require(not Path(p).is_symlink() and sha(p)==v['sha256']==sha(v['source']),'Test environment file drift')
 require(set(git('ls-files','--others','--exclude-standard',cwd=w).splitlines())=={'Manifest.toml','LocalPreferences.toml'},'Unexpected untracked production files')
 require(git('rev-parse','master')==(c['commit'] if actual_master else BASE),'Actual master ref')
 require(BASE+'\trefs/heads/master' in git('ls-remote','origin','refs/heads/master'),'Remote master published/changed prematurely')
 require(subprocess.run(['git','merge-base','--is-ancestor',ENTRY,'HEAD'],cwd=R,stdout=subprocess.DEVNULL).returncode==0,'Unrelated diagnostics')
 return [w/n for n in tree['sha256']]+[Path(n) for n in rd(D/'environment-files.json')]
def full_host(extra=()):
 groups=sorted(set(rd(D/'host.json')['groups'])|set(extra));boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[];unreadable=[]
 for p in Path('/proc').glob('[0-9]*'):
  try:
   a=(p/'stat').read_text().rsplit(')',1)[1].split();comm=(p/'comm').read_text().strip();exe=''
   try:exe=str((p/'exe').resolve(strict=True))
   except PermissionError:unreadable.append(int(p.name))
   except FileNotFoundError:pass
   if int(a[2]) in groups or int(a[3]) in groups or comm.lower().startswith('julia') or Path(exe).name.lower().startswith('julia'):matches.append(dict(guard.process_identity(int(p.name)),comm=comm,exe=exe))
  except (FileNotFoundError,ProcessLookupError):pass
 return dict(time=time.time(),groups=groups,matches=matches,boot_id=boot,head=git('rev-parse','HEAD'),master=git('rev-parse','master'),unreadable_exe_pids=unreadable,scope='All stat/comm and readable exe; inaccessible system exe links remain a visibility limit')
def preparation():
 m=D/'preparation-pins.json';j=rd(m);require(bindings(j),'Readiness input drift')
 require(set(j['sha256'])==set(rd(D/'required-paths.json')['paths']),'Required membership')
 verify_review(rd(D/'review-final.json'),m,list(j['sha256'])+[str(m)],'production commit readiness')
 return sorted({str(path(n)) for n in j['sha256']}|{str(m),str(D/'review-final.json')})
def predecessor(phase):
 config(phase)
 if phase=='master300':return [],[]
 run=D/'runs/master300';sp=run/'sealed.json';a=run/'audit.json';v=rd(run/'timeout-review.json')
 require(v.get('accepted') is True and v.get('scope')=='pure timeout result' and v.get('findings')==[],'Retry lacks independent pure-timeout review')
 # Review binds exact complete prior attempt, excluding itself; files cannot be added silently.
 files=sorted(str(p) for p in run.rglob('*') if p.is_file() and p.name!='timeout-review.json')
 require(set(v.get('sha256',{}))==set(files) and bindings(v),'Prior timeout review membership/bindings')
 require(rd(a)['all_passed'] is False and rd(a).get('pure_timeout') is True,'Not pure timeout')
 previous=rd(sp);first=config('master300');second=config('master600')
 require(previous['config']==first,'Previous config changed')
 require(first['command'][:-2]==second['command'][:-2] and first['command'][-1]==second['command'][-1],'Retry code/options changed')
 require(guard.pins_match(previous),'Previous source/runtime drift')
 return files+[str(run/'timeout-review.json')],rd(run/'posthost.json')['groups']
def guard_command(cfg,pins,started):
 seconds=cfg['seconds']-8
 return [sys.executable,'-B',str(D/'guard.py'),'run',str(pins),cfg['output'],'--seconds',str(seconds),'--deadline',str(started+seconds),'--expected-exit','0','--',*cfg['command']]
