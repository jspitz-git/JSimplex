"""New stage controls. Definitions only; no launch or reservation on import."""
from common import *
import os,sys
D=Q
WRAPPER='/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh'
OLD=D.parent/'NATIVE-PIVOT-QUALIFICATION'
FIX=D.parent/'NATIVE-PIVOT-OBSERVER-FIX'
def config(phase):
 require(phase=='green2','Only new GREEN-2 is prepared')
 stage=R/'.superpowers/native-pivot-green2/green2'
 run=D/'runs/green2';out=run/'output'
 command=['/bin/bash',WRAPPER,'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--project='+str(stage),str(D/'test-driver.jl'),str(out),phase,str(stage)]
 return dict(phase=phase,seconds=60,expected_exit=0,arm='candidate',stage=str(stage),run=str(run),output=str(out),command=command)
def validate_environment():
 expected=rd(D/'environment.json');require({k:os.environ.get(k) for k in expected}==expected,'Loading environment changed')
def verify_review(review,pins,required,scope,phase=None):
 require(review.get('accepted') is True and review.get('findings')==[] and review.get('scope')==scope,'Review not accepted in scope')
 if phase is not None:require(review.get('phase')==phase,'Wrong review phase')
 require(review.get('pins_sha256')==sha(pins),'Review manifest binding')
 require(set(review.get('sha256',{}))==set(required),'Exact review membership')
 require(bindings(review),'Review hashes changed')
def validate_prerequisites(red,green):
 require(red.get('all_passed') is True and red.get('phase')=='red','Original RED not accepted')
 require(green.get('all_passed') is False and green.get('phase')=='green','Original failed GREEN must remain failed')
def predecessor(phase):
 config(phase)
 red=OLD/'runs/red';green=OLD/'runs/green'
 a=rd(red/'audit.json');g=rd(green/'audit.json');validate_prerequisites(a,g)
 verify_review(rd(red/'result-review.json'),red/'audit.json',list(a['sha256'])+[str(red/'audit.json')],'stage result','red')
 gr=rd(green/'result-review.json')
 require(gr['accepted'] is False and gr['diagnostic_accepted'] is True and gr['qualification_accepted'] is False,'Failed GREEN diagnostic review')
 require(set(gr['sha256'])==set(g['sha256'])|{str(green/'audit.json')} and gr['pins_sha256']==sha(green/'audit.json'),'Failed GREEN exact bindings')
 require(bindings(a) and bindings(g) and bindings(gr),'Original evidence changed')
 fp=FIX/'pins-reviewed.json';f=rd(fp)
 verify_review(rd(FIX/'review-final.json'),fp,list(f['sha256'])+[str(fp)],'offline observer correction')
 require(bindings(f),'Observer preparation changed')
 groups=rd(green/'posthost.json')['groups']
 require(not rd(green/'posthost.json')['matches'],'Original closure')
 files={red/'audit.json',red/'result-review.json',green/'audit.json',green/'result-review.json',green/'posthost.json',fp,FIX/'review-final.json'}
 files|={path(n) for z in [a,g,gr,f] for n in z['sha256']}
 return sorted(files),groups
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
