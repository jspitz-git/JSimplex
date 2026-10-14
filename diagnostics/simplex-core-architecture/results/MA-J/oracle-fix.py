from pathlib import Path
import json,hashlib
D=Path.cwd()/'diagnostics/simplex-core-architecture/results/MA-J'
review=json.loads((D/'admission-review.json').read_text())
if review['accepted'] is not False:raise ValueError('expected rejected revision')
for n in ('driver.jl','plan.md','pins.json','admission-review.md','admission-review.json'):
 with (D/(n+'.before-oracle-fix')).open('xb') as f:f.write((D/n).read_bytes())
s=(D/'driver.jl').read_text();marker='function endpoint_oracle'
s=s.replace(marker,'''# Diagnostic conversion must retain stored bits even under a lower ambient context.
qexact(x)=Q(x)
qexact(x::BigFloat)=setprecision(BigFloat,max(precision(x),precision(BigFloat))) do
    Q(x)
end

'''+marker,1)
s=s.replace('Q(c0)','qexact(c0)').replace('Q(c)','qexact(c)').replace('Q(bound_value(', 'qexact(bound_value(').replace('string(Q(x))','string(qexact(x))')
# fixture pivot is exactly +/-2; Q there is deliberately harmless.
old='''                    ok=a==b==want==(offset==0) && same
                    push!(tests,Dict("scalar"=>"stored256ambient$bits","offset"=>offset,"expected"=>want,"reference"=>a,"candidate"=>b,"inputs_preserved"=>same,"pass"=>ok));ok || error("low bits")'''
new='''                    lossy_rejected=true
                    if bits==64 && offset!=0
                        p=lowargs[1]
                        rounded=BigFloat[BigFloat(c;precision=64) for c in p.A.nzval]
                        lossy=LinearProblem(sparse(reshape(rounded,1,3)),zeros(BigFloat,3);row_lower=BigFloat[10],row_upper=BigFloat[10],column_lower=BigFloat[1,1,1],column_upper=BigFloat[1,1,1])
                        lossy_rejected=endpoint_oracle(lossy,[(j,lossy.A[1,j]) for j in 1:3],Q(2),Q(10)) != want
                    end
                    ok=a==b==want==(offset==0) && same && lossy_rejected
                    push!(tests,Dict("scalar"=>"stored256ambient$bits","offset"=>offset,"expected"=>want,"reference"=>a,"candidate"=>b,"inputs_preserved"=>same,"lossy_control_rejected"=>lossy_rejected,"pass"=>ok));ok || error("low bits")'''
if s.count(old)!=1:raise ValueError('expectedlowbit')
s=s.replace(old,new);(D/'driver.jl').write_text(s)
s=(D/'plan.md').read_text()+'''\n## Oracle-context correction (still before the sole numerical attempt)\n\nThe revised admission found direct `Q(stored_BigFloat)` in the diagnostic oracle\nand snapshot could round via Base.ldexp at ambient64. Preserve that review and\nits files/manifest as *.before-oracle-fix. A diagnostic qexact conversion now\nsets precision to max(stored, ambient), restoring the ambient context afterward.\nUse it for every BigFloat oracle/snapshot conversion. Two additional deliberately\nrounded low-bit fixture constructions (oracle only, outside timing) must fail the\nsame expected predicate at offsets -1/+1. Production candidate unchanged.\nThe check grid remains1126 and cost48; negative controls are separately recorded.\n''';(D/'plan.md').write_text(s)
old=json.loads((D/'pins.json.before-oracle-fix').read_text());files={Path(p) for p in old['inventory']}
files.update(p for p in D.iterdir() if p.is_file() and p.name not in ('pins.json','admission-review.md','admission-review.json'))
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
inv={str(p):dict(resolved=str(p.resolve(strict=True)),sha256=sha(p)) for p in sorted(files)}
(D/'pins.json').write_text(json.dumps(dict(files=sorted(inv),trees=[],inventory=inv,inputs=[]),indent=2)+'\n')
(D/'admission-review.md').unlink();(D/'admission-review.json').unlink()
print('final prospective pins',len(inv))
