from pathlib import Path
import json,hashlib
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-sum-rational-growth/2026-10-28');p=D/'extra-tests-reviewed.jl';s=p.read_text();(D/'extra-tests-reviewed.before-value-check.jl').write_text(s)
s=s.replace('v.w.costs[1]=setprecision(BigFloat,512) do;BigFloat(1//4);end','v.w.costs[1]=BigFloat(v.w.costs[1];precision=512)')
s=s.replace('v.w.lower[1]=Bound(setprecision(BigFloat,512) do;BigFloat(-8);end)','v.w.lower[end]=Bound(BigFloat(bound_value(v.w.lower[end]);precision=512))')
s=s.replace('tol=setprecision(BigFloat,512) do;BigFloat(1//1024);end','tol=BigFloat(old.solve_tolerance;precision=512)')
p.write_text(s);(D/'review-fix-preserve-values.py').write_text(Path(__file__).read_text());(D/'review-fix-preserve-values.json').write_text(json.dumps(dict(Julia_executed=False,change='Recovery-widening probes preserve stored cost/bound/tolerance numerical values; only their precision changes',before=hashlib.sha256((D/'extra-tests-reviewed.before-value-check.jl').read_bytes()).hexdigest(),after=hashlib.sha256(p.read_bytes()).hexdigest()),indent=2)+'\n')
