from pathlib import Path
import json,hashlib,sys
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');H=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-HARNESS'
(H/'final-prepare.py').write_bytes(Path(__file__).read_bytes())
p=H/'control.py';s=p.read_text().replace("D/'preparation-pins.json'","D/'preparation-pins-reviewed.json'").replace("D/'required-paths.json'","D/'required-paths-reviewed.json'");p.write_text(s)
p=H/'MEMORY-WORK.md';p.write_text(p.read_text().replace('their five fields','their four fields'))
p=H/'REPORT.md';p.write_text(p.read_text()+'\nAfter-review verification:62 pure mutation controls and32 full-auditor synthetic controls PASS, including unknown events, diagnostic remote mismatch, malformed prefixes and explicit-error timeout refusals. A fixed observational tuple has four fields (ledger wording corrected). No numerical tests executed. Final preparation manifest is preparation-pins-reviewed.json; original133-path manifest remains historical and binds before-review copies where listed in review-fix-bindings.json.\n')
s=(H/'source-check-2.py').read_text().replace("D/'source-check-2.json'","D/'source-check-final.json'")
with (H/'source-check-final.py').open('x') as f:f.write(s)
print('Final source check prepared; canonical reviewed manifest paths selected')
