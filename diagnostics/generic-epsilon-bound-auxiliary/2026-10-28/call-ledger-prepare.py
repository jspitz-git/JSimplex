from pathlib import Path
import shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-epsilon-bound-auxiliary/2026-10-28')
p=D/'CALL-BUDGET.md';s=p.read_text();s+='''\nThe prospective correctness schedule contains324 auxiliary invocations: sixteen Float64/BigFloat contexts each18 (12 successful,4 early stops,2 observer throws), plus three other contexts each12 (10 successful,2 early stops). Together with2,280 benchmark calls this is2,604 top-level invocations, prospectively2,502 successes/70 stops/32 throws. These are schedule counts, not observed internal backend-entry counts. Any unexpected error prevents completion and remains a failed attempt.\n''';p.write_text(s);shutil.copyfile(__file__,D/'call-ledger-prepare.py')
