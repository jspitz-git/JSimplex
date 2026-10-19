from pathlib import Path
import json,hashlib,os
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');Z=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-ZERO-COUNTS-HARNESS';T=Z.with_name('DIRECT-BG-P011-TYPED-REPAIR');F=Z.with_name('DIRECT-BG-BLOCKED-UPDATE-RED2-HARNESS');D=Z.with_name('DIRECT-BG-P011-TYPED-HARNESS');D.mkdir(exist_ok=False)
def put(n,b):
 with (D/n).open('xb') as f:f.write(b if isinstance(b,bytes) else b.encode())
def js(n,v):put(n,json.dumps(v,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
put('prepare.py',Path(__file__).read_bytes());put('host-entry.json',Path('/tmp/p011-harness-host.json').read_bytes())
ledger=R/'.superpowers/sdd/2026-10-19-direct-bg-blocked-update/progress.md';put('progress.md.before-p011-harness',ledger.read_bytes())
copied={}
for n in ['guard.py','supervisor.py','post-return.py','baseline.json','runtime-inputs-complete.json','stages.json']:
 put(n,(Z/n).read_bytes());copied[n]={'source':str(Z/n),'sha256':sha(Z/n)}
put('recorder.jl',(F/'recorder.jl').read_bytes());copied['recorder.jl']={'source':str(F/'recorder.jl'),'sha256':sha(F/'recorder.jl')};js('copied-files.json',copied)
js('historical-groups.json',{'groups':json.loads(Path('/tmp/p011-harness-host.json').read_text())['groups']})
js('environment.json',{k:os.environ.get(k) for k in json.loads((Z/'environment.json').read_text())})
loaded=json.loads((F/'loaded-paths.json').read_text());loaded={k:v for k,v in loaded.items() if k in ['LinearAlgebra','TOML','Test','PrecompileTools']};js('loaded-paths.json',loaded)
p=(Z/'control.py').read_text().replace("ENTRY='716b7ecfd6df6172edaf19cb21e6446c08bf29b0'","ENTRY='42ebde242bf900cec375f970982f97469f013559'")
p=p.replace("PROBE=D.with_name('DIRECT-BG-ZERO-COUNTS-CANDIDATE')","PROBE=D.with_name('DIRECT-BG-ZERO-COUNTS-CANDIDATE')\nTYPED=D.with_name('DIRECT-BG-P011-TYPED-REPAIR')\nREDTEST=D.with_name('DIRECT-BG-BLOCKED-UPDATE-RED2-HARNESS')/'panel-tests.jl'")
p=p.replace("require(phase == 'zero-counts-300','Only separately prepared zero-counts-300 is allowed')","require(phase in ('p011-red300','p011-green300'),'Only prepared P011 RED/GREEN phases are allowed')")
p=p.replace("str(payload),stage]","str(payload),stage,phase]")
p=p.replace("expected_exit=0,stage=stage","expected_exit=1 if phase=='p011-red300' else 0,stage=stage")
p=p.replace('BG zero-count harness preparation','P011 typed harness preparation').replace('BG zero-count exact-run admission','P011 typed exact-run admission')
p=p.replace('validate_stage_binding();validate_probe()','validate_stage_binding();validate_probe();validate_typed()')
a=p.index('def predecessor(phase):');b=p.index('def outer_dir(phase):',a)
p=p[:a]+'''def predecessor(phase):
 config(phase)
 if phase=='p011-red300':return [],[]
 red='p011-red300';run=D/'runs'/red
 require(rd(run/'audit.json').get('all_passed') is True,'Accepted RED audit required')
 validate_result_closure(red,rd(run/'outer-closure.json'))
 files,groups=result_review(red,'P011 typed RED result','result-review.json')
 return sorted(set(files+[str(p) for p in closure_paths(red)])),groups
'''+p[b:]
p=p.replace("[cfg['stage'],str(C),str(PROBE)]","[cfg['stage'],str(C),str(PROBE),str(TYPED)]")
p+='''
def validate_typed():
 v=rd(TYPED/'independent-review.json')
 require(v.get('disposition')=='ACCEPTED — PREPARATION ONLY' and v.get('findings')==[] and v.get('runtime_executed') is False,'Typed repair review')
 require(all(sha(Path(n))==h for n,h in v['reviewed_bindings'].items()),'Typed repair reviewed sources')
 require(sha(TYPED/'independent-review.md')==v['review_markdown_sha256'],'Typed repair review text')
 require(sha(TYPED/'panel-tests.jl')=='15faee72f0f40bddae911818379c99d56aeb4a96e24cb7ce901691f188888910','Exact typed tests')
 require(sha(TYPED/'helpers.jl')=='24164ea279f5eeaaf5a9860ffb11a813ac98e1d8ed8d950c957cd4d2be6c5f6f','Exact helper')
 require(sha(REDTEST)=='694c34056e4a1fda5819d494022cb154694ef3412e7176571949c28e00af3f41','Exact original tests')
'''
put('control.py',p)
for n in ['launch.py','seal.py','outer.py']:
 p=(Z/n).read_text().replace('BG zero-count exact-run admission','P011 typed exact-run admission').replace('zero-count diagnostic','P011 typed RED/GREEN')
 p=p.replace("[cfg['stage'],str(C),str(PROBE)]","[cfg['stage'],str(C),str(PROBE),str(TYPED)]")
 put(n,p)
p=(Z/'audit.py').read_text().replace('BG zero-count exact-run admission','P011 typed exact-run admission')
p=p.replace("p['returncode']==0 and p['reason']=='exit0'","p['returncode']==cfg['expected_exit'] and p['reason']=='exit'+str(cfg['expected_exit'])")
p=p.replace("require(not warning_log(log),'Warning/world-age/error log')\n result=validate({p.name:tomllib.loads(p.read_text()) for p in payload.iterdir()},loaded_for(cfg))", "data={p.name:tomllib.loads(p.read_text()) for p in payload.iterdir()}\n result=validate(data,loaded_for(cfg),phase,test_source_for(phase))\n require(not warning_log(log,data,phase),'Warning/world-age/unexpected error log')")
p=p.replace('Exact69 payload','Exact P011 payload').replace('Diagnostic completeness only, not P011/RED/GREEN or performance acceptance','P011 structural qualification only; no Task2 lifecycle/streams or performance acceptance').replace('Saved zero-count diagnostic integrity/results; independent result review required','Saved P011 RED/GREEN integrity/results; independent result review required')
put('audit.py',p)
with (D/'control.py').open('a') as f:f.write("\ndef test_source_for(phase):\n config(phase)\n return str(REDTEST if phase=='p011-red300' else TYPED/'panel-tests.jl')\n")
print(D)
