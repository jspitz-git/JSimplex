from pathlib import Path
import sys,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-unit-perturb-residual/2026-10-28');sys.path.insert(0,str(D));import common as c
s=(D/'fixtures-reviewed.jl').read_text();s=s.replace('if a.scope in (:dual,:primal);@test same(outputstate(a),outputstate(b));','if a.scope in (:dual,:primal);@test x[1]===:value&&(eltype(a.w.primal)<:Rational ? x[2]==0 : x[2]>0);@test same(outputstate(a),outputstate(b));')
(D/'fixtures-final.jl').write_text(s)
s=(D/'driver-reviewed.jl').read_text().replace('fixtures-reviewed.jl','fixtures-final.jl')
s=s.replace('  @test z["compile_seconds"]','  if spec["scope"] in ("dual","primal");@test T<:Rational ? z["result"]==0 : z["result"]>0;end\n  @test z["compile_seconds"]')
(D/'driver-final.jl').write_text(s)
s=(D/'audit-reviewed.py').read_text().replace('from common_reviewed import','from common_final import').replace('contract-reviewed.json','contract-final.json').replace('pins-reviewed.json','pins-final.json').replace('audit-reviewed.py','audit-final.py')
s=s.replace("type(w['result']) is int and w['result']>=0","type(w['result']) is int and (w['result']==0 if spec['context'].startswith('Rational') else w['result']>0)")
(D/'audit-final.py').write_text(s)
(D/'common_final.py').write_text((D/'common_reviewed.py').read_text().replace('contract-reviewed.json','contract-final.json').replace('pins-reviewed.json','pins-final.json'))
(D/'launch-final.py').write_text((D/'launch-reviewed.py').read_text().replace('from common_reviewed import','from common_final import').replace('contract-reviewed.json','contract-final.json').replace('pins-reviewed.json','pins-final.json').replace('admission-reviewed.json','admission-final.json'))
con=c.read('contract-reviewed.json');con['command'][-2]=str(D/'driver-final.jl');c.put('contract-final.json',con)
shutil.copyfile(__file__,D/'admission-final-prepare.py')
paths=set(c.read('pins-reviewed.json')['inventory']);paths.update(str(p) for p in D.iterdir() if p.is_file() and p.name not in ['pins-final.json'])
c.put('pins-final.json',dict(files=sorted(paths),trees=c.read('pins.json')['trees'],inputs=c.read('pins.json')['inputs'],inventory={n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=c.sha(n)) for n in sorted(paths)}))
print('Final active-shift checks sealed',len(paths),'pins, noJulia')
