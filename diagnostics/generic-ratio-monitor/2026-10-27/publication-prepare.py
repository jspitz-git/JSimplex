from pathlib import Path
import shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-ratio-monitor/2026-10-27');O=D.parents[1]/'generic-interval-stagnation-devex/2026-10-27'
s=(O/'commit-integrate-publish.py').read_text().replace('generic-interval-stagnation-devex','generic-ratio-monitor').replace('import common as c','import common_complete as c').replace('fresh49wholefilesGREEN','fresh50wholefilesGREEN')
a=s.index(" message='Reduce BigFloat");b=s.index(" (D/'commit-message.txt')",a)
s=s[:a]+''' message='Reduce BigFloat ratio and stagnation scalar allocations\\n\\nAvoid constructing a zero for positive primal ratio candidates, and avoid discarded nonnegative negations in progress-step and normalized improvement magnitudes. Preserve all numerical guards, tolerances, arithmetic order, signed-zero handling, scalar ownership, precision/rounding and callback/context checks. Add ordinary whole-function correctness and allocation regressions.\\n'
'''+s[b:]
(D/'commit-integrate-publish.py').write_text(s)
shutil.copyfile(O/'publication_checks.py',D/'publication_checks.py');shutil.copyfile(__file__,D/'publication-prepare.py')
print('publication controls prepared for independentreview; noGitmutation')
