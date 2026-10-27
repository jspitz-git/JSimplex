from pathlib import Path
import shutil
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');O=R/'diagnostics/generic-residual-magnitudes/2026-10-26';D=R/'diagnostics/generic-quality-devex/2026-10-27'
s=(O/'commit-integrate-publish.py').read_text().replace(str(O),str(D)).replace("branch='refs/heads/codex/generic-residual-magnitudes'","branch='refs/heads/codex/generic-quality-devex'").replace("prefix='residual-magnitudes-index-'","prefix='quality-devex-index-'").replace("'exact four names'","'exact five names'")
start=s.index(" message='Avoid temporary BigFloat constants");end=s.index("\n (D/'commit-message.txt')",start)
s=s[:start]+" message='Reduce BigFloat temporary work in residual, quality and Devex checks\\n\\nUse the qualified conditional magnitude in ordinary dual residual checks. Reuse one private comparison-only underflow limit within ordinary BigFloat matrix/vector quality accumulation. Construct each fresh Devex upper cap only for positive overflow. Preserve numerical safeguards, tolerances, precision and rounding, arithmetic order, input owners, callback boundaries and generic/native fallbacks. Add ordinary whole-function differential and allocation regressions.\\n'"+s[end:]
s=s.replace("precommit_qualification='fresh31wholefilesGREEN'","precommit_qualification='fresh34wholefilesGREEN'")
(D/'commit-integrate-publish.py').write_text(s)
shutil.copyfile(O/'publication_checks.py',D/'publication_checks.py')
shutil.copyfile(__file__,D/'prepare-publication.py')
compile(s,str(D/'commit-integrate-publish.py'),'exec')
print('Publication implementation prepared, not executed; requires all reviews and GREEN, MASTER PASS')
