"""New stage controls. Definitions only; no launch or reservation on import."""
from common import *
import os,sys
D=Q
WRAPPER='/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh'
PHASES={'red':(30,1,'reference'),'green':(60,0,'candidate'),'cost':(45,0,'candidate')}
def config(phase):
 require(phase in PHASES,'Unknown phase')
 seconds,expected,arm=PHASES[phase]
 stage=R/'.superpowers/native-pivot-qualification'/phase
 run=D/'runs'/phase;out=run/'output'
 args=[str(D/'cost-driver.jl'),str(out),str(stage),str(D/'inputs.toml')] if phase=='cost' else [str(D/'test-driver-reviewed.jl'),str(out),phase,str(stage)]
 command=['/bin/bash',WRAPPER,'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--project='+str(stage),*args]
 return dict(phase=phase,seconds=seconds,expected_exit=expected,arm=arm,stage=str(stage),run=str(run),output=str(out),command=command)
def validate_environment():
 expected=rd(D/'environment.json');require({k:os.environ.get(k) for k in expected}==expected,'Loading environment changed')
def verify_review(review,pins,required,scope,phase=None):
 require(review.get('accepted') is True and review.get('findings')==[] and review.get('scope')==scope,'Review not accepted in scope')
 if phase is not None:require(review.get('phase')==phase,'Wrong review phase')
 require(review.get('pins_sha256')==sha(pins),'Review manifest binding')
 require(set(review.get('sha256',{}))==set(required),'Exact review membership')
 require(bindings(review),'Review hashes changed')
def predecessor(phase):
 if phase=='red':return [],[]
 previous='red' if phase=='green' else 'green';p=D/'runs'/previous
 a=p/'audit.json';review=p/'result-review.json'
 z=rd(a);require(z.get('all_passed') is True and z.get('phase')==previous,'Predecessor rejected')
 verify_review(rd(review),a,list(z['sha256'])+[str(a)],'stage result',previous)
 require(bindings(z),'Predecessor evidence changed')
 post=rd(p/'posthost.json');require(not post['matches'],'Predecessor process closure')
 return [a,review]+[Path(n) for n in z['sha256']],post['groups']
def full_host(extra=()):
 h=host();missing=set(extra)-set(h['groups'])
 for p in Path('/proc').glob('[0-9]*'):
  try:
   z=(p/'stat').read_text().rsplit(')',1)[1].split()
   if int(z[2]) in missing or int(z[3]) in missing:
    h['matches'].append(dict(pid=int(p.name),pgid=int(z[2]),sid=int(z[3]),start_ticks=int(z[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'),boot_id=h['boot_id']))
  except (FileNotFoundError,ProcessLookupError):pass
 h['groups']=sorted(set(h['groups'])|set(extra));return h
def validate_stage(cfg):
 target=Path(cfg['stage']);manifest=rd(PREV/'overlay-manifest.json')[cfg['arm']]
 require(target.is_dir() and not target.is_symlink(),'Stage absent/symlink')
 require({str(p.relative_to(target)) for p in target.rglob('*') if p.is_file()}=={e['destination'] for e in manifest},'Stage exact membership')
 for e in manifest:
  p=target/e['destination'];require(not p.is_symlink() and sha(p)==e['sha256']==sha(e['source']),'Stage byte identity')
 return [target/e['destination'] for e in manifest]
def guard_command(cfg,pins,started):
 seconds=cfg['seconds']-8
 return [sys.executable,'-B',str(D/'guard.py'),'run',str(pins),cfg['output'],'--seconds',str(seconds),'--deadline',str(started+seconds),'--expected-exit',str(cfg['expected_exit']),'--',*cfg['command']]
