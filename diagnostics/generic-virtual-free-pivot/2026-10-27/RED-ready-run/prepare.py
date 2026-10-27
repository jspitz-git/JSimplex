from pathlib import Path
import sys,json,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-virtual-free-pivot/2026-10-27');O=D/'RED-run';Q=D/'RED-ready-run';Q.mkdir();sys.path.insert(0,str(O));import common as c
s=(D/'new-test.jl').read_text();a='module GenericVirtualFreePivotTests\n';b=a+'using Test,JSimplex,SparseArrays,LinearAlgebra\n';c.need(s.count(a)==1,'outer module import');(D/'new-test-reviewed.jl').write_text(s.replace(a,b,1))
for n in ['common.py','launch.py','audit.py','environment.json','protected-before.json','host-seed.json','host-before.json']:shutil.copyfile(O/n,Q/n)
co=c.read('contract.json');co['command']=[v.replace(str(O),str(Q)) for v in co['command']];co['files']=[str(D/'new-test-reviewed.jl')];co['expected_failure_locations']=[[str(D/'new-test-reviewed.jl'),i] for i,l in enumerate((D/'new-test-reviewed.jl').read_text().splitlines(),1) if '# RED whole-call cost gate' in l]*5
s=(O/'tests.jl').read_text().replace(json.dumps(['generic_virtual_free_pivot_tests.jl']),json.dumps(co['files']));(Q/'tests.jl').write_text(s)
(Q/'contract.json').write_text(json.dumps(co,indent=2)+'\n');shutil.copytree(O/'guard',Q/'guard',ignore=shutil.ignore_patterns('__pycache__'))
(Q/'FIX.md').write_text('Pre-execution RED admission found outer module JSimplex import missing before const aliases. New ordinarytest adds only outer using Test,JSimplex,SparseArrays,LinearAlgebra after module start; original test/stage/RED-run remain unexecuted/preserved. Corrected test is included directly by absolute path under ordinary Test against exact unchanged D/RED source; no production stage edit yet. Five expected cost failures, all numerical expectations unchanged. GREEN will install exactly new-test-reviewed.jl as permanent test, preserving source inverse.\n')
shutil.copyfile(__file__,Q/'prepare.py');pins=c.read('pins.json');paths=set(pins['inventory']);paths.update(str(p) for p in Q.rglob('*') if p.is_file());paths.add(str(D/'new-test-reviewed.jl'))
(Q/'pins.json').write_text(json.dumps(dict(files=sorted(paths),trees=pins['trees'],inputs=[],inventory={n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=c.sha(n)) for n in sorted(paths)}),indent=2,sort_keys=True)+'\n')
print(len(paths),'pins, samebaseline unchanged; noJulia')
