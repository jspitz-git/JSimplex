from pathlib import Path
import json,shutil,sys,subprocess
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-interval-stagnation-devex/2026-10-27');Q=D/'comparison-2';P=D/'comparison-1';sys.path.insert(0,str(D));import common as c
c.unchanged();Q.mkdir()
for n in ['Reference.jl','A.jl','B.jl','C.jl','common.py','environment.json','protected-before.json','launch.py','audit.py','fixtures.jl','driver.jl']:shutil.copyfile(P/n,Q/n)
h=c.host();h['diagnostic_head']=c.git(['rev-parse','HEAD'],c.R);c.need(h['diagnostic_head']==c.read('host-before.json')['diagnostic_head'],'DI unchanged')
for n in ['host-before.json','host-seed.json']:(Q/n).write_text(json.dumps(h,indent=2,sort_keys=True)+'\n')
co=json.loads((P/'contract.json').read_text());co['command']=[v.replace(str(P),str(Q)) for v in co['command']];(Q/'contract.json').write_text(json.dumps(co,indent=2,sort_keys=True)+'\n');shutil.copytree(P/'guard',Q/'guard',ignore=shutil.ignore_patterns('__pycache__'))
(Q/'FIX.md').write_text((P/'FIX.md').read_text()+'\nSecond offline review: copied host snapshot lacked diagnostic_head expected by common.unchanged. New fresh fullhost includes explicit actualDIref; same sources/tests/1813cells/32634windows/guard. Original Q never launched and frozen; no numerical attempt used.\n')
shutil.copyfile(__file__,Q/'prepare.py')
paths=set(json.loads((P/'pins.json').read_text())['files']);paths.add(str(P/'pins.json'));paths.update(str(p) for p in Q.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
for n in ['prelaunch-review-rejected.json','PRELAUNCH-REJECTED.md']:
 if (D/n).exists():paths.add(str(D/n))
pins=dict(files=sorted(paths),trees=[str(c.M/'src'),str(c.M/'test'),str(D/'baseline')],inputs=[],inventory={n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=c.sha(n)) for n in sorted(paths)})
(Q/'pins.json').write_text(json.dumps(pins,indent=2,sort_keys=True)+'\n')
subprocess.run([sys.executable,'-B','-c',"import common;common.unchanged();print('Q2 source/refs/pins/protected invariant check PASS')"],cwd=Q,check=True)
print('new comparison-2:',len(paths),'pins noJulia')
