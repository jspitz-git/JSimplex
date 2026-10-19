"""One offline RED repeat preparation; never invokes numerical entrypoints."""
from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent;R=D.parents[3];P=D.with_name('DIRECT-BG-BLOCKED-UPDATE-TYPED-HARNESS');E=P.with_name('DIRECT-BG-BLOCKED-UPDATE-TYPED-RED')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,j):
 with (D/n).open('x') as f:json.dump(j,f,indent=2);f.write('\n')
def write(n,b):
 with (D/n).open('xb') as f:f.write(b)
copies=['driver.jl','panel.jl','panel-fault.jl','factor.jl','factor-fault.jl','panel-tests.jl','numerical-tests.jl','lifecycle-tests.jl','recorder.jl','guard.py','supervisor.py','post-return.py','baseline.json','runtime-inputs-complete.json','stages.json','environment.json','schedule.json','loaded-paths.json','qualification-bindings.json','fault-transform.json','synthetic-data.py','assertion-sites.json']
for n in copies:write(n,(P/n).read_bytes())
save('copied-files.json',{n:dict(source=str(P/n),sha256=sha(P/n)) for n in copies})
transforms={}
def change(n,edits):
 s=(P/n).read_text();applied=[]
 for old,new,count in edits:
  if s.count(old)!=count:raise RuntimeError('Anchor '+n+' '+repr(old)+' '+str(s.count(old)))
  s=s.replace(old,new);applied.append(dict(old=old,new=new,count=count))
 write(n,s.encode());transforms[n]=dict(source=str(P/n),source_sha256=sha(P/n),prepared_sha256=sha(D/n),edits=applied)
oldpred="""def predecessor(phase):
 config(phase)
 if phase=='red300':return [],[]
 red='red300';run=D/'runs'/red
 require(rd(run/'audit.json').get('all_passed') is True,'Accepted RED audit required')
 validate_result_closure(red,rd(run/'outer-closure.json'))
 files,groups=result_review(red,'BG blocked typed RED result','result-review.json')
 return sorted(set(files+[str(p) for p in closure_paths(red)])),groups
"""
newpred="""def predecessor(phase):
 config(phase)
 validate_timeout_record()
 return sorted(rd(D/'timeout-bindings.json')['sha256']),rd(D/'historical-groups.json')['groups']
"""
timeout="""
def validate_timeout_record():
 t=rd(D/'timeout-bindings.json');require(bindings(t),'Prior timeout evidence drift')
 v=rd(t['review']);require(v.get('accepted') is True and v.get('qualification_accepted') is False and v.get('findings')==[] and v.get('scope')=='BG blocked typed RED timeout diagnostic','Prior record must remain diagnostic only')
 require(bindings(v) and bindings(v,'evidence_sha256'),'Prior timeout review drift')
 a=rd(t['audit']);require(a.get('all_passed') is False and a.get('pure_timeout') is False,'Do not reinterpret failed RED as success')
 require(not Path(t['run']).joinpath('result-review.json').exists(),'No retrospective accepted RED receipt')
 require(set(rd(D/'historical-groups.json')['groups'])==set(rd(t['closure'])['host']['groups']) and len(rd(D/'historical-groups.json')['groups'])==289,'Full289 historical roster')
"""
change('control.py',[
 ("ENTRY='2821702085f6bdaceb48c71a8774c99200e242eb'","ENTRY='67533adf18a5ba4929e77cafa73472c29d3dd5d0'",1),
 ("require(phase in ('red300','green300'),'Only prepared blocked BG typed RED/GREEN phases are allowed')","require(phase=='red1800','Only separately prepared red1800 is allowed')",1),
 ("str(payload),stage,phase]","str(payload),stage,'red300'] # unchanged driver semantic phase; new external attempt is red1800",1),
 ("seconds=300,expected_exit=1 if phase=='red300' else 0","seconds=1800,expected_exit=1",1),
 ('BG blocked typed harness preparation','BG blocked typed RED repeat preparation',1),
 ("validate_stage_binding();validate_probe();validate_typed();validate_qualification()","validate_stage_binding();validate_probe();validate_typed();validate_qualification();validate_timeout_record()",1),
 (oldpred,newpred,1),
 (" return sorted(set(j['sha256'])|{str(m),str(D/'review.json')}|set(rd(D/'review.json').get('evidence_sha256',{})))"," return sorted(set(j['sha256'])|{str(m),str(D/'review.json')}|set(rd(D/'review.json').get('evidence_sha256',{})))",1)
 ])
# Append new fail-closed prior-result lineage definition; recorded separately for inverse.
s=(D/'control.py').read_bytes();(D/'control.py').write_bytes(s+timeout.encode());transforms['control.py']['append']=timeout;transforms['control.py']['prepared_sha256']=sha(D/'control.py')
for n in ['seal.py','outer.py','launch.py']:
 edits=[]
 if 'BG blocked typed exact-run admission' in (P/n).read_text():edits.append(('BG blocked typed exact-run admission','BG blocked typed RED repeat exact-run admission',1))
 if n=='seal.py':edits.append(('SEALED exact BG blocked typed RED/GREEN phase','SEALED exact BG blocked typed RED1800 repeat',1))
 change(n,edits)
change('oracle.py',[('0<=v[k]<=300','0<=v[k]<=1800',1)])
change('audit.py',[
 ('0<=elapsed<=292','0<=elapsed<=1792',1),
 ('BG blocked typed exact-run admission','BG blocked typed RED repeat exact-run admission',1),
 ("result=validate(data,rd(D/'schedule.json'),loaded_for(cfg),phase)","result=validate(data,rd(D/'schedule.json'),loaded_for(cfg),'red300') # unchanged Julia/raw RED semantic phase",1),
 ('warning_log(log,data,phase)',"warning_log(log,data,'red300')",1)
 ])
save('control-transform.json',transforms)
oldrun=P/'runs/red300';oldo=P/'outers/red300';files={p for root in [E,oldrun,oldo] for p in root.rglob('*') if p.is_file()}
files|={P/n for n in ['review.json','review.md','preparation-pins.json','required-paths.json','closure.json','publication.json']}
save('timeout-bindings.json',dict(review=str(E/'result-review.json'),audit=str(oldrun/'audit.json'),closure=str(oldrun/'outer-closure.json'),run=str(oldrun),sha256={str(p):sha(p) for p in sorted(files)}))
h=json.loads(Path('/tmp/bg-red1800-host.json').read_text());save('historical-groups.json',dict(groups=h['groups'],source=str(oldrun/'outer-closure.json'),scope='Old286 plus RED outer/guard/child; full PGID AND SID'))
write('host-entry.json',Path('/tmp/bg-red1800-host.json').read_bytes())
write('progress.md.before-red1800',(R/'.superpowers/sdd/2026-10-19-direct-bg-blocked-update/progress.md').read_bytes())
write('request.txt','Prosím připrav samostatné podmínky opakování RED s delším časovým limitem při zachování driveru a všech kontrol a nech je nezávisle zkontrolovat, zatím bez spuštění Julie.\n'.encode())
print(json.dumps(dict(copied=len(copies),transformed=list(transforms),timeout_bindings=len(files),no_Julia=True)))
