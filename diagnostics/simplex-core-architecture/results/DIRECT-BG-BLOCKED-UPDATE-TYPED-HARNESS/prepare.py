"""Offline preparation only. Never invokes Julia or any launch entrypoint."""
from pathlib import Path
import json,hashlib,os
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');B=R/'diagnostics/simplex-core-architecture/results';D=B/'DIRECT-BG-BLOCKED-UPDATE-TYPED-HARNESS';P=B/'DIRECT-BG-P011-TYPED-HARNESS';F=B/'DIRECT-BG-BLOCKED-UPDATE-HARNESS';T=B/'DIRECT-BG-P011-TYPED-REPAIR';Z=B/'DIRECT-BG-ZERO-COUNTS-CANDIDATE';C=R/'diagnostics/direct-bg-blocked-update/reproduce'
D.mkdir(exist_ok=False)
def put(n,v):
 with (D/n).open('xb') as f:f.write(v if isinstance(v,bytes) else v.encode())
def js(n,v):put(n,json.dumps(v,indent=2)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
put('prepare.py',Path(__file__).read_bytes());put('host-entry.json',Path('/tmp/bg-typed-full-host.json').read_bytes());js('historical-groups.json',{'groups':json.loads(Path('/tmp/bg-typed-full-host.json').read_text())['groups']})
put('progress.md.before-preparation',(R/'.superpowers/sdd/2026-10-19-direct-bg-blocked-update/progress.md').read_bytes())
put('request.txt','Prepare a separate blocked BG U RED/GREEN driver with the accepted typed P011 repair and immutable zero counters, launch conditions and complete auditor, independently reviewed. No Julia execution in this task.\n')
copied={}
for src,names in [(P,['guard.py','supervisor.py','post-return.py','baseline.json','runtime-inputs-complete.json','stages.json','environment.json']), (F,['recorder.jl','numerical-tests.jl','lifecycle-tests.jl','schedule.json','loaded-paths.json']), (C,['factor.jl','factor-fault.jl']), (T,['panel-tests.jl']), (Z,['panel.jl'])]:
 for n in names:put(n,(src/n).read_bytes());copied[n]={'source':str(src/n),'sha256':sha(src/n)}
# Fault clone receives exactly the same immutable tuple amendment, preserving its hooks.
p=(C/'panel-fault.jl').read_text();edits=[('const Upper = Vector{J.PackedUpperColumn{Float64,J.UpperRowIndices}}','const Upper = Vector{J.PackedUpperColumn{Float64,J.UpperRowIndices}}\nconst _BGB_ZERO_COUNTS = ntuple(_ -> 0, Val(20))'),('BGPanelCounts(ntuple(_ -> 0,20))','BGPanelCounts(_BGB_ZERO_COUNTS)'),('counts(::BGNoCounts) = ntuple(_->0,20)','counts(::BGNoCounts) = _BGB_ZERO_COUNTS'),('true,ntuple(_->0,20))','true,_BGB_ZERO_COUNTS)')]
for a,b in edits:
 if p.count(a)!=1:raise RuntimeError('Fault edit anchor '+a)
 p=p.replace(a,b,1)
put('panel-fault.jl',p);js('fault-transform.json',{'source':str(C/'panel-fault.jl'),'source_sha256':sha(C/'panel-fault.jl'),'prepared_sha256':sha(D/'panel-fault.jl'),'edits':edits})
js('copied-files.json',copied)
s=(P/'control.py').read_text().replace("ENTRY='42ebde242bf900cec375f970982f97469f013559'","ENTRY='2821702085f6bdaceb48c71a8774c99200e242eb'")
s=s.replace("('p011-red300','p011-green300')","('red300','green300')").replace("phase=='p011-red300'","phase=='red300'").replace("red='p011-red300'","red='red300'").replace('Only prepared P011 RED/GREEN phases','Only prepared blocked BG typed RED/GREEN phases')
s=s.replace('P011 typed harness preparation','BG blocked typed harness preparation').replace('P011 typed RED result','BG blocked typed RED result')
s=s.replace("return files+[str(run/filename)],rd(run/'posthost.json')['groups']","require('evidence_sha256' not in v or bindings(v,'evidence_sha256'),'Result supplementary drift')\n return files+[str(run/filename)],rd(run/'outer-closure.json')['host']['groups']")
s=s.replace('validate_stage_binding();validate_probe();validate_typed()','validate_stage_binding();validate_probe();validate_typed();validate_qualification()')
a=s.index('def test_source_for(');s=s[:a]+'''def test_source_for(phase):
 config(phase)
 return str(D/'panel-tests.jl')

def validate_qualification():
 q=rd(D/'qualification-bindings.json')
 require(bindings(q),'Accepted typed GREEN or source lineage drift')
 for p in q['accepted_receipts']:
  v=rd(p);require(v.get('accepted') is True and v.get('findings')==[],'Prior qualification acceptance')
  require(bindings(v) and ('evidence_sha256' not in v or bindings(v,'evidence_sha256')),'Prior qualification receipt drift')
 f=rd(D/'fault-transform.json');s=(D/'panel-fault.jl').read_text()
 for old,new in reversed(f['edits']):
  require(s.count(new)==1,'Fault inverse anchor');s=s.replace(new,old,1)
 require(s.encode()==Path(f['source']).read_bytes() and sha(f['source'])==f['source_sha256'] and sha(D/'panel-fault.jl')==f['prepared_sha256'],'Fault exact inverse')
'''
put('control.py',s)
for n in ['launch.py','seal.py','outer.py']:
 s=(P/n).read_text().replace('P011 typed exact-run admission','BG blocked typed exact-run admission').replace('P011 typed RED/GREEN','BG blocked typed RED/GREEN')
 put(n,s)
s=(P/'audit.py').read_text().replace('P011 typed exact-run admission','BG blocked typed exact-run admission').replace('result=validate(data,loaded_for(cfg),phase,test_source_for(phase))','result=validate(data,rd(D/\'schedule.json\'),loaded_for(cfg),phase)').replace('warning_log(log,data,phase)','warning_log(log,data,phase)')
s=s.replace('P011 structural qualification only; no Task2 lifecycle/streams or performance acceptance','Full blocked BG structural/lifecycle/stream qualification; no Task3 performance acceptance').replace('Saved P011 RED/GREEN integrity/results','Saved blocked BG typed RED/GREEN integrity/results')
put('audit.py',s)
# Static accepted qualification bindings, never run the historical scripts.
G=B/'DIRECT-BG-P011-TYPED-GREEN';run=P/'runs/p011-green300';paths={p for root in [G,run,P/'outers/p011-green300'] for p in root.rglob('*') if p.is_file()}
paths.update(p for p in C.rglob('*') if p.is_file());paths.update([F/'review.json',F/'preparation-pins-reviewed.json',F/'test-transform.json',F/'assertion-sites.json'])
js('qualification-bindings.json',{'scope':'Historical acceptance/source linkage, not launch admission','accepted_receipts':[str(run/'result-review.json'),str(F/'review.json')],'sha256':{str(p):sha(p) for p in sorted(paths)}})
print(D)
