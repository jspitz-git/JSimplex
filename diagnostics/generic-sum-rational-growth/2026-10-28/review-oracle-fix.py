from pathlib import Path
import sys,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-sum-rational-growth/2026-10-28');sys.path.insert(0,str(D));import common as c
c.need(c.read('admission-reviewed.json')['accepted'] is False,'rejected review preserved')
e=(D/'extra-tests-reviewed.jl').read_text();old='out=checkpair(a,b,:B);@test out[1]===:error;@test out[2]===DivideError';c.need(e.count(old)==1,'unique infinity oracle')
e=e.replace(old,'''out=checkpair(a,b,:B)
    if rhosign==-1&&mode===:one_sided&&what===:infinite
     @test out[1]===:value;@test out[2]===false
    else
     @test out[1]===:error;@test out[2]===DivideError
    end''');(D/'extra-tests-ready.jl').write_text(e)
(D/'driver-ready.jl').write_text((D/'driver-reviewed.jl').read_text().replace('extra-tests-reviewed.jl','extra-tests-ready.jl'))
(D/'common_ready.py').write_text((D/'common_reviewed.py').read_text().replace('contract-reviewed.json','contract-ready.json').replace('pins-reviewed.json','pins-ready.json'))
(D/'launch-ready.py').write_text((D/'launch-reviewed.py').read_text().replace('common_reviewed','common_ready').replace('admission-reviewed.json','admission-ready.json').replace('contract-reviewed.json','contract-ready.json').replace('pins-reviewed.json','pins-ready.json'))
(D/'audit-ready.py').write_text((D/'audit.py').read_text().replace('common_reviewed','common_ready').replace('contract-reviewed.json','contract-ready.json').replace('pins-reviewed.json','pins-ready.json').replace("'audit.py'","'audit-ready.py'"))
contract=c.read('contract-reviewed.json');contract['command']=[v.replace(str(D/'driver-reviewed.jl'),str(D/'driver-ready.jl')) for v in contract['command']];c.put('contract-ready.json',contract)
c.put('review-oracle-fix.json',dict(Julia_executed=False,rule='Stored -Inf with one-sided selected bound unbounded returns false; ±Inf multiplied by explicitzero and finite selectedbounds still raise DivideError',fixed_assertions_per_case=2,all_case_count_unchanged=2636,windows_unchanged=47448,candidates_unchanged=c.read('source-clones.json'),extra_before=c.sha(D/'extra-tests-reviewed.jl'),extra_after=c.sha(D/'extra-tests-ready.jl')))
shutil.copyfile(__file__,D/'review-oracle-fix.py');c.unchanged();c.put('ready-host.json',c.host());paths=set(c.read('pins-reviewed.json')['files']);paths.update(str(p) for p in D.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
c.put('pins-ready.json',dict(files=sorted(paths),trees=c.read('pins.json')['trees'],inputs=[str(D/'grid.toml')],inventory={n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=c.sha(n)) for n in sorted(paths)}))
for name in ['common_ready.py','launch-ready.py','audit-ready.py']:compile((D/name).read_text(),str(D/name),'exec')
print('minimal ready oracle correction sealed',len(paths),'pins; noJulia')
