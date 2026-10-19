from pathlib import Path
H=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-HARNESS')
for n in ['closure.py','publication.py']:
 with (H/n).open('x') as f:f.write((Path('/tmp/bg-harness-text')/n).read_text())
(H/'closure-prepare.py').write_bytes(Path(__file__).read_bytes())
