from pathlib import Path
import sys,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-ratio-monitor/2026-10-27');sys.path.insert(0,str(D));import common as c
s=(D/'fixtures-final.jl').read_text();old='@test iszero(z)&&iszero(q)&&z!==q';new='@test (a==b ? iszero(z)&&iszero(q) : same(z,q))&&z!==q';assert s.count(old)==1
(D/'fixtures-ready.jl').write_text(s.replace(old,new))
(D/'driver-ready.jl').write_text((D/'driver-final.jl').read_text().replace('fixtures-final.jl','fixtures-ready.jl'))
(D/'common_ready.py').write_text((D/'common_final.py').read_text().replace('contract-final.json','contract-ready.json').replace('pins-final.json','pins-ready.json'))
(D/'launch-ready.py').write_text((D/'launch-final.py').read_text().replace('common_final','common_ready').replace('contract-final.json','contract-ready.json').replace('pins-final.json','pins-ready.json').replace('admission-final.json','admission-ready.json'))
co=c.read('contract-final.json');co['command']=[v.replace('driver-final.jl','driver-ready.jl') for v in co['command']];c.put('contract-ready.json',co)
c.put('review-fix3.json',dict(reason='wide unequal normalized operands need not yield zero under directed rounding; exact equality still requires fresh zero, unequal branch checks full value parity and fresh result',candidate_unchanged=True,Julia_executed=False,bindings={str(D/n):c.sha(D/n) for n in ['fixtures-final.jl','fixtures-ready.jl','driver-ready.jl','changes.json','contract-ready.json','common_ready.py','launch-ready.py']}))
shutil.copyfile(__file__,D/'review-fix3.py')
paths=set(c.read('pins-final.json')['inventory']);paths.update(str(p) for p in D.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
c.put('pins-ready.json',dict(files=sorted(paths),trees=c.read('pins.json')['trees'],inputs=[],inventory={n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=c.sha(n)) for n in sorted(paths)}))
import common_ready as cc;cc.unchanged();cc.put('ready-host.json',cc.host());print('READY',len(paths),'pins; noJulia')
