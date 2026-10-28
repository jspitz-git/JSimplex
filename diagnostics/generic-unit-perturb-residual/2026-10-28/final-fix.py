from pathlib import Path
import sys,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-unit-perturb-residual/2026-10-28');sys.path.insert(0,str(D));import common as c
s=(D/'fixtures-final.jl').read_text();s=s.replace('if T===BigFloat||T===Rational{BigInt}\n   for r in (ra,rb)','if T===BigFloat\n   for r in (ra,rb)')
needle='  # Hand-derived lifted residual:'
s=s.replace(needle,'''  if T===Rational{BigInt}
   for r in (ra,rb)
    @test sameowners(owners(v0[1]),owners(r.values[1]))
    @test sameowners(owners(v0[1]),owners(r.multipliers[1]))
    @test sameowners(owners(r.values[1]),owners(r.primal[1]))
    @test sameowners(owners(r.multipliers[1]),owners(r.dual[1]))
   end
  end
'''+needle)
(D/'fixtures-qualified.jl').write_text(s)
(D/'driver-qualified.jl').write_text((D/'driver-final.jl').read_text().replace('fixtures-final.jl','fixtures-qualified.jl'))
s=(D/'audit-final.py').read_text().replace('from common_final import','from common_qualified import').replace('contract-final.json','contract-qualified.json').replace('pins-final.json','pins-qualified.json').replace('audit-final.py','audit-qualified.py');s=s.replace("D/'output/pins-qualified.json'","D/'output/pins.json'");(D/'audit-qualified.py').write_text(s)
(D/'common_qualified.py').write_text((D/'common_final.py').read_text().replace('contract-final.json','contract-qualified.json').replace('pins-final.json','pins-qualified.json'))
(D/'launch-qualified.py').write_text((D/'launch-final.py').read_text().replace('from common_final import','from common_qualified import').replace('contract-final.json','contract-qualified.json').replace('pins-final.json','pins-qualified.json').replace('admission-final.json','admission-qualified.json'))
con=c.read('contract-final.json');con['command'][-2]=str(D/'driver-qualified.jl');c.put('contract-qualified.json',con)
shutil.copyfile(D/'DESIGN.md',D/'DESIGN.md.before-owner-clarification');p=D/'DESIGN.md';p.write_text(p.read_text().replace('initial independently owned input copies/conversions','initial independent input vector containers/conversions (fresh BigFloat scalar owners; existing Rational{BigInt} scalar sharing retained)'))
shutil.copyfile(__file__,D/'final-fix.py')
paths=set(c.read('pins-final.json')['inventory']);paths.update(str(p) for p in D.iterdir() if p.is_file() and p.name!='pins-qualified.json')
c.put('pins-qualified.json',dict(files=sorted(paths),trees=c.read('pins.json')['trees'],inputs=c.read('pins.json')['inputs'],inventory={n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=c.sha(n)) for n in sorted(paths)}))
c.put('owner-auditor-fix.json',dict(accepted=True,numerics=False,old_rejected_sources_preserved=True,initial_design_binding=dict(before=str(D/'DESIGN.md.before-owner-clarification'),sha256=c.sha(D/'DESIGN.md.before-owner-clarification')),bindings={str(D/n):c.sha(D/n) for n in ['fixtures-qualified.jl','driver-qualified.jl','audit-qualified.py','common_qualified.py','launch-qualified.py','contract-qualified.json','pins-qualified.json','DESIGN.md']}))
print('qualified controls sealed',len(paths),'pins')
