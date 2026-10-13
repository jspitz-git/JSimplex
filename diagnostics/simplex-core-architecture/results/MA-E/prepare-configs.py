from pathlib import Path
import sys,json,hashlib
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/simplex-core-architecture/results/MA-E');sys.path.insert(0,str(D));sys.dont_write_bytecode=True
from control import STAGES,OUT
(D/'configs').mkdir()
for s in STAGES:
 root=D/'overlays'/s['side'];c=dict(stage=s['stage'],side=s['side'],root=str(root),output=str(OUT/s['id']),ma_source='/home/jspitz/.julia/packages/MutableArithmetics/SaQfc/src/MutableArithmetics.jl',source_sha256=hashlib.sha256((root/'src/markowitz_factorization.jl').read_bytes()).hexdigest())
 with (D/'configs'/(s['id']+'.toml')).open('x') as f:
  for k,v in c.items():f.write(k+' = '+json.dumps(v)+'\n')
(D/'schedule.json').write_text(json.dumps(STAGES,indent=2)+'\n')
