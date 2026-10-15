"""New stage controls. Definitions only; no launch or reservation on import."""
from common import *
import os,sys
D=Q
WRAPPER='/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh'
OLD=D.parent/'NATIVE-PIVOT-QUALIFICATION'
GREEN=D.parent/'NATIVE-PIVOT-GREEN2-PREPARATION'/'runs/green2'
RESULT=D.parent/'NATIVE-PIVOT-GREEN2'
def config(phase):
 require(phase=='cost','Only new cost route is prepared')
 stage=R/'.superpowers/native-pivot-cost/cost';run=D/'runs/cost';out=run/'output'
 command=['/bin/bash',WRAPPER,'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--project='+str(stage),str(D/'cost-driver.jl'),str(out),str(stage),str(D/'inputs.toml')]
 return dict(phase=phase,seconds=45,expected_exit=0,arm='candidate',stage=str(stage),run=str(run),output=str(out),command=command)
def validate_environment():
 expected=rd(D/'environment.json');require({k:os.environ.get(k) for k in expected}==expected,'Loading environment changed')
def verify_review(review,pins,required,scope,phase=None):
 require(review.get('accepted') is True and review.get('findings')==[] and review.get('scope')==scope,'Review not accepted in scope')
 if phase is not None:require(review.get('phase')==phase,'Wrong review phase')
 require(review.get('pins_sha256')==sha(pins),'Review manifest binding')
 require(set(review.get('sha256',{}))==set(required),'Exact review membership')
 require(bindings(review),'Review hashes changed')
def validate_prerequisites(green2,failed):
 require(green2.get('all_passed') is True and green2.get('phase')=='green2','Accepted GREEN-2 required')
 require(failed.get('all_passed') is False and failed.get('phase')=='green','Original failed GREEN must remain failed')
def predecessor(phase):
 config(phase)
 ap=GREEN/'audit.json';a=rd(ap);oldp=OLD/'runs/green/audit.json';old=rd(oldp)
 validate_prerequisites(a,old)
 rp=GREEN/'result-review.json';review=rd(rp)
 verify_review(review,ap,list(a['sha256'])+[str(ap)],'stage result','green2')
 require(bindings(a) and bindings(old),'Predecessor audit bindings')
 require(all(sha(path(n))==v for n,v in review['evidence_sha256'].items()),'GREEN-2 supplemental review bindings')
 post=rd(RESULT/'closure-host.json');require(not post['matches'] and len(post['groups'])==214,'GREEN-2 process closure')
 files={ap,rp,oldp,RESULT/'closure-host.json',RESULT/'continuation-mappings.json'}
 files|={path(n) for z in [a,old] for n in z['sha256']}
 files|={path(n) for n in review['evidence_sha256']}
 # Only the two current continuation digests move to exact before-cost copies.
 preserved={str(STATUS):D/'STATUS.md.before-cost',str(ROAD):D/'roadmap.md.before-cost'}
 for rec in [RESULT/'closure.json',RESULT/'publication.json']:
  z=rd(rec);require(z['all_passed'] is True,'GREEN-2 result publication')
  files.add(rec)
  for n,v in z['sha256'].items():
   p=path(n);p=preserved.get(str(p),p)
   require(sha(p)==v,'GREEN-2 closure/publication changed: '+n);files.add(p)
 return sorted(files),post['groups']
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
