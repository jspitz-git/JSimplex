"""Definitions only. No seal/reservation/Julia execution on import."""
from pathlib import Path
import json,hashlib,subprocess,os,sys,time
import guard
D=Path(__file__).resolve().parent;R=D.parents[3];C=R/'diagnostics/direct-bg-export-specialized/reproduce'
MASTER='26e2291745999f485a74f643298ca997d65c7205';ENTRY='7fd611127d3e3366c25ddb531768c3610548f303'
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
G=D.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-GC-DRIVER')
import importlib.util
_spec=importlib.util.spec_from_file_location('accepted_gc_control',G/'control.py');gcbase=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(gcbase)
def config(phase):
 require(phase in ('cost1-300','cost2-300','cost1-600','cost2-600'),'Unprepared phase')
 stage=rd(D/'stages.json')['cost']['path'];run=D/'runs'/phase;out=run/'output'
 command=['/bin/bash',WRAPPER,'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--history-file=no','--project='+stage,str(D/'cost.jl'),phase,str(out),stage]
 return dict(phase=phase,mode='cost',process=int(phase[4]),seconds=300 if phase.endswith('300') else 600,expected_exit=0,stage=stage,run=str(run),output=str(out),command=command)
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
 groups=sorted(set(rd(D/'host-entry.json')['groups'])|set(extra));matches=[];unreadable=[];unreadable_identity=[]
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
 prior=gcbase.preparation();m=D/'preparation-pins-final.json';j=rd(m)
 require(bindings(j) and set(j['sha256'])==set(rd(D/'required-paths-final.json')['paths']),'Preparation drift/membership')
 v=rd(D/'review-final.json');verify_review(v,m,list(j['sha256'])+[str(m)],'BG specialized export cost preparation')
 require(v.get('launch_admitted') is False,'Preparation is not launch admission')
 return sorted(set(prior)|set(j['sha256'])|{str(m),str(D/'review-final.json')}|set(v.get('evidence_sha256',{})))
def result_review(phase,scope,filename):
 run=D/'runs'/phase;v=rd(run/filename);files=sorted(str(p) for p in run.rglob('*') if p.is_file() and p!=run/filename)
 require(v.get('accepted') is True and v.get('findings')==[] and v.get('scope')==scope and v.get('phase')==phase,'Result review absent/wrong')
 require(set(v.get('sha256',{}))==set(files) and bindings(v),'Result review membership/bindings')
 if 'evidence_sha256' in v:require(bindings(v,'evidence_sha256'),'Result evidence bindings')
 return files+[str(run/filename)],rd(run/'posthost.json')['groups']
def predecessor(phase):
 cfg=config(phase);green='greengc300';run=G/'runs'/green
 files,groups=gcbase.result_review(green,'BG specialization GC GREEN result','result-review.json')
 v=rd(run/'result-review.json');require(bindings(v,'evidence_sha256'),'GREEN review evidence')
 closure=rd(run/'outer-closure.json');gcbase.validate_result_closure(green,closure)
 require(rd(run/'audit.json')['all_passed'] is True and guard.pins_match(rd(run/'sealed.json')),'GREEN not accepted/intact')
 outcome=rd(gcbase.outer_dir(green)/'outer-outcome.json')
 require(outcome['identity']==closure['outer_identity'] and outcome['launched'] is True and outcome['returncode']==0 and outcome['error']=='','GREEN outer outcome')
 files+=list(closure['sha256'])+list(v['evidence_sha256']);groups+=closure['host']['groups']
 if cfg['process']==2:
  from analysis import first_process_viable
  choices=[p for p in ('cost1-300','cost1-600') if (D/'runs'/p/'result-review.json').is_file()]
  require(len(choices)==1,'Exactly one first process')
  f,g=result_review(choices[0],'BG specialized export cost result','result-review.json');a=rd(D/'runs'/choices[0]/'audit.json');cl=rd(D/'runs'/choices[0]/'outer-closure.json');validate_result_closure(choices[0],cl)
  require(first_process_viable(a,rd(D/'inputs.json')['fixtures']),'Stop fixed design: first process performance gates')
  require(guard.pins_match(rd(D/'runs'/choices[0]/'sealed.json')),'First process source drift')
  files+=f+list(cl['sha256']);groups+=g+cl['host']['groups']
 if phase.endswith('600'):
  prev=phase[:-3]+'300';f,g=result_review(prev,'pure timeout result','timeout-review.json');a=rd(D/'runs'/prev/'audit.json');old=config(prev);seal=rd(D/'runs'/prev/'sealed.json');cl=rd(D/'runs'/prev/'outer-closure.json');validate_result_closure(prev,cl)
  require(a['all_passed'] is False and a['pure_timeout'] is True and seal['config']==old and old['command'][:-3]==cfg['command'][:-3] and old['command'][-1]==cfg['command'][-1] and guard.pins_match(seal),'Not unchanged pure timeout')
  files+=f+list(cl['sha256']);groups+=g+cl['host']['groups']
 return sorted(set(files)),sorted(set(groups))
def outer_dir(phase):
 config(phase)
 return D/'outers'/phase
def verify_outer(phase,sealed=None,live=False):
 o=outer_dir(phase);r=rd(o/'outer-ready.json');i=r['identity']
 require(r['phase']==phase and r['waiting_only'] is True and r['script_sha256']==sha(D/'outer.py') and r['expected_launcher']==str(D/'launch.py'),'Outer ready')
 require(i['pid']==i['pgid']==i['sid'] and i['start_ticks']>0 and i['command'],'Outer identity')
 if sealed is not None:require(sealed['outer_identity']==i,'Sealed outer identity')
 if live:require(guard.process_identity(i['pid'])==i,'Outer no longer alive')
 return i
def verify_outer_invocation(phase,sealed,live=False):
 i=verify_outer(phase,sealed,live);o=outer_dir(phase);run=Path(config(phase)['run']);sp=run/'sealed.json';rp=run/'admission.json'
 require(rd(o/'release.json').get('one_attempt') is True,'Strict release boolean')
 require(rd(o/'release.json')==dict(phase=phase,sealed_sha256=sha(sp),admission_sha256=sha(rp),outer_ready_sha256=sha(o/'outer-ready.json'),one_attempt=True),'Release binding')
 require(rd(o/'outer-invocation.json')==dict(identity=i,phase=phase,seal_sha256=sha(sp),review_sha256=sha(rp),release_sha256=sha(o/'release.json'),launcher_sha256=sha(D/'launch.py'),method='runpy.run_path launch.py as __main__ in this outer process'),'Outer invocation')
 if live:require(os.getpid()==i['pid'],'Launcher must run inside admitted outer')
 return i
def guard_command(cfg,pins,started):
 seconds=cfg['seconds']-8
 return [sys.executable,'-B',str(D/'guard.py'),'run',str(pins),cfg['output'],'--seconds',str(seconds),'--deadline',str(started+seconds),'--expected-exit',str(cfg['expected_exit']),'--',*cfg['command']]
def loaded_for(cfg):return dict(rd(D/'loaded-paths.json'),JSimplex=str(Path(cfg['stage'])/'src/JSimplex.jl'))

def seal_files(cfg,prepared,extra):
 run=Path(cfg['run'])
 return sorted(set(prepared+list(rd(D/'runtime-inputs-complete.json')['inventory'])+[str(root/n) for label,root in [('diagnostic',R),('production',W)] for n in rd(D/'baseline.json')[label]]+[str(Path(cfg['stage'])/n) for n in rd(D/'stages.json')[cfg['mode']]['sha256']]+extra+[str(run/'host.json'),str(run/'config.json'),str(outer_dir(cfg['phase'])/'outer-ready.json')]))
def verify_seal(cfg,sealed):
 prepared=preparation();extra,_=predecessor(cfg['phase'])
 require(sealed['files']==seal_files(cfg,prepared,extra),'Exact seal membership')
 require(sealed['trees']==[cfg['stage'],str(C)] and sealed['inputs']==[],'Exact sealed trees')
 require(sealed['inventory']==guard.inventory(sealed['files'],sealed['trees']),'Exact sealed inventory')

def closure_paths(phase):
 o=outer_dir(phase);run=Path(config(phase)['run'])
 return [o/n for n in ['outer-ready.json','release.json','outer-invocation.json','outer-outcome.json']]+[run/n for n in ['sealed.json','admission.json','posthost.json','audit.json']]
def validate_result_closure(phase,closure):
 run=Path(config(phase)['run']);s=rd(run/'sealed.json');post=rd(run/'posthost.json')
 outer=verify_outer_invocation(phase,s)
 require(closure.get('all_passed') is True and set(closure.get('sha256',{}))=={str(p) for p in closure_paths(phase)} and bindings(closure),'Exact external closure membership/bindings')
 require(closure['outer_identity']==outer==s['outer_identity'],'External closure identity')
 h=closure['host'];required=set(s['groups'])|set(post['groups'])|{outer['pgid'],outer['sid']}
 require(host_safe(h) and required<=set(h['groups']),'External closure group/session coverage')
 require(all(h[k]==s[k]==post[k] for k in ['head','master','boot_id']) and outer['boot_id']==s['boot_id'],'External closure refs/boot')
 require(h['head']+'\trefs/heads/codex/simplex-core-architecture' in h['remote'] and MASTER+'\trefs/heads/master' in h['remote'],'External closure remote refs')
 return True
