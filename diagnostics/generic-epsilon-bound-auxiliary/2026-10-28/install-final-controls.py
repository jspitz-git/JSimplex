from pathlib import Path
import shutil,ast
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-epsilon-bound-auxiliary/2026-10-28')
for a,b in [('eba-finalize.py','finalize.py'),('eba-closure.py','closure.py'),('eba-diagnostic-publish.py','diagnostic-publish.py')]:
 p=Path('/tmp')/a;ast.parse(p.read_text(),filename=str(p));shutil.copyfile(p,D/b)
shutil.copyfile(__file__,D/'install-final-controls.py')
print('future offline publication controls prepared; no source/pinned-file edits or execution')
