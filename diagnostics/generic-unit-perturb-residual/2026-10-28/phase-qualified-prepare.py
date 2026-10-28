from pathlib import Path
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-unit-perturb-residual/2026-10-28')
for n in ['prepare-phase','stage','commit-integrate-publish']:
 s=(D/(n+'.py')).read_text().replace('import common as c','import common_qualified as c').replace('common_reviewed.py','common_qualified.py').replace('launch-reviewed.py','launch-qualified.py').replace('contract-reviewed.json','contract-qualified.json').replace('pins-reviewed.json','pins-qualified.json').replace('admission-reviewed.json','admission-qualified.json').replace('from common_reviewed import','from common_qualified import')
 compile(s,str(D/(n+'-qualified.py')),'exec');(D/(n+'-qualified.py')).write_text(s)
(D/'phase-qualified-prepare.py').write_bytes(Path(__file__).read_bytes())
print('qualified phase drafts UNEXECUTED')
