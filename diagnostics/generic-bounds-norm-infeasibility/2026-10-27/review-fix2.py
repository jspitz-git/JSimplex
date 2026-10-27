from pathlib import Path
import sys,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-bounds-norm-infeasibility/2026-10-27');sys.path.insert(0,str(D));import common as c
s=(D/'extra-tests.jl').read_text();old='    vals=wide ? setprecision(BigFloat,512) do;[s*floatmax(BigFloat) for s in signs];end : [s*floatmax(BigFloat) for s in signs]';new='''    vals = if wide
     setprecision(BigFloat,512) do
      [sign*floatmax(BigFloat) for sign in signs]
     end
    else
     [sign*floatmax(BigFloat) for sign in signs]
    end''';assert s.count(old)==1
(D/'extra-tests-ready.jl').write_text(s.replace(old,new))
(D/'driver-ready.jl').write_text((D/'driver-reviewed.jl').read_text().replace('extra-tests.jl','extra-tests-ready.jl'))
(D/'common_ready.py').write_text((D/'common_reviewed.py').read_text().replace('contract-reviewed.json','contract-ready.json').replace('pins-reviewed.json','pins-ready.json'))
(D/'launch-ready.py').write_text((D/'launch-reviewed.py').read_text().replace('common_reviewed','common_ready').replace('contract-reviewed.json','contract-ready.json').replace('pins-reviewed.json','pins-ready.json').replace('admission-reviewed.json','admission-ready.json'))
co=c.read('contract-reviewed.json');co['command']=[x.replace('driver-reviewed.jl','driver-ready.jl') for x in co['command']];c.put('contract-ready.json',co)
c.put('review-fix2.json',dict(reason='explicit if assignment removes ternary do-block parsing ambiguity without Julia probe or changed semantics',candidates_unchanged=True,grid_unchanged=True,bindings={str(D/n):c.sha(D/n) for n in ['extra-tests.jl','extra-tests-ready.jl','driver-ready.jl','changes.json','contract-ready.json','common_ready.py','launch-ready.py']}))
shutil.copyfile(__file__,D/'review-fix2.py');paths=set(c.read('pins-reviewed.json')['inventory']);paths.update(str(p) for p in D.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
c.put('pins-ready.json',dict(files=sorted(paths),trees=c.read('pins.json')['trees'],inputs=[],inventory={n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=c.sha(n)) for n in sorted(paths)}))
import common_ready as cc;cc.unchanged();cc.put('ready-host.json',cc.host());print('ready',len(paths),'pins; noJulia')
