from pathlib import Path
import json,hashlib,sys
r=Path.cwd();d=r/'diagnostics/simplex-core-architecture/results/MA-J'
review=json.loads((d/'admission-review.json').read_text())
if review['accepted'] is not False:raise ValueError('expected preserved rejected review')
for name in ('admission-review.json','admission-review.md','pins.json','driver.jl','plan.md','launcher.py'):
 with (d/(name+'.before-review')).open('xb') as f:f.write((d/name).read_bytes())
s=(d/'driver.jl').read_text()
s=s.replace('isfinite(b) && push!(scalars,bound_value(b))','push!(scalars,b.value)')
s=s.replace('[(b.bounded) for b in p.column_lower],[(b.bounded) for b in p.column_upper]','[[b.bounded for b in v] for v in (p.row_lower,p.row_upper,p.column_lower,p.column_upper)]')
s=s.replace('style in ("fixed","units","cancel","zero") ? a : a+Q(3,BigInt(11))','(style in ("fixed","units","cancel","zero") || (style=="prefix" && j<n)) ? a : a+Q(3,BigInt(11))')
marker='''                for n in (2,4,8),style in ("fixed","general","units","cancel")'''
new='''                for n in (4,8),style in ("fixed","general","units","cancel","prefix"),sgn in (-1,1)
                    base=fixture(T,n,style,sgn,"contain");p,terms,_,pivot,rhs=base
                    vertices=Q[0]
                    for (j,c) in terms
                        j==1 && continue
                        vertices=[v+Q(c)*Q(bound_value(b)) for v in vertices for b in (p.column_lower[j],p.column_upper[j])]
                    end
                    points=[(rhs-v)/pivot for v in vertices];xmin,xmax=extrema(points)
                    delta=Q(1,BigInt(1)<<220)
                    for mode in ("exact","lower_outside","upper_outside","lower_exact","upper_exact")
                        lo=Any[bound_value(b) for b in p.column_lower];hi=Any[bound_value(b) for b in p.column_upper]
                        if mode=="exact";lo[1]=T(xmin);hi[1]=T(xmax)
                        elseif mode=="lower_outside";lo[1]=T(xmin+delta);hi[1]=nothing
                        elseif mode=="upper_outside";lo[1]=nothing;hi[1]=T(xmax-delta)
                        elseif mode=="lower_exact";lo[1]=T(xmin);hi[1]=nothing
                        else;lo[1]=nothing;hi[1]=T(xmax)
                        end
                        q=LinearProblem(p.A,p.objective;row_lower=p.row_lower,row_upper=p.row_upper,column_lower=lo,column_upper=hi)
                        args=(q,[(j,q.A[1,j]) for j in 1:n],1,pivot,rhs);before=snapshot(args)
                        want=endpoint_oracle(q,args[2],pivot,rhs)
                        actual=JSimplex._equality_implies_column_bounds(args...);a=reference_bounds(args...);b=candidate_bounds(args...);same=preserved(before,snapshot(args));ok=actual==a==b==want && same
                        push!(tests,Dict("scalar"=>label,"n"=>n,"style"=>style,"sign"=>sgn,"mode"=>"tight_"*mode,"expected"=>want,"actual"=>actual,"reference"=>a,"candidate"=>b,"inputs_preserved"=>same,"pass"=>ok))
                        ok || error("tight boundary")
                    end
                end
'''+marker
if s.count(marker)!=1:raise ValueError('marker')
s=s.replace(marker,new)
start=s.index('        lowargs=setprecision');end=s.index('\n    catch e',start)
s=s[:start]+'''        for offset in (-1,0,1)
            lowargs=setprecision(BigFloat,256) do
                tiny=BigFloat(2)^(-200);p=LinearProblem(sparse(reshape(BigFloat[2,3+tiny,5-tiny+offset*tiny],1,3)),zeros(BigFloat,3);row_lower=BigFloat[10],row_upper=BigFloat[10],column_lower=BigFloat[1,1,1],column_upper=BigFloat[1,1,1])
                (p,[(j,p.A[1,j]) for j in 1:3],1,Q(2),Q(10))
            end
            for bits in (64,512)
                setprecision(BigFloat,bits) do
                    before=snapshot(lowargs);want=endpoint_oracle(lowargs[1],lowargs[2],lowargs[4],lowargs[5]);a=reference_bounds(lowargs...);b=candidate_bounds(lowargs...);same=preserved(before,snapshot(lowargs))
                    ok=a==b==want==(offset==0) && same
                    push!(tests,Dict("scalar"=>"stored256ambient$bits","offset"=>offset,"expected"=>want,"reference"=>a,"candidate"=>b,"inputs_preserved"=>same,"pass"=>ok));ok || error("low bits")
                end
            end
        end'''+s[end:]
s=s.replace('length(tests)==722','length(tests)==1126').replace('MA-J 722 cases','MA-J 1126 cases')
s=s.replace('    println("MA-J', '''    all(w["compile_seconds"]==0 && w["recompile_seconds"]==0 for c in costs for w in c["windows"] if w["phase"]=="measured") || error("measured compilation")
    println("MA-J''')
(d/'driver.jl').write_text(s)
s=(d/'launcher.py').read_text().replace("'--seconds','180','--deadline',str(time.monotonic()+180)","'--seconds','174','--deadline',str(time.monotonic()+174)")
(d/'launcher.py').write_text(s)
s=(d/'plan.md').read_text()+'''\n## Admission amendment (before numerical execution)\n\nInitial review rejected inadequate boundary/low-bit sensitivity, missing binary\npins, measured-compile acceptance and shutdown reserve. Original files/manifest/\nreview preserved as *.before-review; their old path bindings resolve only to\nthose copies. Canonical files below are a new prospective admission, no rerun.\nAdd 400 tight finite-bound cases: four scalar types, 4/8 terms, five patterns\nincluding fixed-prefix then divergent endpoint, two signs, five endpoint-bound\nmodes. Float conversions are checked against their actual stored endpoints; a\nsub-ulp offset may legitimately collapse for Float64. Replace the two cancelling\nlow-bit cases with six offset -1/0/+1 cases at ambient64/512, requiring false/true/\nfalse even though conversion at ambient64 would erase the perturbation. Total\n1126 correctness cases. Check all bound stored scalars, including unbounded zero\npayloads and all row/column bounded flags. Cost remains exactly48 cases.\nMeasured compilation now rejects in both driver (after raw save) and supplemental\npostcheck. Launch uses174s with6s polling/termination reserve inside the180s\nexperiment cap; terminal audit still enforces<=180. Pin bash and actual Python.\nFirst timed batches follow qualification and are not cold measurements.\n'''
(d/'plan.md').write_text(s)
p=d/'postcheck.py';s=p.read_text().replace("len(raw.get('tests',[]))>=722","len(raw.get('tests',[]))==1126");p.write_text(s)
# New immutable manifest, never rerun old freeze.py.
old=json.loads((d/'pins.json.before-review').read_text())
files={Path(p) for p in old['inventory']};files.update((Path('/bin/bash'),Path(sys.executable)))
files.update(p for p in d.iterdir() if p.is_file() and p.name not in ('pins.json','admission-review.md','admission-review.json'))
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
inv={str(p):dict(resolved=str(p.resolve(strict=True)),sha256=sha(p)) for p in sorted(files) if p.name not in ('admission-review.md','admission-review.json','pins.json')}
(d/'pins.json').write_text(json.dumps(dict(files=sorted(inv),trees=[],inventory=inv,inputs=[]),indent=2)+'\n')
# Original rejected reviews preserved; remove live names so next reviewer can write exclusively.
(d/'admission-review.json').unlink();(d/'admission-review.md').unlink()
print('amended prospective admission pins',len(inv))
