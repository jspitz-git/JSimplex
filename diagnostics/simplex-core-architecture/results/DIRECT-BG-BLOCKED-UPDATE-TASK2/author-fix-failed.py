from pathlib import Path
import json,hashlib
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');C=R/'diagnostics/direct-bg-blocked-update/reproduce';Q=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-TASK2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for name in ['factor.jl','factor-fault.jl','lifecycle-tests.jl','numerical-tests.jl','adapter-source-map.json']:
 with (Q/(name+'.before-author-fix')).open('xb') as out:out.write((C/name).read_bytes())
for name in ['factor.jl','factor-fault.jl']:
 p=C/name;s=p.read_text();assert s.count('factor.rs')==2;s=s.replace('factor.rs','factor.positions');p.write_text(s)
p=C/'adapter-source-map.json';m=json.loads(p.read_text());m['qualified_suffix']=m['qualified_suffix'].replace('factor.rs','factor.positions');m['substitutions']['position']='whole identifier position -> r only';p.write_text(json.dumps(m,indent=2)+'\n')
p=C/'numerical-tests.jl';s=p.read_text().replace('if !iszero(J._upper_value(f.upper[f.positions[id]],i))','if i in f.upper[f.positions[id]].indices');p.write_text(s)
p=C/'lifecycle-tests.jl';s=p.read_text();s=s.replace('    J._ensure_bartels_golub_incidence!(f.inner)\n    t=N.Trace();A._bgb_test_eliminate!(f,1;probe=t)','    f.inner.row_columns_ready=false\n    J._ensure_bartels_golub_incidence!(f.inner)\n    t=N.Trace();A._bgb_test_eliminate!(f,1;probe=t)',1)
a='''        oldsaved=N.unpack(saved.inner)
''';b='''        oldsaved=N.unpack(saved.inner)
        newer=Vector(B[:,1]);newer[2]+=1/32
        J.forward_solve!(x,f,newer);J.replace_column!(f,x,1)
        changed=copy(B);changed[:,1]=newer
        J.forward_solve!(x,f,ones(96));J.forward_solve!(v,saved,ones(96))
        @test N.residual(changed,x,ones(96)) && N.residual(B,v,ones(96))
        # A copy of a used, possibly scratch-owning factor is also cache-empty.
        usedcopy=J.copy_basis_factorization(f)
        @test usedcopy.workspace===nothing && usedcopy.inner.updates!==f.inner.updates
'''
assert a in s;s=s.replace(a,b,1);p.write_text(s)
with (Q/'author-fix.json').open('x') as out:json.dump(dict(scope='Pre-review source fixes, no execution',changes=['Qualified original factor.positions, not substring replacement','Incidence oracle uses structural support including explicit zeros','Reset incidence after cold explicit-zero insertion','Exercise active/saved copy divergence and copy after update'],sha256={str(C/n):sha(C/n) for n in ['factor.jl','factor-fault.jl','lifecycle-tests.jl','numerical-tests.jl','adapter-source-map.json']}),out,indent=2)
with (Q/'author-fix.py').open('xb') as out:out.write(Path(__file__).read_bytes())
