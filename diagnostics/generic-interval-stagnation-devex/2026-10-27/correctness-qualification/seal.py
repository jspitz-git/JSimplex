from pathlib import Path
import sys,json,shutil,subprocess
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-interval-stagnation-devex/2026-10-27');Q=D/'correctness-qualification'
(Q/'common_reviewed.py').write_text((Q/'common.py').read_text().replace("read('pins.json')","read('pins-reviewed.json')"))
(Q/'launch-reviewed.py').write_text((Q/'launch.py').read_text().replace('from common import','from common_reviewed import').replace('pins.json','pins-reviewed.json'))
shutil.copyfile('/tmp/isd-qualification-audit.py',Q/'audit-reviewed.py');shutil.copyfile(__file__,Q/'seal.py')
sys.path.insert(0,str(Q));import common_reviewed as c
paths=set(c.read('pins.json')['files']);paths.add(str(Q/'pins.json'));paths.update(str(Q/n) for n in ['common_reviewed.py','launch-reviewed.py','audit-reviewed.py','seal.py'])
c.put('pins-reviewed.json',dict(files=sorted(paths),trees=c.read('pins.json')['trees'],inputs=[],inventory={n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=c.sha(n)) for n in sorted(paths)}));c.unchanged();c.put('author-host.json',c.host());print('complete qualification sealed',len(paths),'pins; noJulia')
