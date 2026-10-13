"""Explicitly admitted structural RED/GREEN checker; no Julia parsing/execution."""
from pathlib import Path
import json,hashlib,sys
H=Path(__file__).resolve().parent;R=H.parents[3];E=H.parent/'MA-E'
mode=sys.argv[1]
if mode not in ('red','green'):raise ValueError(mode)
r=(E/'overlays/reference/src/markowitz_factorization.jl').read_text();e=(E/'overlays/candidate/src/markowitz_factorization.jl').read_text()
p=E/'overlays/candidate/src/markowitz_factorization.jl' if mode=='red' else H/'candidate-markowitz.jl'
s=p.read_text();call='    _markowitz_upper_solve!(work, backend.upper, backend.diagonal, sparse_pivots)\n'
a=r.index('    for pivot in sparse_pivots:-1:1',r.index('function _backend_forward_solve!'));b=r.index('    for index in 1:n',a);loop=r[a:b]
condition='    if (T === BigFloat || T === Rational{BigInt}) && sparse_pivots > 0\n'
route=condition+'    '+call+'    else\n'+''.join('    '+line for line in loop.splitlines(keepends=True))+'    end\n'
helper='# Private scalar scratch exists only during a single upper substitution.\n'
start=e.index(helper);stop=e.index('function _backend_forward_solve!',start);helpers=e[start:stop]
checks={'exact_restricted_route':s.count(route)==1,'exact_condition_once':s.count(condition)==1,'candidate_inverse':s.count(route)==1 and s.replace(route,call,1)==e,'helpers_byte_identical':helpers in s,'reference_inverse':s.count(route)==1 and s.replace(route,loop,1).replace(helpers,'',1)==r}
paths=[Path(__file__),p,E/'overlays/reference/src/markowitz_factorization.jl',E/'overlays/candidate/src/markowitz_factorization.jl']
o={'mode':mode,'checks':checks,'all_passed':all(checks.values()),'sha256':{str(q.relative_to(R)):hashlib.sha256(q.read_bytes()).hexdigest() for q in paths},'scope':'Python source structure only, not Julia RED/GREEN or runtime behavior.'}
with (H/(mode+'.json')).open('x') as f:json.dump(o,f,indent=2);f.write('\n')
print(json.dumps(o,indent=2))
if not o['all_passed']:raise SystemExit(1)
