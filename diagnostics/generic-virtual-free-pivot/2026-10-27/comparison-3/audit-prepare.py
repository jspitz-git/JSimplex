from pathlib import Path
import json,hashlib,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-virtual-free-pivot/2026-10-27/comparison-3')
s=(D/'audit-ready.py').read_text().replace('import common_ready as c','import common_ready2 as c').replace("list(map(F,o['residual']))","[F(v.replace('//','/')) for v in o['residual']]").replace("F(o['bound'])","F(o['bound'].replace('//','/'))").replace("'audit-ready.py'","'audit-reviewed.py'").replace('pins-ready.json','pins-ready2.json');(D/'audit-reviewed.py').write_text(s)
for src,dst in [('common_ready.py','common_ready2.py'),('launch-ready.py','launch-ready2.py')]:
 s=(D/src).read_text().replace('pins-ready.json','pins-ready2.json').replace('from common_ready import *','from common_ready2 import *');(D/dst).write_text(s)
(D/'AUDITOR-NOTE.md').write_text('Pre-execution auditor syntax adaptation: Julia rational strings use // while PythonFraction expects /. Accept only the stored exact rational representation by replacing // with / before Fraction parsing; recompute every native residual/bound independently. No numerical or driver change. Originalunexecuted auditor preserved. Canonical audit-reviewed.py/common_ready2.py/launch-ready2.py/pins-ready2.json.\n')
shutil.copyfile(__file__,D/'audit-prepare.py');pins=json.loads((D/'pins-ready.json').read_text());paths=set(pins['inventory']);paths.update(str(D/n) for n in ['pins-ready.json','audit-reviewed.py','common_ready2.py','launch-ready2.py','AUDITOR-NOTE.md','audit-prepare.py'])
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
new=dict(files=sorted(paths),trees=pins['trees'],inputs=[],inventory={n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=sha(n)) for n in sorted(paths)});(D/'pins-ready2.json').write_text(json.dumps(new,indent=2,sort_keys=True)+'\n');print(len(paths),'pins')
