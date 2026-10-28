from pathlib import Path
import sys,json,shutil,ast
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-epsilon-bound-auxiliary/2026-10-28');S=D/'MASTER-run';P=D/'counter-capture';sys.path.insert(0,str(S));import common as c
c.need(c.read('result-review.json')['accepted'] is False,'rejected MASTER preserved');c.unchanged()
s=(P/'tests.jl').read_text().replace('@testset "Legacy allocation counter capture"','println("COUNTER_SOURCE ",pathof(JSimplex));flush(stdout)\n@testset "Legacy allocation counter capture"');(P/'tests.jl').write_text(s)
for n in ['common.py','environment.json','protected-before.json']:shutil.copyfile(S/n,P/n)
l=(S/'launch.py').read_text().replace('4492','892').replace('4500','900');(P/'launch.py').write_text(l)
shutil.copytree(S/'guard',P/'guard',ignore=shutil.ignore_patterns('__pycache__'))
cmd=c.read('contract.json')['command'];cmd[-1]=str(P/'tests.jl')
files=[str(c.M/'test/generic_epsilon_bound_auxiliary_tests.jl'),str(P/'generic_unit_perturb_residual_tests.jl'),str(P/'generic_dual_comparisons_tests.jl')]
c.put(str(P/'contract.json'),dict(arm='COUNTER_CAPTURE',command=cmd,source_root=str(c.M),files=files,expected_total=23663,expected_exit=0,diagnostic_possible_test_exit=[0,1],attempts=1,shared_limit_seconds=900,guard_limit_seconds=892,source_commit=c.TARGET,scope='Named counter diagnosis only; failed Test exit remains failed. Not production qualification. No GC, sampling, thresholds, warmups or original assertions changed; three-file cohort is not exact fullsuite allocator-state replay.'))
shutil.copyfile('/tmp/eba-capture-audit.py',P/'audit.py')
shutil.copyfile(__file__,P/'controls-prepare.py')
paths=set(c.read('pins.json')['inventory']);paths.update(str(p) for p in P.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
for n in ['failure-audit.json','result-review.json','failure-postcheck-review.json','failure-postcheck.py','failure-audit-host.json','output/run.log','output/process.json','supervisor.json']:paths.add(str(S/n))
for n in ['master-cost-source-review.json','master-second-cost-source-review.json']:paths.add(str(D/n))
c.put(str(P/'pins.json'),dict(files=sorted(paths),trees=c.read('pins.json')['trees'],inputs=[],inventory={n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=c.sha(n)) for n in sorted(paths)}))
import importlib.util
sp=importlib.util.spec_from_file_location('capture_common',P/'common.py');pc=importlib.util.module_from_spec(sp);sp.loader.exec_module(pc);pc.unchanged();pc.put('author-host.json',pc.host())
for p in P.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
print('Countercapture concrete controls sealed',len(paths),'pins/23663checks, noJulia')
