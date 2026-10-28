from pathlib import Path
import sys,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-sum-rational-growth/2026-10-28');sys.path.insert(0,str(D));import common as c
c.need(c.read('admission.json')['accepted'] is False,'rejected initial preserved');c.unchanged();c.put('reviewed-host.json',c.host())
shutil.copyfile(__file__,D/'seal-reviewed.py');paths=set(c.read('pins.json')['files']);paths.update(str(p) for p in D.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
c.put('pins-reviewed.json',dict(files=sorted(paths),trees=c.read('pins.json')['trees'],inputs=[str(D/'grid.toml')],inventory={n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=c.sha(n)) for n in sorted(paths)}))
for n in ['common_reviewed.py','launch-reviewed.py','audit.py']:compile((D/n).read_text(),str(D/n),'exec')
print('revised manifest sealed',len(paths),'pins; noJulia')
