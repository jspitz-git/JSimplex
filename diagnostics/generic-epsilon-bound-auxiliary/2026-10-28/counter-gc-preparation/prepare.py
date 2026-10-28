from pathlib import Path
import sys,json,shutil,ast,importlib.util
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-epsilon-bound-auxiliary/2026-10-28');P=D/'counter-capture';Q=D/'counter-gc-preparation';sys.path.insert(0,str(P));import common as c
r=c.read('result-review.json');c.need(r['accepted'] is True,'independent data review');c.need((D/'counter-capture-diagnosis.json').exists(),'fixed hypothesis review')
p=c.read('output/process.json');extra=[p[k][v] for k in ['runner','child'] for v in ['pgid','sid']];h=c.host(extra);h['diagnostic_head']=c.git(['rev-parse','HEAD'],c.R);h['master_head']=c.git(['rev-parse','HEAD']);c.unchanged();Q.mkdir()
for n in ['common.py','launch.py','environment.json','protected-before.json']:shutil.copyfile(P/n,Q/n)
for n in ['host-before.json','host-seed.json']:c.put(str(Q/n),h)
shutil.copytree(P/'guard',Q/'guard',ignore=shutil.ignore_patterns('__pycache__'))
changes=[]
for old in c.read('source-inverse.json')['changes']:
 name=old['file'];s=(P/name).read_text()
 if name.startswith('generic_unit'):
  needle=' before=Any[];after=Any[]'
  gc=' gc_preparation = T===Rational{BigInt}&&arm===:C ? (@timed GC.gc(true)) : nothing\n'
  block=old['insertion'].replace('"before"=>before,','"gc_preparation"=>cost(gc_preparation),"before"=>before,')
 else:
  needle=' before=Tuple{Int,Int}[];after=Tuple{Int,Int}[];records=Dict{String,Any}[]'
  gc=' gc_preparation=@timed GC.gc(true)\n'
  block=old['insertion'].replace('"before"=>[collect(v) for v in before],','"gc_preparation"=>batch_cost(gc_preparation),"before"=>[collect(v) for v in before],')
 c.need(s.count(needle)==1 and s.count(old['insertion'])==1 and block!=old['insertion'],'unique fixed intervention '+name)
 s=s.replace(old['insertion'],block).replace(needle,gc+needle);(Q/name).write_text(s)
 c.need(s.replace(block,'').replace(gc,'')==(c.M/'test'/name).read_text(),'exact unchanged original inverse '+name)
 ch=dict(old,insertion=block,preparation_insertion=gc,diagnostic_sha256=c.sha(Q/name));ch['gate_line']=next(i for i,x in enumerate(s.splitlines(),1) if (x.startswith(' @test all(after[k]') if name.startswith('generic_unit') else x.startswith('  @test all(100*after[i][1]<97*before[i][1]')))
 changes.append(ch)
c.put(str(Q/'source-inverse.json'),dict(accepted=True,source_commit=c.TARGET,changes=changes,only_intervention='One explicit fullGC after all existing warmups per each of four named Rational gates; no between-arm/pair GC or retry',numerical_checks_thresholds_warmups_samples_order_unchanged=True,observation_only_after_measurements=True,observer_neutrality_not_proved=True))
(Q/'tests.jl').write_text((P/'tests.jl').read_text().replace(str(P),str(Q)))
s=(P/'audit.py').read_text().replace("'mode','before'","'mode','gc_preparation','before'").replace("'batch_size','before'","'batch_size','gc_preparation','before'")
s=s.replace("   a,b=x['before'],x['after'];need(len(a)==len(b)==3,'three UPR pairs')","   cost(x['gc_preparation']);need(x['gc_preparation']['gc_seconds']>0,'fullGC preparation observed outside window')\n   a,b=x['before'],x['after'];need(len(a)==len(b)==3,'three UPR pairs')")
s=s.replace("   a,b=x['before'],x['after'];need(len(a)==len(b)==3 and all(type(y)","   cost(x['gc_preparation'],True);need(x['gc_preparation']['gc_raw']['full_sweep']>=1 and x['gc_preparation']['gc_seconds']>0,'explicit fullGC preparation recorded')\n   a,b=x['before'],x['after'];need(len(a)==len(b)==3 and all(type(y)")
s=s.replace("copy.read_text().replace(ch['insertion'],'')==src.read_text()","copy.read_text().replace(ch['insertion'],'').replace(ch['preparation_insertion'],'')==src.read_text()")
s=s.replace("source_unchanged=True,unchanged_thresholds=True","source_unchanged=True,unchanged_thresholds=True,one_preregistered_postwarm_gc_trial=True")
s=s.replace("original_cost_gate_passed=passed,before=a,after=b","original_cost_gate_passed=passed,preparation_gc=x['gc_preparation'],before=a,after=b")
(Q/'audit.py').write_text(s)
con=c.read('contract.json');con['command']=[x.replace(str(P),str(Q)) for x in con['command']];con['files']=[x.replace(str(P),str(Q)) for x in con['files']];con['scope']='ONE preregistered preparation-state hypothesis test: exactly one fullGC after warmups per each of four named Rational gates, recorded outside windows; unchanged all23663checks/warmups/samples/order/thresholds; no between-arm/pair GC/filter/retry. Neither original failed run is waived; not release qualification.';con['explicit_full_gc_calls']=4;c.put(str(Q/'contract.json'),con)
(Q/'PLAN.md').write_text('''# One fixed post-warm full-GC preparation control\n\nHypothesis: prior preparation/garbage/allocator state can affect native aggregate byte traffic. No measured GC cause or original malloc cause has been proved. Source evidence: counter-capture-diagnosis.json. This is exactly one preregistered experiment, not repeated sampling until a pass.\n\nThe same three ordinary whole files/23663checks, fixtures/data, three warm pairs, three measured alternating pairs, strict event/byte and3percent thresholds stay unchanged. Only four named Rational gates get ONE fullGC after existing warmups (and existing zero-allocation wrapper qualification for DUAL), before all measured windows. No GC between arms/pairs, no filtering, no retry, no changes in production source/test/env/CI. Preparation GC seconds/bytes/events/compile/GCraw cost are separately recorded after measurements. Full original source recovered exactly by removing logging/preparation insertions.\n\nSingle900s/892guard process, usual fresh fullgroups/sessions/boot/start/command/noJulia/refs/pins/resource controls and independent admission/result review. A pass demonstrates sensitivity/control observations only; it does not prove original cause, approve permanent test changes, waive failedMASTER or qualify release. If controls still fail, no adaptive GC, batch growth, threshold change or further tuning follows from this plan.\n''')
shutil.copyfile(__file__,Q/'prepare.py')
paths=set(c.read('pins.json')['inventory']);paths.update(str(x) for x in Q.rglob('*') if x.is_file() and '__pycache__' not in x.parts)
for n in ['result-review.json','audit.json','capture-data.json','output/run.log','output/process.json','audit-host.json','supervisor.json']:paths.add(str(P/n))
paths.add(str(D/'counter-capture-diagnosis.json'))
c.put(str(Q/'pins.json'),dict(files=sorted(paths),trees=c.read('pins.json')['trees'],inputs=[],inventory={n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=c.sha(n)) for n in sorted(paths)}))
sp=importlib.util.spec_from_file_location('gc_common',Q/'common.py');q=importlib.util.module_from_spec(sp);sp.loader.exec_module(q);q.unchanged();q.put('author-host.json',q.host())
for x in Q.glob('*.py'):ast.parse(x.read_text())
print('Fixed oneGC preparation hypothesis sealed',len(paths),'pins; noJulia; all23663originalchecks preserved')
