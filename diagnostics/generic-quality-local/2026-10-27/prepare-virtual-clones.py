from pathlib import Path
import shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-quality-local/2026-10-27');s=(D/'baseline/src/primal_updates.jl').read_text();i=s.index('function _quality_components!(r::AbstractVector{W},scale,terms,B::_PriceAuditMatrix');j=s.index('\nend',i)+5;virtual='_quality_values(B::_PriceAuditMatrix) = nonzeros(B.matrix)\n'+s[i:j]+'\n\n'
for n in ['Reference','CandidateA','CandidateB','CandidateAB','CandidateC']:
 p=D/(n+'.jl');shutil.copyfile(p,D/(n+'.jl.before-virtual'))
 t=p.read_text().replace('_primal_price_prediction_reliable,recompute!','_primal_price_prediction_reliable,recompute!,_PriceAuditMatrix')
 marker='function _audit_primal_values!(ws::SimplexWorkspace{T})';assert t.count(marker)==1;t=t.replace(marker,virtual+marker);p.write_text(t)
shutil.copyfile(__file__,D/'prepare-virtual-clones.py');print('Added exact implicit price-audit matrix fallback to all private reference namespaces')
