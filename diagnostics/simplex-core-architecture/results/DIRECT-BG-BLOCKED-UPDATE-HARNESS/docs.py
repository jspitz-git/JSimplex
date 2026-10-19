from pathlib import Path
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');H=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-HARNESS'
for n in ['ADMISSION.md','MEMORY-WORK.md']:
 with (H/n).open('x') as f:f.write((Path('/tmp/bg-harness-text')/n).read_text())
(H/'docs.py').write_bytes(Path(__file__).read_bytes())
