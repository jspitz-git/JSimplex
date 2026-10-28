from pathlib import Path
import shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-epsilon-bound-auxiliary/2026-10-28');p=D/'fixtures.jl';s=p.read_text()
a=s.index('function metricgraph(');b=s.index('function auxowners(',a)
s=s[:a]+'''scalarleaves(x::BigFloat)=(x,)
scalarleaves(x::Rational{BigInt})=(numerator(x),denominator(x))
scalarleaves(x)=()
function metricgraph(v,x)
 nodes=(v.r.values...,v.r.multipliers...,v.r.primal...,v.r.dual...)
 inputs=Tuple(leaf for node in nodes for leaf in scalarleaves(node))
 outputs=Tuple(leaf for node in x for leaf in scalarleaves(node))
 (Tuple(Tuple(a===b for b in inputs) for a in outputs),Tuple(a===b for a in outputs for b in outputs))
end
'''+s[b:];p.write_text(s);shutil.copyfile(__file__,D/'scalar-alias-review-fix.py')
print('metric graph compares individual BigInt numerator/denominator owner leaves, no Julia')
