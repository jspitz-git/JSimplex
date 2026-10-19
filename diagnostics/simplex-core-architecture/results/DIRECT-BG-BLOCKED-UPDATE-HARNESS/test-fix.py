from pathlib import Path
H=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-HARNESS')
(H/'source-check-failure.txt').write_text('Initial source-check.py exit1: no_world_age_workaround. Literal search matched driver comment "no eval/invokelatest workaround". No source-check.json produced. Original checker preserved; separate source-check-2 excludes full-line comments only for this literal gate. No Julia.\n')
s=(H/'source-check.py').read_text().replace("not any(t in d for t in ['invokelatest','eval(','include_string','@fastmath'])","not any(t in '\\n'.join(line for line in d.splitlines() if not line.lstrip().startswith('#')) for t in ['invokelatest','eval(','include_string','@fastmath'])").replace("D/'source-check.json'","D/'source-check-2.json'")
with (H/'source-check-2.py').open('x') as f:f.write(s)
with (H/'full-audit-tests.py').open('x') as f:f.write(Path('/tmp/bg-harness-text/full-audit-tests.py').read_text())
(H/'test-fix.py').write_bytes(Path(__file__).read_bytes())
