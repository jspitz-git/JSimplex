from pathlib import Path
H=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-HARNESS')
for n in ['synthetic.py','source-check.py']:
 with (H/n).open('x') as f:f.write((Path('/tmp/bg-harness-text')/n).read_text())
p=H/'audit.py';s=p.read_text();assert s.count("p['reason']=='wall_timeout'")==1;p.write_text(s.replace("p['reason']=='wall_timeout'","p['reason']=='wall_time'"))
(H/'checks-setup.py').write_bytes(Path(__file__).read_bytes())
