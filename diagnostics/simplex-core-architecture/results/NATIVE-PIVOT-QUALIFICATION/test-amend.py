"""Offline observation supplement, no Julia. Preserve original generated text."""
from common import *
for n in ['tests-observed.jl','test-inverse.json']:
 with (Q/(n+'.before-equations')).open('xb') as f:f.write((Q/n).read_bytes())
p=Q/'tests-observed.jl';s=p.read_text();a='        x = solve(f, rhs)\n';b=a+'        Main.NP.equation!(matrix,rhs,x,op===transpose)\n';require(s.count(a)==1,'single helper');p.write_text(s.replace(a,b))
z=rd(Q/'test-inverse.json');z['tests-observed.jl']['edits'].append([a,b,1]);z['tests-observed.jl']['sha256']=sha(p)
(Q/'test-inverse.json').write_text(json.dumps(z,indent=2)+'\n')
