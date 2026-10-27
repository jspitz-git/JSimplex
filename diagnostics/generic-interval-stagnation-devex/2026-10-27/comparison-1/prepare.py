from pathlib import Path
import sys,json,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-interval-stagnation-devex/2026-10-27');Q=D/'comparison-1';sys.path.insert(0,str(D));import common as c
c.unchanged();Q.mkdir()
for n in ['Reference.jl','A.jl','B.jl','C.jl','common.py','environment.json','protected-before.json','contract.json','launch.py','audit.py']:shutil.copyfile(D/n,Q/n)
for n in ['host-before.json','host-seed.json']:shutil.copyfile(D/'author-host.json',Q/n)
f=(D/'fixtures.jl').read_text();old='weights=copy(w.pricing_weights),pivot=T(3//4))';new='weights=copy(w.pricing_weights),pivot=T(shape===:negative ? -3//4 : 3//4))';c.need(f.count(old)==1,'one wholepivotcorrection');f=f.replace(old,new)+'\n'+Path('/tmp/isd-mixed-extra.jl').read_text();(Q/'fixtures.jl').write_text(f)
s=(D/'driver.jl').read_text().replace('correctness(T);boundary_correctness(T)','correctness(T);boundary_correctness(T);mixed_precision_correctness(T)');(Q/'driver.jl').write_text(s)
s=(Q/'contract.json').read_text().replace(str(D/'driver.jl'),str(Q/'driver.jl')).replace(str(D/'output'),str(Q/'output'));(Q/'contract.json').write_text(s)
shutil.copytree(D/'guard',Q/'guard',ignore=shutil.ignore_patterns('__pycache__'))
(Q/'FIX.md').write_text('Independent prelaunch rejection: add actual stored512 Bworkspace conversion/owner tests and Cscalar+whole weight/pivot tests under all15ambient contexts. Negative-shaped wholeC now genuinely uses negative pivot. Same1813matrix/32634windows/alloriginalexpectations/candidatebodies. NoJulia attempted; originalrootunexecuted/frozen. No tolerance/precision/source tuning.\n')
shutil.copyfile(__file__,Q/'prepare.py')
paths=set(c.read('pins.json')['files']);paths.update(str(p) for p in Q.rglob('*') if p.is_file() and '__pycache__' not in p.parts);paths.add(str(D/'pins.json'))
for n in ['prelaunch-review-rejected.json','PRELAUNCH-REJECTED.md','independent-initial-review-check.json']:
 if (D/n).exists():paths.add(str(D/n))
pins=dict(files=sorted(paths),trees=[str(c.M/'src'),str(c.M/'test'),str(D/'baseline')],inputs=[],inventory={n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=c.sha(n)) for n in sorted(paths)})
with (Q/'pins.json').open('x') as out:json.dump(pins,out,indent=2,sort_keys=True);out.write('\n')
print('corrected separatecomparisonprepared',len(paths),'pins noJulia')
