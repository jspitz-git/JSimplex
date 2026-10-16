"""New stage controls. Definitions only; no launch or reservation on import."""
from common import *
import os,sys
D=Q
WRAPPER='/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh'
DRIVER=D.parent/'NATIVE-PIVOT-INTEGRATION-DRIVER-PREPARATION'
PREPARATION=DRIVER
def config(phase):
 require(phase=='integration','Only new integration stage is prepared')
 stage=R/'.superpowers/native-pivot-integration-180/integration';run=D/'runs/integration';out=run/'output'
 command=['/bin/bash',WRAPPER,'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--project='+str(stage),str(DRIVER/'driver.jl'),str(out),phase,str(stage)]
 return dict(phase=phase,seconds=180,expected_exit=0,arm='candidate',stage=str(stage),run=str(run),output=str(out),command=command)
def validate_environment():
 expected=rd(D/'environment.json');require({k:os.environ.get(k) for k in expected}==expected,'Loading environment changed')
def verify_review(review,pins,required,scope,phase=None):
 require(review.get('accepted') is True and review.get('findings')==[] and review.get('scope')==scope,'Review not accepted in scope')
 if phase is not None:require(review.get('phase')==phase,'Wrong review phase')
 require(review.get('pins_sha256')==sha(pins),'Review manifest binding')
 require(set(review.get('sha256',{}))==set(required),'Exact review membership')
 require(bindings(review),'Review hashes changed')
def predecessor(phase):
 config(phase);P=DRIVER;mp=P/'preparation-pins.json';m=rd(mp);rp=P/'review-final.json';v=rd(rp)
 verify_review(v,mp,list(m['sha256'])+[str(mp)],'offline preparation')
 require(bindings(m),'Driver preparation input drift')
 require(all(sha(path(n))==h for n,h in v['evidence_sha256'].items()),'Supplemental driver review drift')
 files={mp,rp}|{path(n) for n in m['sha256']}|{path(n) for n in v['evidence_sha256']}
 preserved={str(STATUS):D.parent/'NATIVE-PIVOT-INTEGRATION-ENVIRONMENT-AMENDMENT/STATUS.md.before-environment',str(ROAD):D.parent/'NATIVE-PIVOT-INTEGRATION-ENVIRONMENT-AMENDMENT/roadmap.md.before-environment'}
 for rec in [P/'closure.json',P/'publication.json']:
  z=rd(rec);require(z['all_passed'] is True,'Driver publication not PASS');files.add(rec)
  for n,h in z['sha256'].items():
   p=path(n);p=preserved.get(str(p),p);require(sha(p)==h,'Driver closure drift '+n);files.add(p)
 h=rd(P/'closure-host.json');require(not h['matches'] and len(h['groups'])==216,'Previous driver closure')
 files.add(P/'closure-host.json')
 K=D.parent/'NATIVE-PIVOT-INTEGRATION-QUALIFICATION';oldrun=D.parent/'NATIVE-PIVOT-INTEGRATION-ENVIRONMENT-AMENDMENT/runs/integration'
 v=rd(K/'result-review.json');a=rd(oldrun/'audit.json')
 require(v['accepted'] is True and v['qualification_accepted'] is False and v['scope']=='diagnostic result' and v['findings']==[],'Previous failed result review')
 require(set(v['sha256'])==set(a['sha256'])|{str(oldrun/'audit.json')} and bindings(v) and bindings(a),'Previous result binding')
 require(all(sha(path(k))==x for k,x in v['evidence_sha256'].items()),'Previous supplemental result')
 files.update([K/'result-review.json',oldrun/'audit.json'])
 files.update(path(k) for k in v['sha256']);files.update(path(k) for k in v['evidence_sha256'])
 preserved={str(STATUS):D/'STATUS.md.before-180',str(ROAD):D/'roadmap.md.before-180'}
 for rec in [K/'closure.json',K/'publication.json']:
  z=rd(rec);require(z['all_passed'] is True,'Previous diagnostic publication');files.add(rec)
  for k,x in z['sha256'].items():
   p=path(k);p=preserved.get(str(p),p);require(sha(p)==x,'Previous closure binding '+k);files.add(p)
 h=rd(K/'closure-host.json');require(not h['matches'] and len(h['groups'])==218,'Previous closure groups');files.add(K/'closure-host.json')
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
