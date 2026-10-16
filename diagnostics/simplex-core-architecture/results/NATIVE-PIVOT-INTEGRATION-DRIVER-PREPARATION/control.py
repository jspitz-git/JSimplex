"""New stage controls. Definitions only; no launch or reservation on import."""
from common import *
import os,sys
D=Q
WRAPPER='/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh'
PREPARATION=D.parent/'NATIVE-PIVOT-INTEGRATION-PREPARATION'
def config(phase):
 require(phase=='integration','Only new integration stage is prepared')
 stage=R/'.superpowers/native-pivot-integration/integration';run=D/'runs/integration';out=run/'output'
 command=['/bin/bash',WRAPPER,'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--project='+str(stage),str(D/'driver.jl'),str(out),phase,str(stage)]
 return dict(phase=phase,seconds=60,expected_exit=0,arm='candidate',stage=str(stage),run=str(run),output=str(out),command=command)
def validate_environment():
 expected=rd(D/'environment.json');require({k:os.environ.get(k) for k in expected}==expected,'Loading environment changed')
def verify_review(review,pins,required,scope,phase=None):
 require(review.get('accepted') is True and review.get('findings')==[] and review.get('scope')==scope,'Review not accepted in scope')
 if phase is not None:require(review.get('phase')==phase,'Wrong review phase')
 require(review.get('pins_sha256')==sha(pins),'Review manifest binding')
 require(set(review.get('sha256',{}))==set(required),'Exact review membership')
 require(bindings(review),'Review hashes changed')
def predecessor(phase):
 config(phase);P=PREPARATION;mp=P/'preparation-pins-reviewed.json';m=rd(mp);rp=P/'review-final.json';v=rd(rp)
 verify_review(v,mp,list(m['sha256'])+[str(mp.relative_to(R))],'offline integration preparation')
 require(bindings(m),'Preparation input drift')
 require(all(sha(path(n))==h for n,h in v['evidence_sha256'].items()),'Supplemental review drift')
 files={mp,rp}|{path(n) for n in m['sha256']}|{path(n) for n in v['evidence_sha256']}
 preserved={str(STATUS):D/'STATUS.md.before-driver',str(ROAD):D/'roadmap.md.before-driver'}
 for rec in [P/'closure.json',P/'publication.json']:
  z=rd(rec);require(z['all_passed'] is True,'Preparation publication not PASS');files.add(rec)
  for n,h in z['sha256'].items():
   p=path(n);p=preserved.get(str(p),p);require(sha(p)==h,'Preparation closure drift '+n);files.add(p)
 h=rd(P/'closure-host.json');require(not h['matches'] and len(h['groups'])==216,'Previous host closure')
 files.add(P/'closure-host.json')
 return sorted(files),h['groups']
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
