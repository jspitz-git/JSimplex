from pathlib import Path
import sys,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-unit-perturb-residual/2026-10-28');sys.path.insert(0,str(D));import common_qualified as c
p=D/'FINAL-REPORT.md';old=p.read_text();needle='Independent numerical and work/memory review found no unnecessary new full scan, solve, conversion, copied vector, repeated invariant check or persistent numeric cache.'
c.need(old.count(needle)==1,'unique reviewed work statement')
replacement='Independent numerical and work/memory review found no unnecessary new full vector/matrix scan, solve, conversion, copied vector or persistent numeric cache. A does retain one avoidable scalar finiteness check on nonunit inputs because its finite-first guard runs before unit testing; the independent predicate-order supplement explicitly accepts this bounded tradeoff. Unit-first ordering is an unmeasured alternative and is not implemented or claimed faster.'
new=old.replace(needle,replacement)
shutil.copyfile(p,D/'FINAL-REPORT.md.before-predicate-clarification');p.write_text(new);shutil.copyfile(__file__,D/'final-prose-fix.py')
c.put('final-prose-fix.json',dict(accepted=True,documentation_only=True,numerics=False,checks=dict(single_statement_replaced=(new==old.replace(needle,replacement) and new.count(replacement)==1),unchanged_continuations=True,source_unchanged=True),bindings={str(D/n):c.sha(D/n) for n in ['FINAL-REPORT.md.before-predicate-clarification','FINAL-REPORT.md','predicate-order-supplement.json','final-prose-fix.py']}))
print('final report predicate-order qualification prepared without production/numerical change')
