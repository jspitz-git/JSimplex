"""Create separate RED-only master-stage harness; never execute Julia/launch/seal."""
from pathlib import Path
import json,hashlib,ast
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');H=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-HARNESS';D=H.with_name('DIRECT-BG-BLOCKED-UPDATE-RED2-HARNESS');S=H.with_name('DIRECT-BG-BLOCKED-UPDATE-STAGE-REPAIR')
def save(n,x):
 with (D/n).open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def write(n,t):
 with (D/n).open('x') as f:f.write(t)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
# Tests precede new control implementation; only definitions/configuration inspected.
write('routing-tests.py','''"""Offline configuration and gate tests; no outer/seal/launcher or Julia."""
from pathlib import Path
import sys,json,copy
from unittest.mock import patch
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D));import control as c
checks={}
def ck(n,v):
 c.require(v,n);checks[n]=True
def reject(n,f):
 try:f()
 except (RuntimeError,KeyError,FileNotFoundError):checks[n]=True
 else:raise RuntimeError('Accepted '+n)
cfg=c.config('red300');m=c.rd(c.REPAIR/'stage.json')
ck('master_stage',cfg['stage']==m['stage'])
ck('new_private_run_root',Path(cfg['run'])==D/'runs/red300' and not Path(cfg['run']).exists())
ck('new_driver',cfg['command'][-4]==str(D/'driver.jl'))
ck('exact_300',cfg['seconds']==300 and cfg['expected_exit']==1 and cfg['mode']=='red')
ck('guard_292',c.guard_command(cfg,D/'pins',10)[c.guard_command(cfg,D/'pins',10).index('--seconds')+1]=='292')
ck('loaded_path',c.loaded_for(cfg)['JSimplex']==str(Path(m['stage'])/'src/JSimplex.jl'))
for phase in ['green300','red600','red','',None]:reject('phase_'+str(phase),lambda:c.config(phase))
ck('predecessor_empty',c.predecessor('red300')==([],[]));reject('no_green_predecessor',lambda:c.predecessor('green300'))
ck('all_old_groups',len(c.rd(D/'host-entry.json')['groups'])==271)
c.validate_stage_binding();checks['stage_binding']=True
real=c.rd
for label,mut in [('old_stage',lambda j:j['red'].update(path=str(c.OLD/'stages.json'))),('changed_hash',lambda j:j['red']['sha256'].update({'src/factorization.jl':'0'*64})),('extra_mode',lambda j:j.update(green=j['red']))]:
 bad=copy.deepcopy(real(D/'stages.json'));mut(bad)
 with patch.object(c,'rd',lambda p:bad if Path(p)==D/'stages.json' else real(p)):reject(label,c.validate_stage_binding)
# Pure receipt validator must reject wrong scope, nonboolean acceptance, omissions and hash drift.
import tempfile
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp)/'pins';p.write_text('fixed');v=dict(accepted=True,findings=[],scope='BG blocked U RED2 preparation',pins_sha256=c.sha(p),sha256={str(p):c.sha(p)})
 c.verify_review(v,p,[str(p)],v['scope']);checks['valid_review']=True
 for label,change in [('wrong_scope',dict(scope='BG blocked U driver preparation')),('nonboolean',dict(accepted=1)),('findings',dict(findings=['x'])),('missing_binding',dict(sha256={})),('bad_pin',dict(pins_sha256='0'*64))]:
  bad=dict(v,**change);reject(label,lambda:c.verify_review(bad,p,[str(p)],v['scope']))
ck('no_run_or_outer',not (D/'runs').exists() and not (D/'outers').exists())
c.save(D/'routing-tests.json',dict(all_passed=True,checks=checks,scope=__doc__))
print('Routing/gates PASS',len(checks))
''')
# Source regression predicates against old controls BEFORE replacing routing.
old=(H/'control.py').read_text();red={'master_stage_bound':"REPAIR/'stage.json'" in old,'red_only':"require(phase == 'red300'" in old,'repair_review_bound':'BG blocked U RED2 preparation' in old}
save('routing-source-red.json',dict(checks=red,expected_missing=3,scope='Three missing source routing guarantees; not numerical six-failure RED'))
if any(red.values()):raise RuntimeError('Unexpected source baseline')
copied={}
for n in ['driver.jl','recorder.jl','panel-tests.jl','lifecycle-tests.jl','numerical-tests.jl','oracle.py','guard.py','supervisor.py','schedule.json','assertion-sites.json','test-transform.json','loaded-paths.json','environment.json','baseline.json','runtime-inputs-complete.json','seal.py','post-return.py']:
 write(n,(H/n).read_text());copied[n]=dict(source=str(H/n),sha256=sha(H/n))
for n in ['launch.py','outer.py','audit.py']:
 text=(H/n).read_text();text=text.replace('BG blocked U exact-stage admission','BG blocked U RED2 exact-stage admission');write(n,text)
# Retain complete process protection and full auditor; change preparation, routing and predecessor only.
t=old.replace("ENTRY='1a824ea2d6478ba5ecbd3afc8ffbe83207bf2fd8'","ENTRY='ee7d652cd4939d2fbce32f10c56073fbc62b640c'")
t=t.replace("W=Path(","OLD=D.with_name('DIRECT-BG-BLOCKED-UPDATE-HARNESS');REPAIR=D.with_name('DIRECT-BG-BLOCKED-UPDATE-STAGE-REPAIR')\nW=Path(",1)
t=t.replace("require(phase in ('red300','green300'),'Unprepared phase')","require(phase == 'red300','Only separately prepared RED300 is allowed')")
start=t.index('def preparation():');end=t.index('def result_review(',start)
t=t[:start]+'''def validate_stage_binding():
 m=rd(REPAIR/'stage.json');stages=rd(D/'stages.json')
 require(m['master']==MASTER and stages=={'red':dict(path=m['stage'],sha256=m['stage_files'])},'Exact repaired stage routing')
 require(bindings(m),'Repair source/stage bindings')
 require(rd(REPAIR/'review.json').get('accepted') is True and rd(REPAIR/'review.json').get('findings')==[] and bindings(rd(REPAIR/'review.json')),'Repair independent review')
 require(bindings(rd(REPAIR/'publication.json')),'Repair publication drift')
def preparation():
 m=D/'preparation-pins.json';j=rd(m)
 require(bindings(j) and set(j['sha256'])==set(rd(D/'required-paths.json')['paths']),'Preparation drift/membership')
 verify_review(rd(D/'review.json'),m,list(j['sha256'])+[str(m)],'BG blocked U RED2 preparation')
 require(rd(D/'review.json').get('launch_admitted') is False,'Offline review is not admission')
 validate_stage_binding()
 for name,item in rd(D/'copied-files.json').items():require(sha(D/name)==sha(item['source'])==item['sha256'],'Frozen copied control drift')
 return sorted(set(j['sha256'])|{str(m),str(D/'review.json')}|set(rd(D/'review.json').get('evidence_sha256',{})))
''' +t[end:]
start=t.index('def predecessor(');end=t.index('def outer_dir(',start)
t=t[:start]+'''def predecessor(phase):
 config(phase)
 # Failed original RED is historical evidence, never a qualification prerequisite.
 return [],[]
''' +t[end:]
t=t.replace('def validate_sources():\n','def validate_sources():\n validate_stage_binding()\n',1)
write('control.py',t)
m=json.loads((S/'stage.json').read_text());save('stages.json',{'red':dict(path=m['stage'],sha256=m['stage_files'])});save('copied-files.json',copied)
# New synthetic checks use frozen pure data generators, never execute old checker scripts.
s=(H/'synthetic-reviewed.py').read_text();prefix=s[:s.index('\ndef run():')];write('synthetic-data.py',prefix)
f=(H/'full-audit-tests-reviewed.py').read_text().replace("D/'synthetic-reviewed.py'","D/'synthetic-data.py'")
f=f.replace("  cfg.update(phase='green300',mode='green',expected_exit=0);seal['phase']='green300';docs['reservation.json'].update(phase='green300');process.update(returncode=0,reason='exit0');raw,units=mock('green')\n  restore();ck('complete_GREEN',a.checks_for('green300')['all_passed'])\n",'')
f=f.replace("a.audit('green300')","a.audit('red300')").replace("D/'full-audit-tests-reviewed.json'","D/'auditor-tests.json'")
write('auditor-tests.py',f)
for p in D.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
save('adaptations.json',dict(copied=len(copied),control_changes=['RED-only phase gate','new package-relative run/outer/driver roots','master repaired stage binding with independent repair review/publication','new preparation/review scope and immutable inputs','271 prior groups from fresh entry','no GREEN predecessor'],unchanged=['driver and all Julia test clones','candidate14files','oracle.py','guard.py','supervisor.py','resource limits and inclusive300/inner292','assertion sites and expected six N026'],runtime_acceptance=False))
print('New separate RED2 harness written; no execution admission')
