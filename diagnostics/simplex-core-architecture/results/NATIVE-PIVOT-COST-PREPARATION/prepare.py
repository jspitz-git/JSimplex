"""One-shot offline cost routing preparation; no stage, seal or Julia."""
from pathlib import Path
import json,os,hashlib
D=Path(__file__).resolve().parent;R=D.parents[3];Q=D.parent/'NATIVE-PIVOT-QUALIFICATION';G=D.parent/'NATIVE-PIVOT-GREEN2-PREPARATION'
def put(n,s):
 with (D/n).open('x') as f:f.write(s)
def save(n,z):put(n,json.dumps(z,indent=2)+'\n')
identical=['cost-driver.jl','inputs.json','inputs.toml','saved-C.json','guard.py','supervisor.py','exact.py','oracle.py','budget.json','loaded-paths.json']
for n in identical:
 with (D/n).open('xb') as f:f.write((Q/n).read_bytes())
edits={}
def changed(n,src,replacements):
 s=src.read_text()
 for a,b in replacements:
  if s.count(a)!=1:raise RuntimeError((n,a[:80],s.count(a)))
  s=s.replace(a,b,1)
 put(n,s);edits[n]={'source':str(src),'edits':[{'before':a,'after':b} for a,b in replacements]}
changed('common.py',G/'common.py',[("HEAD='30b0b3402ef5d319c8faa0a78aca32ca3c354d22'","HEAD='294d4435e888577d90533b50c3c44da6702976e6'")])
s=(G/'control.py').read_text();a=s.index("OLD=D.parent/");b=s.index('def validate_environment():')
config='''OLD=D.parent/'NATIVE-PIVOT-QUALIFICATION'
GREEN=D.parent/'NATIVE-PIVOT-GREEN2-PREPARATION'/'runs/green2'
RESULT=D.parent/'NATIVE-PIVOT-GREEN2'
def config(phase):
 require(phase=='cost','Only new cost route is prepared')
 stage=R/'.superpowers/native-pivot-cost/cost';run=D/'runs/cost';out=run/'output'
 command=['/bin/bash',WRAPPER,'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--project='+str(stage),str(D/'cost-driver.jl'),str(out),str(stage),str(D/'inputs.toml')]
 return dict(phase=phase,seconds=45,expected_exit=0,arm='candidate',stage=str(stage),run=str(run),output=str(out),command=command)
'''
a2=s.index('def validate_prerequisites(');b2=s.index('def full_host(',a2)
pre='''def validate_prerequisites(green2,failed):
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
'''
changed('control.py',G/'control.py',[(s[a:b],config),(s[a2:b2],pre)])
for n in ['seal.py','launch.py']:
 with (D/n).open('xb') as f:f.write((G/n).read_bytes())
changed('audit.py',Q/'audit_reviewed.py',[('from control_reviewed import *','from control import *')])
save('environment.json',{k:os.environ.get(k) for k in json.loads((Q/'environment.json').read_text())})
save('source-map.json',dict(byte_identical={n:str(Q/n) for n in identical}|{n:str(G/n) for n in ['seal.py','launch.py']},changed=edits))
print('Prepared new route; numerical driver/inputs/oracle/guard unchanged; no stage or launch')
