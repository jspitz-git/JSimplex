"""One-shot offline construction after structural RED."""
from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent;R=H.parents[3];E=H.parent/'MA-E';F=H.parent/'MA-F-repair';G=H.parent/'MA-G'
pins={}
def read(p):
 b=p.read_bytes();pins[str(p.relative_to(R)) if p.is_relative_to(R) else str(p)]=hashlib.sha256(b).hexdigest();return b
read(Path(__file__));red=json.loads(read(H/'red.json'))
if red['all_passed'] or sum(red['checks'].values())!=1:raise RuntimeError('RED')
r=read(E/'overlays/reference/src/markowitz_factorization.jl').decode();e=read(E/'overlays/candidate/src/markowitz_factorization.jl').decode()
a=r.index('    for pivot in sparse_pivots:-1:1',r.index('function _backend_forward_solve!'));b=r.index('    for index in 1:n',a);loop=r[a:b]
call='    _markowitz_upper_solve!(work, backend.upper, backend.diagonal, sparse_pivots)\n'
if e.count(call)!=1:raise RuntimeError('call cardinality')
route='    if (T === BigFloat || T === Rational{BigInt}) && sparse_pivots > 0\n'+'    '+call+'    else\n'+''.join('    '+line for line in loop.splitlines(keepends=True))+'    end\n'
with (H/'candidate-markowitz.jl').open('x') as f:f.write(e.replace(call,route,1))
for src,name in [(E/'overlays/candidate/test/markowitz_ma_upper_tests.jl','candidate-tests.jl'),(E/'overlays/candidate/src/JSimplex.jl','candidate-JSimplex.jl'),(E/'overlays/candidate/Project.toml','candidate-Project.toml'),(E/'fixtures.toml','fixtures.toml'),(F/'driver.jl','qualified-driver-reference.jl'),(F/'kernels.jl','qualified-kernels-reference.jl')]:
 with (H/name).open('xb') as f:f.write(read(src))
start=r.index('function _backend_forward_solve!');end=r.index('function _backend_transpose_solve!',start)
with (H/'reference-forward.jl').open('x') as f:f.write(r[start:end].replace('function _backend_forward_solve!','function reference_forward!',1))
for p in [G/'review.json',G/'review.md',R/'diagnostics/simplex-core-architecture/MA-MARKOWITZ-CONTROL-REGRESSIONS.md',R/'docs/superpowers/plans/2026-10-14-ma-markowitz-routing-preparation.md',E/'test-counts.json',E/'test-instrumentation.json',F/'admission-reviewed.md',E/'admission-reviewed.md',H/'host.json']:
 read(p)
# Pin installed Test/scoped context sources already located in accepted manifest; do not run Julia.
manifest=json.loads((F/'manifest-reviewed.json').read_text()) if (F/'manifest-reviewed.json').exists() else None
# File naming is deliberately not guessed: use reviewed manifest path inventory below.
for p in F.glob('*pins*.json'):
 d=json.loads(p.read_text())
 if isinstance(d,dict):
  for k in d.get('sha256',{}):
   q=Path(k)
   if str(q).endswith(('/Test/src/Test.jl','/base/scopedvalues.jl')) and q.is_file():read(q)
with (H/'inputs.json').open('x') as f:json.dump({'sha256':pins,'scope':'Read-time source bindings, not launch pins. Copied driver/kernels are references only; not executable MA-H controls.'},f,indent=2);f.write('\n')
print(json.dumps({'candidate_sha256':hashlib.sha256((H/'candidate-markowitz.jl').read_bytes()).hexdigest(),'input_bindings':len(pins)}))
