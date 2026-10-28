from pathlib import Path
import sys,json,shutil,ast,hashlib
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-epsilon-bound-auxiliary/2026-10-28');sys.path.insert(0,str(D));import common as old
old.need((D/'admission-rejection.json').exists() and not (D/'reservation.json').exists(),'prelaunch rejection only');old.unchanged()
c=old.read('contract.json');c['correctness_assertions']=7197;c['expected_assertions']=57353
old.put('contract-qualified.json',c)
common=(D/'common.py').read_text().replace('contract.json','contract-qualified.json').replace('pins.json','pins-qualified.json');(D/'common_qualified.py').write_text(common)
a=(D/'audit.py').read_text().replace('from common import','from common_qualified import').replace("read('contract.json')","read('contract-qualified.json')").replace("D/'pins.json'","D/'pins-qualified.json'").replace("'audit.py','contract.json','pins.json'","'audit-qualified.py','contract-qualified.json','pins-qualified.json'")
# Guard's copied output manifest retains canonical output/pins.json.
(D/'audit-qualified.py').write_text(a)
l=(D/'launch.py').read_text().replace('from common import','from common_qualified import').replace("read('admission.json')","read('admission-qualified.json')").replace("read('contract.json')","read('contract-qualified.json')").replace("D/'pins.json'","D/'pins-qualified.json'").replace("D/'admission.json'","D/'admission-qualified.json'")
(D/'launch-qualified.py').write_text(l)
for p in [D/'common_qualified.py',D/'audit-qualified.py',D/'launch-qualified.py']:ast.parse(p.read_text(),filename=str(p))
old.put('count-supplement.json',dict(accepted=True,reason='Source schedule was correct; an author addition mistake added100 to each of17 floating contexts. No Julia or attempt reservation exists. Original sealed contract/audit/preparation reviews/rejection remain unchanged.',per_context=dict(BigFloat=401,Float64=375,Float32=355,Rational=226),correctness=15*401+375+355+2*226,cell_assertions=408*50+750*34+76*56,total=57353,unchanged_driver=old.sha(D/'driver.jl'),unchanged_fixtures=old.sha(D/'fixtures.jl'),unchanged_grid=old.sha(D/'expected-cases.json'),superseded_contract=old.sha(D/'contract.json'),superseded_pins=old.sha(D/'pins.json'),superseded_preparation_review=old.sha(D/'preparation-review.json')))
shutil.copyfile(__file__,D/'count-qualified.py')
paths=set(old.read('pins.json')['inventory']);paths.update(str(p) for p in D.iterdir() if p.is_file())
old.put('pins-qualified.json',dict(files=sorted(paths),trees=old.read('pins.json')['trees'],inputs=old.read('pins.json')['inputs'],inventory={n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=old.sha(n)) for n in sorted(paths)}))
import common_qualified as c;c.unchanged();c.put('qualified-author-host.json',c.host());print(json.dumps(dict(pins=len(paths),expected_assertions=57353,noJulia=True,old_pins_unchanged=True)))
