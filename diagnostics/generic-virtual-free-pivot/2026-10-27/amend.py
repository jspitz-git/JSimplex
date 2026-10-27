from pathlib import Path
import sys,shutil,json
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-virtual-free-pivot/2026-10-27');sys.path.insert(0,str(D));import common as c
shutil.copyfile('/tmp/vfp-extra.jl',D/'extra-tests.jl')
s=(D/'driver.jl').read_text();a='include(joinpath(@__DIR__,"fixtures.jl"))';b='ct=@timed correctness(T);';c.need(s.count(a)==s.count(b)==1,'two insertions')
s=s.replace(a,a+'\ninclude(joinpath(@__DIR__,"extra-tests.jl"))').replace(b,'ct=@timed begin;correctness(T);extra_correctness(T);end;')
(D/'driver-reviewed.jl').write_text(s)
c.put('driver-amendment.json',dict(accepted=True,reason='pre-execution independent admission boundary coverage findings',original_unexecuted=True,originals_preserved=True,source_candidates_unchanged=True,two_insertions=True))
old=c.read('contract.json');old['command']=[v.replace('/driver.jl','/driver-reviewed.jl') for v in old['command']];c.put('contract-reviewed.json',old)
s=(D/'launch.py').read_text().replace("read('contract.json')","read('contract-reviewed.json')").replace("D/'pins.json'","D/'pins-reviewed.json'")
(D/'launch-reviewed.py').write_text(s)
s=(D/'common.py').read_text().replace("read('contract.json')","read('contract-reviewed.json')").replace("read('pins.json')","read('pins-reviewed.json')")
(D/'common_reviewed.py').write_text(s)
for n in ['launch-reviewed.py']:
 s=(D/n).read_text().replace('from common import *','from common_reviewed import *');(D/n).write_text(s)
s=(D/'audit.py').read_text().replace('import common as c','import common_reviewed as c').replace("c.read('contract.json')","c.read('contract-reviewed.json')").replace("'pins.json'","'pins-reviewed.json'").replace("'audit.py'","'audit-reviewed.py'")
(D/'audit-reviewed.py').write_text(s)
shutil.copyfile(__file__,D/'amend.py')
pins=c.read('pins.json');paths=set(pins['inventory']);paths.update(str(D/n) for n in ['extra-tests.jl','driver-reviewed.jl','driver-amendment.json','contract-reviewed.json','launch-reviewed.py','common_reviewed.py','audit-reviewed.py','amend.py','pins.json'])
c.put('pins-reviewed.json',dict(files=sorted(paths),trees=pins['trees'],inputs=[],inventory={n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=c.sha(n)) for n in sorted(paths)}))
print(len(paths),'reviewed pins; original unexecuted preserved')
